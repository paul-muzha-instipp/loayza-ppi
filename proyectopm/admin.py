from django.contrib import admin
from .models import (
    Cliente, Categoria, Producto, Carrusel_inicio,
    Carrito, ItemCarrito, Pedido, DetallePedido
)

@admin.register(Carrusel_inicio)
class Carrusel_inicioAdmin(admin.ModelAdmin):
    # Campos que se muestran en la lista del panel
    list_display = ('nombre', 'orden', 'get_imagen_preview', 'pagina_inicio')
    list_editable = ('orden', 'pagina_inicio') 
    search_fields = ('nombre',)
    readonly_fields = ('get_imagen_preview',)
    def get_imagen_preview(self, obj):
        if obj.imagen:
            # mark_safe indica a Django que renderice este código HTML directamente
            return mark_safe(f'<img src="{obj.imagen.url}" width="100" />')
        return "No Imagen"
    get_imagen_preview.short_description = 'Previsualización'

# Registro básico de todos los modelos
admin.site.register(Cliente)
admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(Carrito)
admin.site.register(ItemCarrito)
admin.site.register(Pedido)
admin.site.register(DetallePedido)
