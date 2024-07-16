from django import forms
from .models import Producto, Transaccion, Categoria, Proveedor
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'direccion', 'telefono', 'email']

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'cantidad', 'precio', 'stock_minimo', 'categoria', 'codigo_barras']
    
    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio <= 0:
            raise forms.ValidationError("El precio debe ser un valor positivo.")
        return precio

class TransaccionForm(forms.ModelForm):
    codigo_barras = forms.CharField(max_length=100, required=False, label='Código de Barras')
    class Meta:
        model = Transaccion
        fields = ['tipo', 'cantidad']
        
    def clean_codigo_barras(self):
        codigo_barras = self.cleaned_data.get('codigo_barras')
        if codigo_barras:
            try:
                producto = Producto.objects.get(codigo_barras=codigo_barras)
            except Producto.DoesNotExist:
                raise forms.ValidationError("El producto con este código de barras no existe.")
        return codigo_barras

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']
