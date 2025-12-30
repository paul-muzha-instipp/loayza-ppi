from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.contrib.auth.models import AbstractUser
import uuid

# 1. Usuarios
# class Usuario(models.Model):
#     username = models.CharField(max_length=50, unique=True)
#     password_hash = models.CharField(max_length=128)
#     email = models.EmailField(unique=True)
#     ROLE_CHOICES = [
#         ('admin', 'Administrador'),
#         ('cliente', 'Cliente'),
#     ]
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='cliente')

#     def __str__(self):
#         return self.username

#-------- Informacion personal de la empresa -------#
class InformacionEmpresa(models.Model):
    nombre = models.CharField(max_length=100, default="Mi Empresa")
    telefono = models.CharField(max_length=20, blank=True, null=True) 
    correo = models.EmailField(blank=True, null=True)               
    direccion = models.TextField(blank=True, null=True)  
    mapa_iframe = models.TextField(blank=True, null=True, verbose_name="Código de Google Maps (Iframe)", help_text="Pegue aquí el código iframe de Google Maps")          
    logo = models.ImageField(upload_to='empresa/logos/', null=True, blank=True)
    def __str__(self):
        return self.nombre

#-------------Redes sociales de la empresa------------------#
class ConfiguracionSitio(models.Model):
    redes_activas = models.BooleanField(
        default=True, 
        verbose_name="¿Mostrar redes sociales en el inicio?"
    )
    class Meta:
        verbose_name = "Configuración del Sitio"
        verbose_name_plural = "Configuraciones del Sitio"

    def __str__(self):
        return "Configuración Global del Sitio"

class User(AbstractUser):
    dni = models.CharField(max_length=13, unique=True, verbose_name='Cédula o RUC')   
    image = models.ImageField(upload_to='users/%Y/%m/%d', verbose_name='Imagen', null=True, blank=True)
    is_change_password = models.BooleanField(default=False)
    token = models.UUIDField(primary_key=False, editable=False, null=True, blank=True, default=uuid.uuid4, unique=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups', 
        blank=True,
        help_text=('The groups this user belongs to.'),
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions', 
        blank=True,
        help_text=('Specific permissions for this user.'),
    )

# 2. Clientes
class Cliente(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='perfil_cliente')
    cedula = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)   # <---- AGREGADO
    # ...otros campos...
    def __str__(self):
        return f"{self.nombre} ({self.cedula})"

# 3. Categorías
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)  # <-- cambio aquí
    pagina_inicio= models.BooleanField(default=False)
    def __str__(self):
        return self.nombre
    
# 4. Marcas
class Marcas(models.Model):
    nombre= models.CharField(max_length=100)
    descripcion= models.TextField(blank=True)
    imagen = models.ImageField(upload_to='marcas/', blank=True, null=True)  # <-- cambio aquí
    pagina_inicio= models.BooleanField(default=False)
    orden= models.IntegerField(default=0, verbose_name='Orden')
    class Meta:
        ordering = ['orden', 'nombre']
        
    def __str__(self):
        return self.nombre    
# 5. Redes    
class Redes(models.Model):
    ESTADO_CHOICES = [
        ('f', 'facebook'),
        ('t', 'tik tok'),
        ('i', 'instagram'),
        ('y', 'youtube'),
        ('w', ' WhatsApp')
    ]
    nombre = models.CharField(max_length=100)
    url = models.TextField(blank=True)
    tipo = models.CharField(max_length=2, choices=ESTADO_CHOICES)
    estado = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre 
    
# 6. Noticias   
class Noticias(models.Model): # Si prefieres Noticia en singular, re-nombra la clase
    titulo = models.CharField(max_length=200) # Renombrado para mayor claridad
    contenido = models.TextField(blank=True, verbose_name="Código de Incrustación (HTML)")
    pagina_inicio = models.BooleanField(default=False)
    fecha_publicacion = models.DateTimeField(auto_now_add=True) 
    def __str__(self):
        return self.titulo # Retorna el título
    class Meta:
        verbose_name_plural = "Noticias"
        ordering = ['-fecha_publicacion'] # Las más nuevas primero

# 7. Carrusel_principal_inicio   
class Carrusel_inicio(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Name/Titulo del Slide')
    imagen = models.ImageField(upload_to='inicio/', blank=True, null=True)
    pagina_inicio= models.BooleanField(default=True)
    orden = models.IntegerField(default=0, verbose_name='Orden')
    def __str__(self):
        return self.nombre
    class Meta:
        verbose_name = 'Slide de Carrusel'
        verbose_name_plural = 'Slides del Carrusel'
        ordering = ['orden', '-id'] # Ordena por el campo 'orden'
    def __str__(self):
        return self.nombre
    # Función de utilidad para ver el preview en el Admin
    def get_imagen_preview(self):
        if self.imagen:
            return mark_safe(f'<img src="{self.imagen.url}" width="100" />')
        return "No Imagen"
    get_imagen_preview.short_description = 'Previsualización'

# 8. Productos
class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)  # <-- cambio aquí
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)
    stock = models.PositiveIntegerField(default=0)
    pagina_inicio= models.BooleanField(default=False)
    tipo='1'
    def __str__(self):
        return self.nombre

# 9. Carritos
class Carrito(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=64, blank=True)  # Puede estar vacío si es usuario autenticado
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('comprado', 'Comprado'),
        ('abandonado', 'Abandonado'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')

    def __str__(self):
        if self.cliente:
            return f"Carrito de {self.cliente.nombre} ({self.estado})"
        return f"Carrito sesión {self.session_id[:8]}... ({self.estado})"

# 10. Items_Carrito
class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

# 11. Pedidos
class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, related_name='pedidos_cliente')
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('anulado', 'Anulado'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.nombre if self.cliente else 'Sin cliente'}"

# 12. Detalles_Pedido
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre if self.producto else 'Producto eliminado'}"


