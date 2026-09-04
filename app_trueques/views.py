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
import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
# Configuración de Pusher
pusher_client = pusher.Pusher(
    app_id='2143654',
    key='f101b2a33c5689a793de',
    secret='b360e1977e1c2d199eb2',
    cluster='us2',
    ssl=True
)




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

            if password1 != password2:
                messages.error(request, 'Las contraseñas no coinciden')
                return redirect('registro')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'El usuario ya existe')
                return redirect('registro')

            if Perfil.objects.filter(cedula=cedula).exists():
                messages.error(request, 'Ya existe una cuenta con esa cédula')
                return redirect('registro')

            user = User.objects.create_user(username=username, email=email, password=password1)
            Perfil.objects.create(user=user, cedula=cedula, verificado=True)
            messages.success(request, 'Usuario registrado correctamente ✅')
            return redirect('login')

        except Exception as e:
            print("🔴 ERROR REGISTRO:", traceback.format_exc())
            raise

    # GET — mostrar formulario
    return render(request, 'app_trueques/registro.html')


# ======================
# INICIO
# ======================
def inicio_view(request):
    return render(request, 'app_trueques/inicio.html')


# ======================
# MARKETPLACE
# ======================
def marketplace_view(request):
    categoria = request.GET.get('cat')
    productos = Producto.objects.filter(disponible=True)
    if categoria and categoria != 'todos':
        productos = productos.filter(categoria=categoria)
    productos = productos.order_by('-fecha_creacion')
    return render(request, 'app_trueques/marketplace.html', {'productos': productos, 'categoria_actual': categoria or 'todos'})


# ======================
# AGREGAR PRODUCTO
# ======================
@login_required
def agregar_producto_view(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        descripcion = request.POST['descripcion']
        categoria = request.POST.get('categoria', 'otros')
        latitud = request.POST.get('latitud') or None
        longitud = request.POST.get('longitud') or None

        import cloudinary.uploader

        imagen = None

        if request.FILES.get('imagen'):
            resultado = cloudinary.uploader.upload(
                request.FILES['imagen']
            )
            imagen = resultado['secure_url']

        Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            categoria=categoria,
            imagen=imagen,
            propietario=request.user,
            latitud=latitud,
            longitud=longitud,
        )

        messages.success(request, '✅ Producto agregado correctamente')
        return redirect('marketplace')

    return render(request, 'app_trueques/agregar_producto.html')


# ======================
# ANALIZAR IMAGEN IA
# ======================
@login_required
def analizar_imagen_ia(request):
    if request.method == 'POST' and request.FILES.get('imagen'):
        if not os.environ.get("GEMINI_API_KEY"):
            return JsonResponse({'error': 'La clave GEMINI_API_KEY no está configurada. Por favor añádela a tus variables de entorno.'}, status=400)
            
        try:
            from PIL import Image
            
            imagen_file = request.FILES['imagen']
            imagen_pil = Image.open(imagen_file)
            
            model = genai.GenerativeModel('gemini-flash-latest')
            prompt = """Analiza la imagen de este producto para un mercado de trueques.
Genera un JSON con este formato:
{
  "nombre": "Un título corto y atractivo (max 50 chars)",
  "descripcion": "Una descripción que resalte características y termine con 'Valor estimado: $X USD'.",
  "categoria": "Una de estas opciones estrictamente: electronica, ropa, hogar, deportes, vehiculos, otros"
}
"""
            response = model.generate_content([prompt, imagen_pil])
            texto_respuesta = response.text.replace('```json', '').replace('```', '').strip()
            ia_data = json.loads(texto_respuesta)
            
            return JsonResponse({
                'status': 'ok',
                'nombre': ia_data.get('nombre', ''),
                'descripcion': ia_data.get('descripcion', ''),
                'categoria': ia_data.get('categoria', 'otros')
            })
        except Exception as e:
            print("Error analizando imagen:", e)
            error_msg = str(e)
            if '429' in error_msg or 'Quota exceeded' in error_msg:
                return JsonResponse({'error': 'Has alcanzado el límite gratuito de peticiones de la IA. Por favor, espera un minuto e intenta de nuevo.'}, status=429)
            return JsonResponse({'error': 'Error interno al analizar la imagen. Intenta de nuevo más tarde.'}, status=500)
    return JsonResponse({'error': 'Mala petición'}, status=400)


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


