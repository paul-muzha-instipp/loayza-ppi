from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.core.mail import send_mail
from .models import Categoria, Producto
from django.core.paginator import Paginator
from .forms import ProductoForm  # Si vas a usar un ModelForm (puedes crearlo después)
from .forms import CategoriaForm
from .models import Pedido, DetallePedido


from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .models import Pedido, Producto, Cliente, Categoria
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum

import json
from django.db.models import Count

def inicio(request):
    return render(request, 'inicio.html')


def categorias(request):
    categorias = Categoria.objects.all()
    return render(request, 'categorias.html', {'categorias': categorias})


# ---------------------------- LOGGIN Y LOGGOUT  ----------------------------
def admin_login(request):
    # Limpia la cola de mensajes SIEMPRE, incluso si vienes de un redirect con mensajes de admin
    # list(messages.get_messages(request))

    login_error = None  # <- Así, siempre existe la variable
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')  # Cambia este nombre por tu vista dashboard
        else:
            login_error = 'Usuario o contraseña incorrectos, o no tiene permisos de administrador.'

    return render(request, 'admin_login.html', {'login_error': login_error})

def admin_logout(request):
    logout(request)
    list(messages.get_messages(request))  # Esto limpia los mensajes pendientes
    return redirect('admin_login')

# ------------------- DASHBOARD -------------------------
@login_required(login_url='admin_login')
def admin_dashboard(request):
        
    # Fechas para últimos 12 meses
    hoy = timezone.now()
    hace_12m = hoy - timedelta(days=365)
    meses_labels = []
    ventas_mes = []
    pedidos_mes = []
    clientes_mes = []

    # Top N clientes por monto total
    TOP_N = 5
    clientes_top = (
        Cliente.objects
        .annotate(total_compras=Sum('pedido__total'))
        .order_by('-total_compras')[:TOP_N]
    )

    labels_clientes_top = [c.nombre for c in clientes_top]
    data_clientes_top = [float(c.total_compras or 0) for c in clientes_top]

    from dateutil.relativedelta import relativedelta

    # --- 1. Pedidos y ventas por mes ---
    hoy = timezone.now().replace(day=1)  # Asegura primer día del mes actual
    pedidos_mensual = (
        Pedido.objects.filter(fecha__gte=hoy - relativedelta(months=12))
        .annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(
            pedidos=Count('id'),
            ventas=Sum('total')
        ).order_by('mes')
    )

    meses_labels = []
    ventas_mes = []
    pedidos_mes = []
    clientes_mes = []

    hoy = timezone.now().replace(day=1)
    for i in range(13):  # 12 meses atrás + el actual
        mes_iter = hoy - relativedelta(months=12 - i)
        label = mes_iter.strftime('%b %Y')
        meses_labels.append(label)
        p = next((x for x in pedidos_mensual if x['mes'].month == mes_iter.month and x['mes'].year == mes_iter.year), None)
        ventas_mes.append(float(p['ventas']) if p and p['ventas'] else 0)
        pedidos_mes.append(p['pedidos'] if p else 0)
        clientes_mes.append(
            Cliente.objects.filter(
                created_at__year=mes_iter.year,
                created_at__month=mes_iter.month
            ).count()
        )
    
    print(len(ventas_mes))

    # --- 2. Ventas por categoría ---
    ventas_categoria = (
        Pedido.objects.filter(fecha__gte=hace_12m)
        .values('detalles__producto__categoria__nombre')
        .annotate(total_ventas=Sum('detalles__precio_unitario'))
        .order_by('-total_ventas')
    )
    labels_categoria = [v['detalles__producto__categoria__nombre'] or "Sin cat" for v in ventas_categoria]
    data_categoria = [float(v['total_ventas'] or 0) for v in ventas_categoria]

    # --- 3. KPIs básicos ---
    total_ventas = sum(ventas_mes)
    total_pedidos = sum(pedidos_mes)
    total_clientes = Cliente.objects.count()
    productos_bajo_stock = Producto.objects.filter(stock__lte=5)
    total_productos = Producto.objects.aggregate(Sum('stock'))['stock__sum'] or 0

    # --- 4. Predicción simple (regresión lineal) ---
    # Tomamos ventas_mes para predecir los siguientes 3 meses
    import numpy as np
    y = np.array(ventas_mes)
    x = np.arange(1, len(y)+1)
    # Solo si hay al menos 4 meses con ventas:
    if len(x) > 3 and np.sum(y) > 0:
        coef = np.polyfit(x, y, 1)
        f = np.poly1d(coef)
        x_pred = np.arange(len(x)+1, len(x)+4)
        y_pred = f(x_pred)
        y_pred = [float(v) if v > 0 else 0 for v in y_pred]
    else:
        y_pred = [0, 0, 0]

    meses_futuro = []
    ult_fecha = hoy.replace(day=1)
    for i in range(1, 4):
        if ult_fecha.month == 12:
            ult_fecha = ult_fecha.replace(year=ult_fecha.year+1, month=1)
        else:
            ult_fecha = ult_fecha.replace(month=ult_fecha.month+1)
        meses_futuro.append(ult_fecha.strftime('%b %Y'))
    print(len(y_pred))
 
     # Cantidad de pedidos por estado
    estados = [label for code, label in Pedido.ESTADO_CHOICES]
    data_pedidos_estado = []
    labels_pedidos_estado = []
    for code, label in Pedido.ESTADO_CHOICES:
        count = Pedido.objects.filter(estado=code).count()
        data_pedidos_estado.append(count)
        labels_pedidos_estado.append(label)

    # Top 10 productos más vendidos (por cantidad total vendida)
    top_productos = (
        Producto.objects
        .annotate(total_vendido=Sum('detallepedido__cantidad'))
        .order_by('-total_vendido')[:5]
    )

    labels_productos_top = [p.nombre for p in top_productos]
    data_productos_top = [int(p.total_vendido or 0) for p in top_productos]
 
    context = {
        'total_ventas': total_ventas,
        'total_pedidos': total_pedidos,
        'total_clientes': total_clientes,
        'productos_bajo_stock': productos_bajo_stock,  # Cambia: antes era el count, ahora la lista
        'cant_productos_bajo_stock': productos_bajo_stock.count(),  # Si quieres mostrar el número
        'total_productos': total_productos,
        'meses_labels': json.dumps(meses_labels),
        'ventas_mes': json.dumps(ventas_mes),
        'pedidos_mes': json.dumps(pedidos_mes),
        'clientes_mes': json.dumps(clientes_mes),
        'labels_categoria': json.dumps(labels_categoria),
        'data_categoria': json.dumps(data_categoria),
        'meses_futuro': json.dumps(meses_futuro),
        'y_pred': json.dumps(y_pred),
        'labels_clientes_top': json.dumps(labels_clientes_top),
        'data_clientes_top': json.dumps(data_clientes_top),
        'labels_pedidos_estado': json.dumps(labels_pedidos_estado),
        'data_pedidos_estado': json.dumps(data_pedidos_estado),
        'labels_productos_top': json.dumps(labels_productos_top),
        'data_productos_top': json.dumps(data_productos_top),
    }
    return render(request, 'admin_dashboard.html', context)

