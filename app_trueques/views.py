from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Perfil, Producto, Mensaje


# ======================
# VISTA DE LOGIN
# ======================
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {username} 👋')
            return redirect('inicio')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
            return redirect('login')

    return render(request, 'app_trueques/login.html')


# ======================
# VISTA DE REGISTRO
# ======================
def registro_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        cedula = request.POST['cedula']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('registro')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe')
            return redirect('registro')

        user = User.objects.create_user(username=username, email=email, password=password1)
        Perfil.objects.create(user=user, cedula=cedula)

        messages.success(request, 'Usuario registrado correctamente ✅')
        return redirect('login')

    return render(request, 'app_trueques/registro.html')


# ======================
# VISTA DE INICIO
# ======================
def inicio_view(request):
    return render(request, 'app_trueques/inicio.html')


# ======================
# VISTA DE MARKETPLACE
# ======================
def marketplace_view(request):
    productos = Producto.objects.all().order_by('-fecha_creacion')
    return render(request, 'app_trueques/marketplace.html', {'productos': productos})


# ======================
# VISTA PARA AGREGAR PRODUCTO
# ======================
@login_required
def agregar_producto_view(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        descripcion = request.POST['descripcion']
        imagen = request.FILES.get('imagen')
        latitud = request.POST.get('latitud') or None
        longitud = request.POST.get('longitud') or None

        Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            imagen=imagen,
            propietario=request.user,
            latitud=latitud,
            longitud=longitud,
        )
        messages.success(request, '✅ Producto agregado correctamente')
        return redirect('marketplace')

    return render(request, 'app_trueques/agregar_producto.html')


# ======================
# VISTA DE DETALLE DE PRODUCTO
# ======================
@login_required
def producto_detalle_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'app_trueques/producto_detalle.html', {'producto': producto})


# ======================
# VISTA DE CHAT
# ======================
@login_required
def chat_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    propietario = producto.propietario

    if propietario == request.user:
        ultimo_mensaje = Mensaje.objects.filter(
            producto=producto,
            receptor=request.user
        ).order_by('-fecha_envio').first()

        if ultimo_mensaje:
            otro_usuario = ultimo_mensaje.emisor
        else:
            messages.info(request, '⚠️ No tienes conversaciones activas con este producto.')
            return redirect('mis_chats')
    else:
        otro_usuario = propietario

    mensajes = Mensaje.objects.filter(
        producto=producto,
        emisor__in=[request.user, otro_usuario],
        receptor__in=[request.user, otro_usuario]
    ).order_by('fecha_envio')

    if request.method == 'POST':
        contenido = request.POST.get('mensaje')
        if contenido and contenido.strip():
            Mensaje.objects.create(
                emisor=request.user,
                receptor=otro_usuario,
                producto=producto,
                contenido=contenido
            )
            return redirect('chat', producto_id=producto.id)

    context = {
        'producto': producto,
        'otro_usuario': otro_usuario,
        'mensajes': mensajes,
    }
    return render(request, 'app_trueques/chat.html', context)


# ======================
# VISTA DE MIS CHATS
# ======================
@login_required
def mis_chats_view(request):
    user = request.user

    chats = Mensaje.objects.filter(Q(emisor=user) | Q(receptor=user))

    chat_agrupados = {}
    for msg in chats.order_by('-fecha_envio'):
        key = msg.producto.id
        if key not in chat_agrupados:
            otro_usuario = msg.receptor if msg.emisor == user else msg.emisor
            chat_agrupados[key] = {
                'producto': msg.producto,
                'otro_usuario': otro_usuario,
                'ultimo_mensaje': msg.contenido,
                'fecha': msg.fecha_envio
            }

    context = {'chats': chat_agrupados.values()}
    return render(request, 'app_trueques/mis_chats.html', context)


# ======================
# VISTA DE CERRAR SESIÓN
# ======================
def logout_view(request):
    logout(request)
    messages.success(request, '👋 Has cerrado sesión correctamente.')
    return redirect('login')