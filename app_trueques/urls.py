from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_view, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),

    # Marketplace y productos
    path('marketplace/', views.marketplace_view, name='marketplace'),
    path('agregar-producto/', views.agregar_producto_view, name='agregar_producto'),
    path('producto/<int:producto_id>/', views.producto_detalle_view, name='producto_detalle'),
    path('producto/<int:producto_id>/eliminar/', views.eliminar_producto_view, name='eliminar_producto'),

    # Chat
    path('chat/<int:producto_id>/', views.chat_view, name='chat'),
    path('chat/<int:producto_id>/enviar/', views.enviar_mensaje, name='enviar_mensaje'),
    path('mis-chats/', views.mis_chats_view, name='mis_chats'),

    # Perfil
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/editar/', views.editar_perfil_view, name='editar_perfil'),
    path('perfil/<str:username>/', views.perfil_publico_view, name='perfil_publico'),

    # Calificaciones
    path('calificar/<str:username>/', views.calificar_view, name='calificar'),

    # Trueques
    path('trueques/', views.trueques_view, name='trueques'),
    path('trueque/<int:trueque_id>/completar/', views.completar_trueque_view, name='completar_trueque'),
    path('trueque/<int:trueque_id>/cancelar/', views.cancelar_trueque_view, name='cancelar_trueque'),
]