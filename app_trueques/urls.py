from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_view, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('marketplace/', views.marketplace_view, name='marketplace'),
    path('agregar-producto/', views.agregar_producto_view, name='agregar_producto'),

    # Vista de detalle de producto
    path('producto/<int:producto_id>/', views.producto_detalle_view, name='producto_detalle'),

    # Vista del chat
    path('chat/<int:producto_id>/', views.chat_view, name='chat'),

    # Vista de Mis Chats
    path('mis-chats/', views.mis_chats_view, name='mis_chats'),

    path('logout/', views.logout_view, name='logout'),
]
