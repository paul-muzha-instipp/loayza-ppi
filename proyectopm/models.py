from django.db import models
from django.contrib.auth.models import User


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

# 2. Clientes
class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
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

    def __str__(self):
        return self.nombre


# 4. Productos
class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)  # <-- cambio aquí
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nombre

# 5. Carritos
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

# 6. Items_Carrito
class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

# 7. Pedidos
class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
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

# 8. Detalles_Pedido
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre if self.producto else 'Producto eliminado'}"

