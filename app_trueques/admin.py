from django.contrib import admin
from .models import Perfil, Producto, Mensaje

# ======================
# PERFIL DE USUARIO
# ======================
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'cedula')
    search_fields = ('user__username', 'cedula')
    list_filter = ('user__is_active',)
    ordering = ('user__username',)
    readonly_fields = ('user',)


# ======================
# PRODUCTOS PARA TRUEQUES
# ======================
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'propietario', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion', 'propietario__username')
    list_filter = ('fecha_creacion',)
    readonly_fields = ('fecha_creacion',)
    fieldsets = (
        ('Información del producto', {
            'fields': ('nombre', 'descripcion', 'imagen')
        }),
        ('Propietario', {
            'fields': ('propietario',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion',)
        }),
    )


# ======================
# MENSAJES / CHAT
# ======================
@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('emisor', 'receptor', 'producto', 'fecha_envio')
    search_fields = ('emisor__username', 'receptor__username', 'contenido')
    list_filter = ('fecha_envio',)
    ordering = ('-fecha_envio',)
    readonly_fields = ('fecha_envio',)
    fieldsets = (
        ('Participantes', {
            'fields': ('emisor', 'receptor')
        }),
        ('Contenido', {
            'fields': ('producto', 'contenido')
        }),
        ('Fecha', {
            'fields': ('fecha_envio',)
        }),
    )