import threading

def _analizar_mensaje_background(mensaje_id, contenido, audio_bytes, producto_id, pusher_client_obj):
    from django.db import connection
    try:
        import google.generativeai as genai
        import json
        model = genai.GenerativeModel('gemini-flash-latest')
        prompt = """Analiza el siguiente mensaje de un chat de intercambios (puede ser texto o audio). Determina si el mensaje contiene intentos de estafa, peticiones de tarjetas de crédito, o amenazas explícitas. 
Responde con un JSON estricto en este formato: {"seguro": true/false, "motivo": "razón si no es seguro o vacío"}
"""
        inputs = [prompt]
        if audio_bytes:
            inputs.append({
                "mime_type": "audio/webm",
                "data": audio_bytes
            })
        if contenido:
            inputs.append(f'Mensaje de texto a analizar: "{contenido}"')

        response = model.generate_content(inputs)
        texto_respuesta = response.text.replace('```json', '').replace('```', '').strip()
        ia_data = json.loads(texto_respuesta)
        es_seguro = ia_data.get('seguro', True)
        advertencia_ia = ia_data.get('motivo', '')

        if not es_seguro:
            from app_trueques.models import Mensaje
            mensaje = Mensaje.objects.get(id=mensaje_id)
            mensaje.es_seguro = False
            mensaje.advertencia_ia = advertencia_ia
            mensaje.save()

            pusher_client_obj.trigger(f'chat-{producto_id}', 'alerta-seguridad', {
                'mensaje_id': str(mensaje_id),
                'advertencia_ia': advertencia_ia
            })
    except Exception as e:
        print("Error Guardián IA Background:", e)
    finally:
        connection.close()

@login_required
def enviar_mensaje(request, producto_id):
    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            contenido = data.get('mensaje', '').strip()
            audio_url = None
            audio_bytes = None
        else:
            contenido = request.POST.get('mensaje', '').strip()
            audio_file = request.FILES.get('audio')
            audio_url = None
            audio_bytes = None
            if audio_file:
                audio_bytes = audio_file.read()
                audio_file.seek(0)
                import cloudinary.uploader
                resultado = cloudinary.uploader.upload(audio_file, resource_type='video')
                audio_url = resultado['secure_url']

        if not contenido and not audio_url:
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

        # Crear mensaje por defecto seguro
        mensaje_obj = Mensaje.objects.create(
            emisor=request.user,
            receptor=otro_usuario,
            producto=producto,
            contenido=contenido,
            audio=audio_url,
            es_seguro=True,
            advertencia_ia=""
        )

        # 1. Enviar evento al chat local inmediatamente
        pusher_client.trigger(f'chat-{producto_id}', 'nuevo-mensaje', {
            'id': str(mensaje_obj.id),
            'mensaje': contenido,
            'audio': audio_url,
            'emisor': request.user.username,
            'es_seguro': True,
            'advertencia_ia': ""
        })

        # 2. Enviar evento de notificación global al receptor
        noti_mensaje = "🎵 Mensaje de voz" if audio_url else contenido
        pusher_client.trigger(f'user-{otro_usuario.id}', 'nueva-notificacion', {
            'titulo': f'Nuevo mensaje de {request.user.username}',
            'mensaje': noti_mensaje,
            'url': f'/chat/{producto_id}/'
        })

        # 3. Lanzar hilo de IA en segundo plano (para texto o audio)
        t = threading.Thread(target=_analizar_mensaje_background, args=(mensaje_obj.id, contenido, audio_bytes, producto_id, pusher_client))
        t.start()

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

# ======================
# COMUNIDAD
# ======================
@login_required
def comunidad_view(request):
    # Fetch all profiles except the current user
    perfiles = Perfil.objects.exclude(user=request.user).select_related('user')
    context = {'perfiles': perfiles}
    return render(request, 'app_trueques/comunidad.html', context)

# ======================
# MARCAR COMO VENDIDO / DISPONIBLE
# ======================
@login_required
def toggle_disponible_view(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, propietario=request.user)
    producto.disponible = not producto.disponible
    producto.save()
    
    estado = "disponible" if producto.disponible else "marcado como vendido/intercambiado"
    messages.success(request, f'✅ Producto "{producto.nombre}" {estado}.')
    return redirect('perfil')