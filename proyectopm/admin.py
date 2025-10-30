from django.contrib import admin
from .models import (
    Cliente, Categoria, Producto,
    Carrito, ItemCarrito, Pedido, DetallePedido
)

# Registro básico de todos los modelos
admin.site.register(Cliente)
admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(Carrito)
admin.site.register(ItemCarrito)
admin.site.register(Pedido)
admin.site.register(DetallePedido)
