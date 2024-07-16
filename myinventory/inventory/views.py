from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db import models
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .decorators import group_required

from .models import Producto, Transaccion, Categoria, Proveedor
from .forms import ProductoForm, TransaccionForm, CategoriaForm, ProveedorForm, RegistroForm

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter

def scan_barcode(request):
    return render(request, 'inventory/scan_barcode.html')

def custom_permission_denied_view(request, exception):
    return render(request, 'inventory/403.html', status=403)

@login_required
def lista_usuarios(request):
    usuarios = User.objects.all()
    return render(request, 'inventory/lista_usuarios.html', {'usuarios': usuarios})

@login_required
@group_required('Empleados', 'Gerente')
def listar_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'inventory/listar_proveedores.html', {'proveedores': proveedores})


def gerente_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.groups.filter(name='gerente').exists():
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return _wrapped_view_func

@login_required
@gerente_required
def some_view_for_gerentes(request):
    productos = Producto.objects.all()
    total_valor = sum(producto.cantidad * producto.precio for producto in productos)
    
    context = {
        'message': 'Bienvenido, gerente!',
        'productos': productos,
        'total_valor': total_valor
    }
    return render(request, 'inventory/some_view_for_gerentes.html', context)

@login_required
@group_required('Empleados', 'Gerente')
def index(request):
    query = request.GET.get('q')
    if query:
        productos = Producto.objects.filter(nombre__icontains=query)
    else:
        productos = Producto.objects.all()
    
    paginator = Paginator(productos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_valor = sum(producto.cantidad * producto.precio for producto in productos)
    productos_bajo_stock = Producto.objects.filter(cantidad__lt=models.F('stock_minimo'))
    
    return render(request, 'inventory/index.html', {
        'page_obj': page_obj,
        'total_valor': total_valor,
        'productos_bajo_stock': productos_bajo_stock
    })

@login_required
@group_required('Empleados', 'Gerente')
def historial_transacciones(request):
    query = request.GET.get('q')
    tipo = request.GET.get('tipo')
    
    transacciones = Transaccion.objects.all().order_by('-fecha')
    
    if query:
        transacciones = transacciones.filter(producto__nombre__icontains=query)
    
    if tipo:
        transacciones = transacciones.filter(tipo=tipo)
    
    paginator = Paginator(transacciones, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'inventory/historial_transacciones.html', {'page_obj': page_obj, 'query': query, 'tipo': tipo})

@login_required
@group_required('Empleados', 'Gerente')
def registrar_transaccion(request):
    if request.method == 'POST':
        form = TransaccionForm(request.POST)
        if form.is_valid():
            tipo = form.cleaned_data['tipo']
            cantidad = form.cleaned_data['cantidad']
            codigo_barras = form.cleaned_data['codigo_barras']

            if codigo_barras:
                producto = get_object_or_404(Producto, codigo_barras=codigo_barras)
                transaccion = Transaccion.objects.create(
                    producto=producto, tipo=tipo, cantidad=cantidad
                )
                if 'transaccion_productos' not in request.session:
                    request.session['transaccion_productos'] = []
                request.session['transaccion_productos'].append({
                    'producto_id': producto.id,
                    'cantidad': cantidad,
                    'tipo': tipo
                })
                request.session.modified = True
                return redirect('inventory:registrar_transaccion')
    else:
        form = TransaccionForm()

    if 'transaccion_productos' in request.session:
        productos = [get_object_or_404(Producto, id=item['producto_id']) for item in request.session['transaccion_productos']]
        cantidades = [item['cantidad'] for item in request.session['transaccion_productos']]
    else:
        productos = []
        cantidades = []

    return render(request, 'inventory/registrar_transaccion.html', {'form': form, 'productos': zip(productos, cantidades)})


@login_required
@group_required('Empleados', 'Gerente')
def finalizar_transaccion(request):
    if 'transaccion_productos' in request.session:
        for item in request.session['transaccion_productos']:
            producto = get_object_or_404(Producto, id=item['producto_id'])
            Transaccion.objects.create(producto=producto, cantidad=item['cantidad'], tipo=item['tipo'])
        del request.session['transaccion_productos']
    return redirect('inventory:historial_transacciones')


@login_required
@group_required('Gerente')
def delete_producto(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method == 'POST':
        producto.delete()
        return redirect('inventory:index')
    return render(request, 'inventory/delete_producto.html', {'producto': producto})

@login_required
@group_required('Gerente')
def edit_producto(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('inventory:index')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'inventory/edit_producto.html', {'form': form})

@login_required
@group_required('Empleados', 'Gerente')
def detail(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    return render(request, 'inventory/detail.html', {'producto': producto})

@login_required
@group_required('Gerente')
def add_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:index')
    else:
        form = ProductoForm()
    return render(request, 'inventory/add_producto.html', {'form': form})

@login_required
def generar_reporte(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_inventario.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 100, "Reporte de Inventario")

    productos = Producto.objects.all()

    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, height - 150, "Nombre")
    p.drawString(250, height - 150, "Cantidad")
    p.drawString(350, height - 150, "Precio")
    p.drawString(450, height - 150, "Valor Total")

    y = height - 170
    p.setFont("Helvetica", 12)
    for producto in productos:
        p.drawString(100, y, producto.nombre)
        p.drawString(250, y, str(producto.cantidad))
        p.drawString(350, y, f"${producto.precio}")
        p.drawString(450, y, f"${producto.cantidad * producto.precio}")
        y -= 20

    p.showPage()
    p.save()
    return response

@login_required
def generar_reporte_ventas(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_ventas.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 100, "Reporte de Ventas")

    transacciones = Transaccion.objects.filter(tipo='venta')

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 150, "Fecha")
    p.drawString(200, height - 150, "Producto")
    p.drawString(350, height - 150, "Cantidad")
    p.drawString(450, height - 150, "Total")

    y = height - 170
    p.setFont("Helvetica", 12)
    for transaccion in transacciones:
        p.drawString(50, y, transaccion.fecha.strftime("%Y-%m-%d %H:%M:%S"))
        p.drawString(200, y, transaccion.producto.nombre)
        p.drawRightString(400, y, str(transaccion.cantidad))
        p.drawRightString(500, y, f"${transaccion.cantidad * transaccion.producto.precio}")
        y -= 20

    p.showPage()
    p.save()
    return response

@login_required
def generar_reporte_transacciones(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_transacciones.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 100, "Reporte de Transacciones")

    transacciones = Transaccion.objects.all().order_by('-fecha')

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 150, "Fecha")
    p.drawString(150, height - 150, "Producto")
    p.drawString(350, height - 150, "Tipo")
    p.drawString(450, height - 150, "Cantidad")

    y = height - 170
    p.setFont("Helvetica", 12)
    for transaccion in transacciones:
        p.drawString(50, y, transaccion.fecha.strftime("%Y-%m-%d %H:%M"))
        p.drawString(150, y, transaccion.producto.nombre)
        p.drawString(350, y, transaccion.tipo)
        p.drawString(450, y, str(transaccion.cantidad))
        y -= 20

    p.showPage()
    p.save()
    return response

@login_required
def vista_reporte_ventas(request):
    return render(request, 'inventory/reportes.html')

@login_required
@group_required('Gerente')
def agregar_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:index')
    else:
        form = CategoriaForm()
    return render(request, 'inventory/add_categoria.html', {'form': form})

@login_required
@group_required('Gerente')
def agregar_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:index')
    else:
        form = ProveedorForm()
    return render(request, 'inventory/add_proveedor.html', {'form': form})

@login_required
@group_required('Gerente')
def editar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            return redirect('inventory:listar_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'inventory/editar_proveedor.html', {'form': form})

@login_required
@group_required('Gerente')
def eliminar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    if request.method == 'POST':
        proveedor.delete()
        return redirect('inventory:listar_proveedores')
    return render(request, 'inventory/eliminar_proveedor.html', {'proveedor': proveedor})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('inventory:index')
    else:
        form = AuthenticationForm()
    return render(request, 'inventory/registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('inventory:index')
    else:
        form = RegistroForm()
    return render(request, 'inventory/registration/register.html', {'form': form})