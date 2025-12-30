from django.urls import path
from . import views
from django.conf import settings 
from django.conf.urls.static import static

urlpatterns = [
    path('', views.inicio, name='inicio'),  # Página principal
    path('categorias/', views.categorias, name='categorias'),  # Listado de categorías
    path('categorias/<int:categoria_id>/', views.productos_categoria, name='productos_categoria'),  # Productos por categoría
    path('carrito/', views.carrito, name='carrito'),  # Carrito de compras
    path('comprar/', views.comprar, name='comprar'),  # Finalizar compra
    path('about/', views.about, name='about'),  # Página "about"
    path('agregar_al_carrito/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('actualizar_carrito/<int:producto_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('eliminar_del_carrito/<int:producto_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('buscar/', views.buscar_productos, name='buscar_productos'),
    path('producto/<int:producto_id>/', views.producto_detalle, name='detalle_producto'),
     # --- agregar noticias administrativamente ---
    path('noticias/eliminar/<int:noticia_id>/', views.admin_noticia_eliminar, name='admin_noticia_eliminar'),
    path('noticias/crear/', views.admin_noticia_crear, name='admin_noticia_crear'),
    path('noticias/editar/<int:noticia_id>/', views.admin_noticia_editar, name='admin_noticia_editar'),

    # --- Login y Logout ---
    path('admin_login/', views.admin_login, name='admin_login'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),

    # El dashboard y otras vistas protegidas:
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),  # ejemplo
    path('admin_pedidos/', views.admin_pedidos, name='admin_pedidos'),
   
    # --- Admin de Productos ---
    path('panel/productos/', views.admin_productos, name='admin_productos'),
    path('panel/productos/crear/', views.admin_producto_crear, name='admin_producto_crear'),
    path('panel/productos/<int:producto_id>/editar/', views.admin_producto_editar, name='admin_producto_editar'),
    path('panel/productos/<int:producto_id>/eliminar/', views.admin_producto_eliminar, name='admin_producto_eliminar'),
    
    # --- Admin de Categorias ---
    path('panel/categorias/', views.admin_categorias, name='admin_categorias'),
    path('panel/categorias/crear/', views.admin_categoria_crear, name='admin_categoria_crear'),
    path('panel/categorias/<int:categoria_id>/editar/', views.admin_categoria_editar, name='admin_categoria_editar'),
    path('panel/categorias/<int:categoria_id>/eliminar/', views.admin_categoria_eliminar, name='admin_categoria_eliminar'),

    # --- Admin de Pedidos ---
    path('panel/pedidos/', views.admin_pedidos, name='admin_pedidos'),
    path('panel/pedidos/<int:pedido_id>/', views.admin_pedido_detalle, name='admin_pedido_detalle'),
    path('panel/pedidos/<int:pedido_id>/editar/', views.admin_pedido_editar, name='admin_pedido_editar'),

    # --- Admin de Pedidos ---
    path('panel/clientes/', views.admin_clientes, name='admin_clientes'),
    path('panel/clientes/<int:cliente_id>/', views.admin_cliente_detalle, name='admin_cliente_detalle'),
    # path('panel/clientes/<int:cliente_id>/eliminar/', views.admin_cliente_eliminar, name='admin_cliente_eliminar'),

   # --- GESTIÓN UNIFICADA DE INICIO (Carrusel + Marcas Top) ---
    path('panel/carrusel/', views.admin_carrusel_gestion, name='admin_carrusel_gestion'),
    # URL para editar Slides
    path('panel/carrusel/slide/<int:slide_id>/', views.admin_carrusel_gestion, name='admin_carrusel_gestion'),
    # URLs de eliminación
    path('panel/carrusel/slide/<int:slide_id>/eliminar/', views.admin_carrusel_eliminar, name='admin_carrusel_eliminar'),
    path('panel/marcas/eliminar/<int:marca_id>/', views.admin_marcas_eliminar, name='admin_marcas_eliminar'),
    # --- URLs PARA   ---
    path('agregar_carrito/<int:producto_id>/', views.agregar_al_carrito, name='agregar_carrito'),
    # --- URLs PARA REDES SOCIALES  ---
    # El interruptor MAESTRO -> Debe llamar a la función global
    path('panel/redes/toggle-global/', views.toggle_redes_global, name='toggle_redes_global'),
    # Los interruptores INDIVIDUALES -> Llama a la función individual con ID
    path('panel/redes/toggle/<int:red_id>/', views.toggle_red_social, name='toggle_red_social'),
    # Editar enlaces
    path('panel/redes/editar/<int:red_id>/', views.admin_red_editar, name='admin_red_editar'),
    path('panel/redes/agregar/', views.admin_red_agregar, name='admin_red_agregar'),
    path('panel/redes/eliminar/<int:red_id>/', views.admin_red_eliminar, name='admin_red_eliminar'),
    #---------  Guardar la informacion de la empresa ------------#
    path('panel/empresa/guardar/', views.admin_empresa_guardar, name='admin_empresa_guardar'),
    
    #--------- Crear usuarios administrativos ------------#
    path('usuarios/crear/', views.crear_usuario_admin, name='crear_usuario_admin'),
    path('usuarios/toggle/<int:user_id>/', views.toggle_usuario_status, name='toggle_usuario_status'),

    # Autocompleta la busqueda de productos
    path('api/autocomplete/', views.autocomplete_productos, name='autocomplete_productos'),



]
