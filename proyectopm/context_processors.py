from .models import Categoria

def menu_context(request):
    # Todas las categorías para el menú
    categorias_menu = Categoria.objects.all()
    # Total de productos en el carrito (sumando cantidades)
    carrito = request.session.get('carrito', {})
    carrito_total = sum(carrito.values())
    # Año actual
    from datetime import datetime
    year = datetime.now().year

    return {
        'categorias_menu': categorias_menu,
        'carrito_total': carrito_total,
        'year': year,
    }

# proyectopm/context_processors.py
from .models import Producto

def notificaciones_stock(request):
    productos_bajo = Producto.objects.filter(stock__lte=5)
    return {
        'cant_productos_bajo_stock': productos_bajo.count(),
        'productos_bajo_stock': productos_bajo
    }