def admin_required(user):
    return user.is_authenticated and user.is_staff


# ------------------- ADMIN DE PRODUCTOS -------------------------
@login_required
@user_passes_test(admin_required)

def admin_productos(request):
    
    productos_list = Producto.objects.all().order_by('-id')
    paginator = Paginator(productos_list, 10)  # 10 productos por página

    page_number = request.GET.get('page')
    productos = paginator.get_page(page_number)
    return render(request, 'admin_productos.html', {'productos': productos})


@login_required
@user_passes_test(admin_required)
def admin_producto_crear(request):
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_productos')
    else:
        form = ProductoForm()
    return render(request, 'admin_producto_form.html', {'form': form, 'titulo': 'Agregar Producto'})


@login_required
@user_passes_test(admin_required)
def admin_producto_editar(request, producto_id):
    producto = Producto.objects.get(pk=producto_id)
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('admin_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'admin_producto_form.html', {'form': form, 'titulo': 'Editar Producto'})


@login_required
@user_passes_test(admin_required)
def admin_producto_eliminar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        producto.delete()
        return redirect('admin_productos')
    return render(request, 'admin_producto_confirmar_eliminar.html', {'producto': producto})




# ------------------- ADMIN DE PEDIDOS -------------------------

@login_required
@user_passes_test(admin_required)
def admin_pedidos(request):
    pedidos = Pedido.objects.all().order_by('-fecha')
    return render(request, 'admin_pedidos.html', {'pedidos': pedidos})

@login_required
@user_passes_test(admin_required)
def admin_pedido_detalle(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    detalles_queryset = pedido.detalles.select_related('producto').all()

    # Calcula el subtotal por cada detalle y crea una lista de diccionarios
    detalles = []
    for d in detalles_queryset:
        detalles.append({
            'nombre': d.producto.nombre if d.producto else 'Producto eliminado',
            'cantidad': d.cantidad,
            'precio_unitario': d.precio_unitario,
            'subtotal': d.cantidad * d.precio_unitario,
        })

    mensaje = None
    if request.method == "POST":
        nuevo_estado = request.POST.get("estado")
        if nuevo_estado and nuevo_estado != pedido.estado:
            pedido.estado = nuevo_estado
            pedido.save()
            mensaje = "Estado actualizado correctamente."

            # ---- ENVÍO DE CORREO ----
            cliente = pedido.cliente
            if cliente and cliente.email:
                asunto = f"Actualización de tu pedido #{pedido.id}"
                if nuevo_estado == "enviado":
                    contenido = f"¡Hola {cliente.nombre}! Tu pedido ha sido ENVIADO."
                elif nuevo_estado == "entregado":
                    contenido = f"¡Hola {cliente.nombre}! Tu pedido ha sido ENTREGADO."
                elif nuevo_estado == "cancelado":
                    contenido = f"Hola {cliente.nombre}, tu pedido ha sido CANCELADO. Si tienes dudas contáctanos."
                else:
                    contenido = f"Tu pedido cambió de estado a: {nuevo_estado}"

                send_mail(
                    asunto,
                    contenido,
                    "paulmuzha07@gmail.com",  # Cambia esto por un email válido
                    [cliente.email],
                    fail_silently=True,   # No detiene la app si el mail falla
                )


        else:
            mensaje = "No hubo cambios."
    else:
        mensaje = None

    return render(request, "admin_pedido_detalle.html", {
        "pedido": pedido,
        "detalles": detalles,
        "mensaje": mensaje,
        "ESTADOS": Pedido.ESTADO_CHOICES
    })

@login_required
@user_passes_test(admin_required)
def admin_pedido_editar(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(Pedido.ESTADO_CHOICES).keys():
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, 'Estado del pedido actualizado correctamente.')
            return redirect('admin_pedidos')
        else:
            messages.error(request, 'Estado no válido.')
    return render(request, 'admin_pedido_editar.html', {
        'pedido': pedido,
        'opciones_estado': Pedido.ESTADO_CHOICES
    })

# @login_required
# @user_passes_test(admin_required)
# def admin_pedido_eliminar(request, pedido_id):
#     pedido = get_object_or_404(Pedido, id=pedido_id)
#     if request.method == 'POST':
#         pedido.delete()
#         messages.success(request, 'Pedido eliminado correctamente.')
#         return redirect('admin_pedidos')
#     return render(request, 'admin_pedido_eliminar.html', {'pedido': pedido})





# ------------------- Funciones de agregar carrito de compras -------------------------

from .models import Cliente
from django.contrib.auth.decorators import login_required, user_passes_test

@login_required
@user_passes_test(admin_required)
def admin_clientes(request):
    clientes = Cliente.objects.all().order_by('nombre')
    return render(request, 'admin_clientes.html', {'clientes': clientes})

@login_required
@user_passes_test(admin_required)
def admin_cliente_detalle(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    pedidos = cliente.pedido_set.all()  # Asumiendo que la relación es cliente.pedido_set
    return render(request, 'admin_cliente_detalle.html', {
        'cliente': cliente,
        'pedidos': pedidos,
    })

# @login_required
# @user_passes_test(admin_required)
# def admin_cliente_eliminar(request, cliente_id):
#     cliente = get_object_or_404(Cliente, id=cliente_id)
#     if request.method == "POST":
#         cliente.delete()
#         messages.success(request, "Cliente eliminado correctamente.")
#         return redirect('admin_clientes')
#     return render(request, 'admin_cliente_eliminar_confirm.html', {'cliente': cliente})


# ------------------- Funciones de agrgear carrito de compras -------------------------
# LISTAR CATEGORÍAS
def admin_categorias(request):
    categorias = Categoria.objects.all()
    return render(request, 'admin_categorias.html', {'categorias': categorias})

# CREAR NUEVA CATEGORÍA
def admin_categoria_crear(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría agregada correctamente.")
            return redirect('admin_categorias')
    else:
        form = CategoriaForm()
    return render(request, 'admin_categoria_form.html', {'form': form, 'titulo': 'Agregar Categoría'})

# EDITAR CATEGORÍA
def admin_categoria_editar(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect('admin_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'admin_categoria_form.html', {'form': form, 'titulo': 'Editar Categoría'})

# ELIMINAR CATEGORÍA
def admin_categoria_eliminar(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, "Categoría eliminada correctamente.")
        return redirect('admin_categorias')
    return render(request, 'admin_categoria_eliminar.html', {'categoria': categoria})




# ------------------- Funciones PRODUCTO Y CATEGORIAS -------------------------

def categorias(request):
    categorias = Categoria.objects.all()
    return render(request, 'categorias.html', {'categorias': categorias})


def productos_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    productos = Producto.objects.filter(categoria=categoria)
    return render(request, 'productos_categoria.html', {
        'categoria': categoria,
        'productos': productos
    })


# ------------------- Funciones de agrear carrito de compras -------------------------


def carrito(request):
    carrito = request.session.get('carrito', {})
    productos = []
    total = 0

    for producto_id, cantidad in carrito.items():
        producto = Producto.objects.get(id=producto_id)
        subtotal = producto.precio * cantidad
        productos.append({
            'producto': producto,
            'precio_unitario': producto.precio,
            'cantidad': cantidad,
            'subtotal': subtotal,
            'id': producto.id
        })
        total += subtotal

    return render(request, 'carrito.html', {
        'items_carrito': productos,
        'total_carrito': total
    })


from django.contrib import messages

def agregar_al_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    cantidad_actual = carrito.get(str(producto_id), 0)

    # Consulta el producto real
    producto = Producto.objects.get(id=producto_id)

    if cantidad_actual + 1 > producto.stock:
        messages.warning(request, f"No hay suficiente stock de {producto.nombre}. Solo hay {producto.stock} disponibles.")
    else:
        carrito[str(producto_id)] = cantidad_actual + 1
        messages.success(request, f"{producto.nombre} agregado al carrito.")

    request.session['carrito'] = carrito
    return redirect(request.META.get('HTTP_REFERER', 'carrito'))


from django.views.decorators.http import require_POST

from django.contrib import messages

@require_POST
def actualizar_carrito(request, producto_id):
    nueva_cantidad = int(request.POST.get('cantidad', 1))
    carrito = request.session.get('carrito', {})
    producto = Producto.objects.get(id=producto_id)

    if nueva_cantidad > producto.stock:
        messages.warning(request, f"Solo hay {producto.stock} de {producto.nombre}. No se puede actualizar.")
    elif nueva_cantidad > 0:
        carrito[str(producto_id)] = nueva_cantidad
        messages.success(request, f"Cantidad actualizada para {producto.nombre}.")
    else:
        carrito.pop(str(producto_id), None)
        messages.info(request, f"{producto.nombre} eliminado del carrito.")

    request.session['carrito'] = carrito
    return redirect('carrito')


def eliminar_del_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    carrito.pop(str(producto_id), None)
    request.session['carrito'] = carrito
    from django.contrib import messages
    messages.info(request, "Producto eliminado del carrito.")
    return redirect('carrito')



# ------------------- Funciones de Finalizar compra -------------------------

from .models import Cliente, Pedido, DetallePedido, Producto

def comprar(request):
    carrito = request.session.get('carrito', {})
    productos = []
    total = 0

    for producto_id, cantidad in carrito.items():
        producto = Producto.objects.get(id=producto_id)
        subtotal = producto.precio * cantidad
        productos.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})
        total += subtotal

    # Si carrito está vacío, redirige
    if not productos:
        return redirect('carrito')

    mensaje = ''
    cliente_datos = {}

    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')
        email = request.POST.get('email')

        # ...antes de crear cliente y pedido
        #VALIDAR EL STOCK ANTES DE LA COMPRA
        errores_stock = []
        for item in productos:
            if item['cantidad'] > item['producto'].stock:
                errores_stock.append(
                    f"Solo hay {item['producto'].stock} unidades de {item['producto'].nombre} disponibles."
                )

        if errores_stock:
            return render(request, 'comprar.html', {
                'productos': productos,
                'total': total,
                'mensaje': " ".join(errores_stock),
                'cliente_datos': cliente_datos
            })


        # Buscar o crear cliente por cédula
    
        if not cedula:
            mensaje = "Debe ingresar la cédula."
            # Devolver los datos que ya puso el usuario
            cliente_datos = {
                'nombre': nombre,
                'direccion': direccion,
                'telefono': telefono,
                'email': email,
            }
            return render(request, 'comprar.html', {
                'productos': productos,
                'total': total,
                'mensaje': mensaje,
                'cliente_datos': cliente_datos,
            })
        
        cliente, creado = Cliente.objects.get_or_create(cedula=cedula, defaults={
            'nombre': nombre, 'direccion': direccion, 'telefono': telefono, 'email': email 
        })
        if not creado:
            # Si ya existe, actualizar datos
            cliente.nombre = nombre
            cliente.direccion = direccion
            cliente.telefono = telefono
            # al crear/actualizar cliente:
            cliente.email = email
            cliente.save()

        # Crear pedido
        pedido = Pedido.objects.create(cliente=cliente, total=total)

        # Crear detalles del pedido
        for item in productos:
            producto = item['producto']
            cantidad = item['cantidad']
            # Descontar stock
            producto.stock -= cantidad
            producto.save()
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio
            )

        # Vacía el carrito
        request.session['carrito'] = {}
        mensaje = "¡Compra realizada con éxito!"
        return render(request, 'compra_exitosa.html', {'pedido': pedido})

    elif request.method == 'GET' and request.GET.get('cedula'):
        # Autocompletar datos si la cédula existe
        try:
            cliente = Cliente.objects.get(cedula=request.GET.get('cedula'))
            cliente_datos = {
                'cedula': cliente.cedula,
                'nombre': cliente.nombre,
                'direccion': cliente.direccion,
                'telefono': cliente.telefono,
                'email': cliente.email
            }
        except Cliente.DoesNotExist:
            cliente_datos = {'cedula': request.GET.get('cedula')}

    return render(request, 'comprar.html', {
        'productos': productos,
        'total': total,
        'mensaje': mensaje,
        'cliente_datos': cliente_datos
    })



def about(request):
    return render(request, 'about.html')





# ------------------- Admin pedidos -------------------------

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required  # Solo accesible para admin logueados
def admin_pedidos(request):
    from .models import Pedido, DetallePedido

    pedidos = Pedido.objects.all().order_by('-fecha')  # Más recientes primero

    # Opcional: podrías paginar si hay muchos pedidos
    return render(request, 'admin_pedidos.html', {'pedidos': pedidos})
