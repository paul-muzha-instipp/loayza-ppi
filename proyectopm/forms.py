from django import forms
from django.contrib.auth.models import User,Group
from .models import Producto,Categoria,Noticias,User, Carrusel_inicio, Marcas, Redes


class RedSocialForm(forms.ModelForm):
            class Meta:
                model = Redes
                fields = ['nombre', 'url', 'tipo', 'estado']
                widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'url': forms.URLInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'https://...'}),
            'tipo': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }

class UserForm(forms.ModelForm):

   

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'username', 'password',
            'dni', 'email', 'image', 'is_active'
        )
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Nombres', 'autofocus': True}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Apellidos'}),
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'dni': forms.TextInput(attrs={'placeholder': 'Cédula'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Correo electrónico'}),
            'password': forms.PasswordInput(attrs={'placeholder': 'Contraseña'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class NoticiaForm(forms.ModelForm):
    contenido = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Pega aquí el código HTML de Incrustación completo.'}),
        label='Contenido de la Noticia / Código de Incrustación'
    )
    class Meta:
        model = Noticias
        fields = ['titulo', 'contenido', 'pagina_inicio'] #fecha de publicación fuera para cambiarla

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'categoria', 'precio', 'imagen', 'rating', 'stock', 'pagina_inicio']
        labels = {
            'nombre': 'Nombre del producto',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'precio': 'Precio',
            'imagen': 'Imagen',
            'rating': 'Calificación',
            'stock': 'Stock',
            'pagina_inicio': 'Mostrar en Galería Destacada' 
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio': forms.NumberInput(attrs={'step': '0.01', 'min': 0}),
            'rating': forms.NumberInput(attrs={'step': '0.1', 'min': 1, 'max': 5}),
            'stock': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo si existe la imagen (o sea, en edición)
        if self.instance and self.instance.imagen:
            self.fields['imagen'].widget.attrs.update({'class': 'form-control'})
            self.fields['imagen'].widget.clear_checkbox_label = 'Eliminar imagen actual'
            self.fields['imagen'].widget.initial_text = 'Actualmente'
            self.fields['imagen'].widget.input_text = 'Subir nueva imagen'

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'imagen']
        labels = {
            'nombre': 'Nombre de la categoría',
            'descripcion': 'Descripción',
            'imagen': 'Imagen'
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo si existe la imagen (o sea, en edición)
        if self.instance and self.instance.imagen:
            self.fields['imagen'].widget.attrs.update({'class': 'form-control'})
            self.fields['imagen'].widget.clear_checkbox_label = 'Eliminar imagen actual'
            self.fields['imagen'].widget.initial_text = 'Actualmente'
            self.fields['imagen'].widget.input_text = 'Subir nueva imagen'

class MarcasForm(forms.ModelForm):
    class Meta:
        model = Marcas
        fields = ['nombre', 'descripcion', 'imagen', 'orden', 'pagina_inicio']
        labels = {
            'nombre': 'Nombre de la marca TOP',
            'descripcion': 'Descripción',
            'imagen': 'Logo de la marca',
            'orden': 'Orden de aparición',
            'pagina_inicio': 'Mostrar en inicio'
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
            'orden': forms.NumberInput(attrs={'min': 0}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo si existe la imagen (o sea, en edición)
        if self.instance and self.instance.imagen:
            self.fields['imagen'].widget.attrs.update({'class': 'form-control'})
            self.fields['imagen'].widget.clear_checkbox_label = 'Eliminar imagen actual'
            self.fields['imagen'].widget.initial_text = 'Actualmente'
            self.fields['imagen'].widget.input_text = 'Subir nueva imagen'


class CarruselInicioForm(forms.ModelForm):
    class Meta:
        model = Carrusel_inicio
        fields = ['nombre', 'imagen', 'orden', 'pagina_inicio'] 
        labels = {
            'nombre': 'Título o Nombre del Slide',
            'imagen': 'Imagen del Carrusel',
        }
        widgets = {
            'orden': forms.NumberInput(attrs={'min': 1}),
        }
    
