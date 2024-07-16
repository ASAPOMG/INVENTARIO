from django.urls import path, include
from . import views
from django.contrib import admin
from django.contrib.auth import views as auth_views

app_name = 'inventory'

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_producto, name='add_producto'),
    path('edit/<int:producto_id>/', views.edit_producto, name='edit_producto'),
    path('delete/<int:producto_id>/', views.delete_producto, name='delete_producto'),
    path('detail/<int:producto_id>/', views.detail, name='detail'),
    path('transaccion/', views.registrar_transaccion, name='registrar_transaccion'),
    path('historial/', views.historial_transacciones, name='historial_transacciones'),
    path('generar_reporte/', views.generar_reporte, name='generar_reporte'),
    path('generar_reporte_transacciones/', views.generar_reporte_transacciones, name='generar_reporte_transacciones'),
    path('generar_reporte_ventas/', views.generar_reporte_ventas, name='generar_reporte_ventas'),
    path('vista_reporte_ventas/', views.vista_reporte_ventas, name='vista_reporte_ventas'),
    path('add_categoria/', views.agregar_categoria, name='add_categoria'),
    path('proveedores/', views.listar_proveedores, name='listar_proveedores'),
    path('add_proveedor/', views.agregar_proveedor, name='add_proveedor'),
    path('editar_proveedor/<int:proveedor_id>/', views.editar_proveedor, name='editar_proveedor'),
    path('eliminar_proveedor/<int:proveedor_id>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('register/', views.register_view, name='register'),
    path('some_view_for_gerentes/', views.some_view_for_gerentes, name='some_view_for_gerentes'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('scan_barcode/', views.scan_barcode, name='scan_barcode'),  # Nueva URL
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='inventory/registration/logged_out.html'), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('finalizar_transaccion/', views.finalizar_transaccion, name='finalizar_transaccion'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]

handler403 = 'inventory.views.custom_permission_denied_view'
