from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.conf import settings
import pusher
import json
import requests
import traceback
from .models import Perfil, Producto, Mensaje, Calificacion, Trueque

# Configuración de Pusher
pusher_client = pusher.Pusher(
    app_id='2143654',
    key='f101b2a33c5689a793de',
    secret='b360e1977e1c2d199eb2',
    cluster='us2',
    ssl=True
)


# ======================
# METAMAP
# ======================
def obtener_token_metamap():
    url = 'https://api.getmati.com/oauth'
    response = requests.post(url, data={
        'grant_type': 'client_credentials',
        'client_id': settings.METAMAP_CLIENT_ID,
        'client_secret': settings.METAMAP_CLIENT_SECRET,
    })
    if response.status_code == 200:
        return response.json().get('access_token')
    return None


def crear_verificacion_metamap(token, cedula):
    url = 'https://api.getmati.com/v2/verifications'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'flowId': settings.METAMAP_CLIENT_ID,
        'metadata': {'cedula': cedula}
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        return response.json()
    return None


# ======================
# LOGIN
# ======================
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        cedula   = request.POST.get('cedula', '').strip()

        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, '❌ Usuario o contraseña incorrectos')
            return redirect('login')

        try:
            perfil = Perfil.objects.get(user=user_obj)
            if perfil.cedula != cedula:
                messages.error(request, '❌ La cédula no coincide con la registrada')
                return redirect('login')
        except Perfil.DoesNotExist:
            messages.error(request, '❌ No se encontró el perfil del usuario')
            return redirect('login')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {username} 👋')
            return redirect('inicio')
        else:
            messages.error(request, '❌ Usuario o contraseña incorrectos')
            return redirect('login')

    return render(request, 'app_trueques/login.html')


# ======================
# REGISTRO
# ======================
def registro_view(request):
    if request.method == 'POST':
        try:
            username = request.POST['username']
            email = request.POST['email']
            cedula = request.POST['cedula']
            password1 = request.POST['password1']
            password2 = request.POST['password2']
            metamap_verificado = request.POST.get('metamap_verificado', 'false')

            if password1 != password2:
                messages.error(request, 'Las contraseñas no coinciden')
                return redirect('registro')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'El usuario ya existe')
                return redirect('registro')

            if Perfil.objects.filter(cedula=cedula).exists():
                messages.error(request, 'Ya existe una cuenta con esa cédula')
                return redirect('registro')

            if metamap_verificado != 'true':
                messages.error(request, '⚠️ Debes verificar tu identidad antes de registrarte')
                return redirect('registro')

            user = User.objects.create_user(username=username, email=email, password=password1)
            Perfil.objects.create(user=user, cedula=cedula, verificado=True)
            messages.success(request, 'Usuario registrado y verificado correctamente ✅')
            return redirect('login')

        except Exception as e:
            print("🔴 ERROR REGISTRO:", traceback.format_exc())
            raise

    # GET — mostrar formulario
    context = {
        'metamap_client_id': settings.METAMAP_CLIENT_ID or '',
    }
    return render(request, 'app_trueques/registro.html', context)


# ======================
# INICIO
# ======================
def inicio_view(request):
    return render(request, 'app_trueques/inicio.html')


# ======================
# MARKETPLACE
# ======================
def marketplace_view(request):
    productos = Producto.objects.filter(disponible=True).order_by('-fecha_creacion')
    return render(request, 'app_trueques/marketplace.html', {'productos': productos})


# ======================
# AGREGAR PRODUCTO
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
# ELIMINAR PRODUCTO
# ======================
@login_required
def eliminar_producto_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, propietario=request.user)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, '🗑️ Producto eliminado correctamente')
    return redirect('perfil')


# ======================
# DETALLE PRODUCTO
# ======================
@login_required
def producto_detalle_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'app_trueques/producto_detalle.html', {'producto': producto})


