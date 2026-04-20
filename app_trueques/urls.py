from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_view, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('marketplace/', views.marketplace_view, name='marketplace'),
    path('agregar-producto/', views.agregar_producto_view, name='agregar_producto'),
    path('producto/<int:producto_id>/', views.producto_detalle_view, name='producto_detalle'),
    path('chat/<int:producto_id>/', views.chat_view, name='chat'),
    path('chat/<int:producto_id>/enviar/', views.enviar_mensaje, name='enviar_mensaje'),
    path('mis-chats/', views.mis_chats_view, name='mis_chats'),
    path('logout/', views.logout_view, name='logout'),
]