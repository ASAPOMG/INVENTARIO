from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Producto

def create_user_groups(sender, **kwargs):
    content_type = ContentType.objects.get_for_model(Producto)
    
    # Intentar obtener el permiso 'view_producto'
    try:
        ver_permiso = Permission.objects.get(codename='view_producto', content_type=content_type)
    except Permission.DoesNotExist:
        ver_permiso = None
        print("El permiso view_producto no existe aún.")
    
    # Asignar el permiso solo si existe
    if ver_permiso:
        empleado_group, created = Group.objects.get_or_create(name='Empleado')
        empleado_group.permissions.add(ver_permiso)

    # Puedes añadir más lógica aquí si es necesario

# Conectar la señal post_migrate
from django.db.models.signals import post_migrate
from django.apps import AppConfig

class InventoryConfig(AppConfig):
    name = 'inventory'

    def ready(self):
        post_migrate.connect(create_user_groups, sender=self)
