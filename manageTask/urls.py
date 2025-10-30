# from django.contrib import admin
# from django.urls import path
# from proyectopm import views 

from django.contrib import admin
from django.urls import path, include
from proyectopm import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('proyectopm.urls')),  # Apunta las rutas base a tu app

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
