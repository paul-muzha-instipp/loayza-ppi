from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'categoria', 'precio', 'imagen', 'rating', 'stock']
        labels = {
            'nombre': 'Nombre del producto',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'precio': 'Precio',
            'imagen': 'Imagen',
            'rating': 'Calificación',
            'stock': 'Stock'
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

from django import forms
from .models import Categoria

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
