from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.core.paginator import Paginator
from .forms import ProductoForm, CategoriaForm, NoticiaForm, MarcasForm, CarruselInicioForm, UserForm
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .models import Producto, Cliente, Categoria, Noticias, Pedido, DetallePedido, Carrusel_inicio, Marcas, Redes, ConfiguracionSitio, InformacionEmpresa, User
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
import json
import re
from django.db.models import Count
from urllib.parse import quote # Importante para mostrar el texto del mensaje

def admin_required(user):
    return user.is_authenticated and user.is_staff

def inicio(request):
    productos = Producto.objects.filter(pagina_inicio=True)    
    noticias_activas = Noticias.objects.filter(pagina_inicio=True).order_by('-fecha_publicacion')
    noticias_carrusel = Noticias.objects.filter(pagina_inicio=True).order_by('-fecha_publicacion')
    slides = Carrusel_inicio.objects.filter(pagina_inicio=True).order_by('orden')
    marcas_listado = Marcas.objects.filter(pagina_inicio=True).order_by('orden')
    return render(request, 'inicio.html', 
                  {'productos':productos,
                   'noticias_activas': noticias_activas,
                   'slides': slides,
                   'noticias_carrusel': noticias_carrusel,
                   'marcas_slides': marcas_listado
                   })
def categorias(request):
    categorias = Categoria.objects.all()
    return render(request, 'categorias.html', {'categorias': categorias})

def about(request):
    empresa = InformacionEmpresa.objects.filter(id=1).first()
    return render(request, 'about.html', {'empresa': empresa})
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
        .annotate(total_compras=Sum('pedidos_cliente__total'))
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

# ------------------- Funcion de agregar carrito de compras -------------------------
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

#---------- Configuracion del buscador ---------------#

def buscar_productos(request):
    query = request.GET.get('q')
    productos = []
    if query:
        # Esto busca en nombre, descripción y categoría
        productos = Producto.objects.filter(
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query) | 
            Q(categoria__nombre__icontains=query) 
        ).distinct()
    
    context = {
        'query': query,
        'productos': productos,
        # Importante: categorías_menu para que el dropdown de tu navbar no se vacíe
        'categorias_menu': Categoria.objects.all(), 
    }
    return render(request, 'search_results.html', context)

def producto_detalle(request, producto_id):
    """Muestra la página de detalle de un producto específico"""
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'producto_detalle.html', {'producto': producto})

#--------------Autocompletado del buscador -----------#
def autocomplete_productos(request):
    term = request.GET.get('term', '')
    # Buscamos coincidencias en el nombre, limitando a los mejores 8 resultados
    productos = Producto.objects.filter(nombre__icontains=term)[:8]
    
    # Preparamos los datos que necesita el JavaScript
    data = []
    for p in productos:
        data.append({
            'id': p.id,
            'nombre': p.nombre,
            'precio': str(p.precio)
        })
    return JsonResponse(data, safe=False)

# ------------------- Admin pedidos -------------------------

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required  # Solo accesible para admin logueados
def admin_pedidos(request):
    from .models import Pedido, DetallePedido

    pedidos = Pedido.objects.all().order_by('-fecha')  # Más recientes primero

    # Opcional: podrías paginar si hay muchos pedidos
    return render(request, 'admin_pedidos.html', {'pedidos': pedidos})

# ------------------- ADMIN DE NOTICIAS -------------------------
# CREAR NOTICIA
@login_required
@user_passes_test(admin_required)
def admin_noticia_crear(request):
    """Crea una nueva noticia."""
    if request.method == "POST":
        # Manejar archivos (imagen) con request.FILES
        form = NoticiaForm(request.POST, request.FILES) 
        if form.is_valid():
            form.save()
            messages.success(request, "Noticia creada correctamente.")
            return redirect('admin_carrusel_gestion')

# EDITAR NOTICIA
@login_required
@user_passes_test(admin_required)
def admin_noticia_editar(request, noticia_id):
    """Edita una noticia existente."""
    noticia = get_object_or_404(Noticias, id=noticia_id)
    if request.method == "POST":
        # Pasar 'instance' para actualizar el objeto existente
        # Manejar archivos (imagen) con request.FILES
        form = NoticiaForm(request.POST, request.FILES, instance=noticia) 
        if form.is_valid():
            form.save()
            messages.success(request, "Noticia actualizada correctamente.")
            return redirect('admin_carrusel_gestion')

# ELIMINAR NOTICIA
@login_required
@user_passes_test(admin_required)
@require_POST  # <--- ESTO ES VITAL: Solo permite borrar vía formulario POST
def admin_noticia_eliminar(request, noticia_id):
    noticia = get_object_or_404(Noticias, id=noticia_id)
    if request.method == 'POST':
        try:
            noticia.delete()
            messages.success(request, f'La noticia "{noticia.titulo}" ha sido eliminada exitosamente.')
            # Redirigir a la lista de noticias
            return redirect('admin_carrusel_gestion')
        except Exception as e:
            # Manejo de errores (p.ej., si hay un problema con la DB)
            messages.error(request, f'Error al eliminar la noticia: {e}')
            return redirect('admin_carrusel_gestion')

