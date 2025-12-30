from .models import Categoria, InformacionEmpresa, Redes, Producto, ConfiguracionSitio
from datetime import datetime

def menu_context(request):
    empresa = InformacionEmpresa.objects.last()
    # Buscamos la configuración global
    config_sitio = ConfiguracionSitio.objects.last() 
    redes = Redes.objects.filter(estado=True)
    # VALIDACIÓN CORRECTA:
    if config_sitio and not config_sitio.redes_activas:
        redes = Redes.objects.none()
    categorias_menu = Categoria.objects.all()
    carrito = request.session.get('carrito', {})
    carrito_total = sum(carrito.values())
    year = datetime.now().year
    return {
        'categorias_menu': categorias_menu,
        'carrito_total': carrito_total,
        'year': year,
        'config_global': empresa, # Datos de la empresa (logo, tel)
        'config_sitio': config_sitio, # <--- Pásalo al contexto para usarlo en el HTML
        'redes_activas': redes, 
    }
def redes_sociales(request):
    empresa = InformacionEmpresa.objects.last()
    #  Validar el interruptor maestro para el link de WhatsApp
    if empresa and not empresa.redes_activas:
        return {'link_whatsapp_global': "#"}
    whatsapp = Redes.objects.filter(tipo='w', estado=True).first()
    return {
        'link_whatsapp_global': whatsapp.url if whatsapp else "#"
    }
# proyectopm/context_processors.py
from .models import Producto
def notificaciones_stock(request):
    productos_bajo = Producto.objects.filter(stock__lte=5)
    return {
        'cant_productos_bajo_stock': productos_bajo.count(),
        'productos_bajo_stock': productos_bajo
    }
def redes_sociales(request):
    # Obtenemos la red que sea de tipo WhatsApp ('w')
    whatsapp = Redes.objects.filter(tipo='w', estado=True).first()
    return {
        'link_whatsapp_global': whatsapp.url if whatsapp else "#"
    }