# ======================
# PERFIL PROPIO
# ======================
@login_required
def perfil_view(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    productos = Producto.objects.filter(propietario=request.user).order_by('-fecha_creacion')
    calificaciones = perfil.calificaciones_recibidas.order_by('-fecha')
    trueques = Trueque.objects.filter(
        Q(solicitante=request.user) | Q(propietario=request.user)
    ).order_by('-fecha')

    context = {
        'perfil': perfil,
        'productos': productos,
        'calificaciones': calificaciones,
        'trueques': trueques,
    }
    return render(request, 'app_trueques/perfil.html', context)


# ======================
# EDITAR PERFIL
# ======================
@login_required
def editar_perfil_view(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        perfil.bio = request.POST.get('bio', '').strip()
        perfil.ciudad = request.POST.get('ciudad', '').strip()

        if 'foto' in request.FILES:
            import cloudinary.uploader
            resultado = cloudinary.uploader.upload(request.FILES['foto'])
            perfil.foto = resultado['secure_url']

        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.save()

        perfil.save()
        messages.success(request, '✅ Perfil actualizado correctamente')
        return redirect('perfil')

    return render(request, 'app_trueques/editar_perfil.html', {'perfil': perfil})


# ======================
# PERFIL PÚBLICO
# ======================
@login_required
def perfil_publico_view(request, username):
    usuario = get_object_or_404(User, username=username)

    if usuario == request.user:
        return redirect('perfil')

    perfil, _ = Perfil.objects.get_or_create(user=usuario)
    productos = Producto.objects.filter(propietario=usuario, disponible=True).order_by('-fecha_creacion')
    calificaciones = perfil.calificaciones_recibidas.order_by('-fecha')

    ya_califico = Calificacion.objects.filter(
        evaluador=request.user,
        evaluado=perfil
    ).exists()

    context = {
        'perfil': perfil,
        'productos': productos,
        'calificaciones': calificaciones,
        'ya_califico': ya_califico,
    }
    return render(request, 'app_trueques/perfil_publico.html', context)


# ======================
# CALIFICAR USUARIO
# ======================
@login_required
def calificar_view(request, username):
    usuario = get_object_or_404(User, username=username)

    if usuario == request.user:
        messages.error(request, '❌ No puedes calificarte a ti mismo')
        return redirect('perfil_publico', username=username)

    perfil = get_object_or_404(Perfil, user=usuario)

    if Calificacion.objects.filter(evaluador=request.user, evaluado=perfil).exists():
        messages.error(request, '⚠️ Ya calificaste a este usuario')
        return redirect('perfil_publico', username=username)

    if request.method == 'POST':
        puntaje = request.POST.get('puntaje')
        comentario = request.POST.get('comentario', '').strip()

        if not puntaje or int(puntaje) not in range(1, 6):
            messages.error(request, '❌ Puntaje inválido')
            return redirect('calificar', username=username)

        Calificacion.objects.create(
            evaluador=request.user,
            evaluado=perfil,
            puntaje=int(puntaje),
            comentario=comentario
        )
        messages.success(request, f'✅ Calificaste a {username} con {puntaje}⭐')
        return redirect('perfil_publico', username=username)

    return render(request, 'app_trueques/calificar.html', {'perfil': perfil})


# ======================
# TRUEQUES
# ======================
@login_required
def trueques_view(request):
    trueques = Trueque.objects.filter(
        Q(solicitante=request.user) | Q(propietario=request.user)
    ).order_by('-fecha')
    return render(request, 'app_trueques/trueques.html', {'trueques': trueques})


@login_required
def completar_trueque_view(request, trueque_id):
    trueque = get_object_or_404(
        Trueque,
        id=trueque_id,
        propietario=request.user,
        estado='pendiente'
    )
    if request.method == 'POST':
        trueque.estado = 'completado'
        trueque.save()
        messages.success(request, '🎉 Trueque marcado como completado')
    return redirect('trueques')


@login_required
def cancelar_trueque_view(request, trueque_id):
    trueque = get_object_or_404(
        Trueque,
        id=trueque_id,
        estado='pendiente'
    )
    if request.user not in [trueque.solicitante, trueque.propietario]:
        messages.error(request, '❌ No tienes permiso para cancelar este trueque')
        return redirect('trueques')

    if request.method == 'POST':
        trueque.estado = 'cancelado'
        trueque.save()
        messages.success(request, '❌ Trueque cancelado')
    return redirect('trueques')


# ======================
# CHAT
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

    context = {
        'producto': producto,
        'otro_usuario': otro_usuario,
        'mensajes': mensajes,
        'pusher_key': 'f101b2a33c5689a793de',
        'pusher_cluster': 'us2',
    }
    return render(request, 'app_trueques/chat.html', context)


@login_required
def enviar_mensaje(request, producto_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        contenido = data.get('mensaje', '').strip()

        if not contenido:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)

        producto = get_object_or_404(Producto, id=producto_id)
        propietario = producto.propietario

        if propietario == request.user:
            ultimo_mensaje = Mensaje.objects.filter(
                producto=producto,
                receptor=request.user
            ).order_by('-fecha_envio').first()
            otro_usuario = ultimo_mensaje.emisor if ultimo_mensaje else None
        else:
            otro_usuario = propietario

        if not otro_usuario:
            return JsonResponse({'error': 'No se encontró receptor'}, status=400)

        Mensaje.objects.create(
            emisor=request.user,
            receptor=otro_usuario,
            producto=producto,
            contenido=contenido
        )

        pusher_client.trigger(f'chat-{producto_id}', 'nuevo-mensaje', {
            'mensaje': contenido,
            'emisor': request.user.username,
        })

        return JsonResponse({'status': 'ok'})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ======================
# MIS CHATS
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
# LOGOUT
# ======================
def logout_view(request):
    logout(request)
    messages.success(request, '👋 Has cerrado sesión correctamente.')
    return redirect('login')