# ------------------- ADMIN DE MARCAS TOP -------------------------
@login_required
@user_passes_test(admin_required)
def admin_marcas_eliminar(request, marca_id):
    if request.method == 'POST':
        marca = get_object_or_404(Marcas, id=marca_id)
        marca.delete()
        messages.success(request, f"Marca '{marca.nombre}' eliminada correctamente.")
        return redirect('admin_carrusel_gestion')

# ------------------- ADMIN DE REDES SOCIALES -------------------------
def toggle_red_social(request, red_id):
    if request.method == 'POST':
        red = get_object_or_404(Redes, id=red_id)
        red.estado = not red.estado
        red.save()
    return redirect('admin_carrusel_gestion')

@login_required
@user_passes_test(admin_required)
def toggle_redes_global(request):
    if request.method == 'POST':
        # Buscamos la configuración única del sitio (ID=1)
        config, created = ConfiguracionSitio.objects.get_or_create(id=1)
        # Cambiamos el estado booleano
        config.redes_activas = not config.redes_activas
        config.save()
        messages.success(request, f"Visibilidad global: {'Activada' if config.redes_activas else 'Desactivada'}")
    return redirect('admin_carrusel_gestion')

# ------------------- ADMIN DE CARRUSELES -------------------------
@login_required
@user_passes_test(admin_required)
def admin_carrusel_gestion(request, slide_id=None):
    # 1. Carga de instancias para edición (GET)
    slide = get_object_or_404(Carrusel_inicio, id=slide_id) if slide_id else None
    marca_id = request.GET.get('edit_marca')
    marca_instancia = get_object_or_404(Marcas, id=marca_id) if marca_id else None
    noticia_id = request.GET.get('edit_noticia')
    noticia_instancia = get_object_or_404(Noticias, id=noticia_id) if noticia_id else None

    # 2. PROCESAMIENTO DE FORMULARIOS (POST)
    if request.method == 'POST':
        # --- LÓGICA PARA NOTICIAS ---
        if 'btn_guardar_noticia' in request.POST:
            id_post = request.POST.get('noticia_id_hidden')
            instancia_post = get_object_or_404(Noticias, id=id_post) if id_post else None
            form_noticia = NoticiaForm(request.POST, request.FILES, instance=instancia_post)
            if form_noticia.is_valid():
                form_noticia.save()
                messages.success(request, "Noticia guardada con éxito.")
                return redirect('admin_carrusel_gestion')

        # --- LÓGICA PARA SLIDES ---
        elif 'btn_guardar_slide' in request.POST:
            form_slide = CarruselInicioForm(request.POST, request.FILES, instance=slide)
            if form_slide.is_valid():
                form_slide.save()
                messages.success(request, "Slide principal guardado.")
                return redirect('admin_carrusel_gestion')

        # --- LÓGICA PARA MARCAS (CORREGIDA) ---
        elif 'btn_guardar_marca' in request.POST:
            # Usamos marca_instancia (la variable de la línea 757)
            form_marca = MarcasForm(request.POST, request.FILES, instance=marca_instancia)
            if form_marca.is_valid():
                form_marca.save()
                messages.success(request, "Marca actualizada." if marca_instancia else "Marca creada.")
                return redirect('admin_carrusel_gestion')

    # 3. PREPARACIÓN DE FORMULARIOS PARA EL CONTEXTO (GET o errores de validación)
    # Si no es POST, inicializamos los formularios con las instancias correspondientes
    form_noticia = NoticiaForm(instance=noticia_instancia)
    form_slide = CarruselInicioForm(instance=slide)
    form_marca = MarcasForm(instance=marca_instancia)

    # 4. CARGA DE DATOS PARA LAS TABLAS
    noticias_listado = Noticias.objects.all().order_by('-fecha_publicacion')
    slides = Carrusel_inicio.objects.all().order_by('orden')
    marcas_listado = Marcas.objects.all().order_by('orden')
    redes = Redes.objects.all()
    empresa_info = InformacionEmpresa.objects.filter(id=1).first()
    config_global, created = ConfiguracionSitio.objects.get_or_create(id=1)

    context = {
        'form': form_slide,
        'marcas_form': form_marca,
        'noticia_form': form_noticia,
        'noticia_editando': noticia_instancia,
        'slides': slides,
        'marcas_slides': marcas_listado,
        'redes': redes,
        'noticias': noticias_listado,
        'config_global': config_global,
        'empresa': empresa_info,
        'titulo_form': "Editar Slide" if slide else "Añadir Nuevo Slide",
        'titulo_marcas_form': "Editar Marca" if marca_instancia else "Añadir Nueva Marca",
    }
    return render(request, 'admin_inicio_usuario.html', context)

# Funcion de eliminar imagenes del carrusel principal#
@login_required
@user_passes_test(admin_required)
def admin_carrusel_eliminar(request, slide_id):
    slide = get_object_or_404(Carrusel_inicio, id=slide_id)
    if request.method == 'POST':
        slide.delete()
        messages.success(request, f"Slide '{slide.nombre}' eliminado correctamente.")
        return redirect('admin_carrusel_gestion')        

# Funcion de eliminar imagenes del carrusel MARCAS TOP#
@login_required
@user_passes_test(admin_required)
def admin_marcas_eliminar(request, marca_id):
    marca = get_object_or_404(Marcas, id=marca_id)
    if request.method == 'POST':
        marca.delete()
        messages.success(request, f"Marca '{marca.nombre}' eliminada correctamente.")
        return redirect('admin_carrusel_gestion') # Redirigimos a la vista unificada


# ------------------- CRUD REDES SOCIALES  -------------------------
@login_required
@user_passes_test(admin_required)
def admin_red_agregar(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        tipo = request.POST.get('tipo')
        url_input = request.POST.get('url')
        if tipo == 'w':
            # Definimos 'numero' limpiando el input
            numero = re.sub(r'\D', '', url_input) 
            # Preparamos el mensaje
            mensaje = quote("Hola, Deseo más información")
            # Usamos la variable 'numero' que definimos arriba
            url_final = f"https://wa.me/{numero}?text={mensaje}"
        else:
            url_final = url_input
        Redes.objects.create(nombre=nombre, tipo=tipo, url=url_final, estado=True)
        messages.success(request, f"La red '{nombre}' ha sido agregada.")
    return redirect('admin_carrusel_gestion')

@login_required
@user_passes_test(admin_required)
def admin_red_editar(request, red_id):
    red = get_object_or_404(Redes, id=red_id)
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        url_input = request.POST.get('url')
        
        red.nombre = request.POST.get('nombre')
        red.tipo = tipo
        
        if tipo == 'w':
            # Solo generamos el link si el usuario mandó un número (no una URL completa)
            if "wa.me" not in url_input:
                numero = re.sub(r'\D', '', url_input)
                mensaje = quote("Hola, Deseo mas informacion")
                red.url = f"https://wa.me/{numero}?text={mensaje}"
            else:
                red.url = url_input
        else:
            red.url = url_input
            
        red.save()
        messages.success(request, f"{red.nombre} actualizada correctamente.")
    return redirect('admin_carrusel_gestion')

@login_required
@user_passes_test(admin_required)
def admin_red_eliminar(request, red_id):
    red = get_object_or_404(Redes, id=red_id)
    if request.method == 'POST':
        nombre = red.nombre
        red.delete()
        messages.success(request, f"La red '{nombre}' fue eliminada.")
    return redirect('admin_carrusel_gestion')

#------ Edita la informacion de la empresa ------#
@login_required
@user_passes_test(admin_required)
def admin_empresa_guardar(request):
    if request.method == 'POST':
        empresa = InformacionEmpresa.objects.filter(id=1).first()
        if not empresa:
            empresa = InformacionEmpresa(id=1)
        empresa.nombre = request.POST.get('nombre', 'Mi Empresa')
        empresa.telefono = request.POST.get('telefono')
        empresa.correo = request.POST.get('correo')
        empresa.mapa_iframe = request.POST.get('mapa_iframe')
        empresa.direccion = request.POST.get('direccion')
        if request.FILES.get('logo'):
            empresa.logo = request.FILES.get('logo')
        empresa.save()
        messages.success(request, "Información actualizada correctamente.")
    return redirect('admin_carrusel_gestion')

# ------------------- GESTIÓN DE USUARIOS ADMINISTRATIVOS -------------------------# 
@login_required
@user_passes_test(admin_required)
def crear_usuario_admin(request):
    if request.method == 'POST':
        # Pasamos request.POST y request.FILES para procesar la imagen
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_staff = True 
            user.save()
            form.save_m2m()
            messages.success(request, f"El usuario '{user.username}' ha sido creado exitosamente.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = UserForm()
        usuarios = User.objects.filter(is_staff=True).order_by('-date_joined')
    return render(request, 'admin_crear_administrador.html', {
        'form': form,
        'usuarios': usuarios, # Enviamos la lista a la plantilla 
        'titulo': 'Registrar Nuevo Usuario Administrativo'
    })
login_required
@user_passes_test(admin_required)
def toggle_usuario_status(request, user_id):
    # Buscamos al usuario, si no existe lanza error 404
    usuario = get_object_or_404(User, id=user_id)
    # Seguridad: Evitar que el admin se desactive a sí mismo por accidente
    if usuario == request.user:
        messages.error(request, "No puedes desactivar tu propia cuenta.")
    else:
        usuario.is_active = not usuario.is_active # Si es True pasa a False, y viceversa
        usuario.save()
        estado = "activado" if usuario.is_active else "desactivado"
        messages.info(request, f"El usuario {usuario.username} ha sido {estado}.")
    
    return redirect('crear_usuario_admin')