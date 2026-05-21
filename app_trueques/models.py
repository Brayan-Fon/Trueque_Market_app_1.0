from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.utils import timezone


# ======================
# PERFIL DE USUARIO
# ======================
class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cedula = models.CharField(max_length=20, unique=True)
    verificado = models.BooleanField(default=False)
    foto = models.CharField(max_length=500, null=True, blank=True)
    bio = models.TextField(max_length=300, blank=True, default='')
    ciudad = models.CharField(max_length=100, blank=True, default='')
    fecha_registro = models.DateTimeField(default=timezone.now)

    def promedio_calificacion(self):
        resultado = self.calificaciones_recibidas.aggregate(Avg('puntaje'))
        return round(resultado['puntaje__avg'] or 0, 1)

    def total_calificaciones(self):
        return self.calificaciones_recibidas.count()

    def total_trueques(self):
        return Trueque.objects.filter(
            models.Q(solicitante=self.user) | models.Q(propietario=self.user),
            estado='completado'
        ).count()

    def insignias(self):
        lista = []
        if self.verificado:
            lista.append({'icono': '✅', 'nombre': 'Verificado'})
        total = self.total_trueques()
        if total >= 1:
            lista.append({'icono': '🤝', 'nombre': 'Primer trueque'})
        if total >= 5:
            lista.append({'icono': '⭐', 'nombre': 'Truequeador activo'})
        if total >= 10:
            lista.append({'icono': '🏅', 'nombre': 'Vendedor confiable'})
        if self.promedio_calificacion() >= 4.5 and self.total_calificaciones() >= 3:
            lista.append({'icono': '💎', 'nombre': 'Muy valorado'})
        return lista

    def __str__(self):
        return f"{self.user.username} - {self.cedula} - {'✅' if self.verificado else '❌'}"


# ======================
# PRODUCTOS PARA TRUEQUES
# ======================
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


# ======================
# TRUEQUES
# ======================
class Trueque(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trueques_solicitados')
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trueques_recibidos')
    producto_ofrecido = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, related_name='ofrecido_en')
    producto_deseado = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, related_name='deseado_en')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.solicitante.username} ↔ {self.propietario.username} [{self.estado}]"


# ======================
# CALIFICACIONES
# ======================
class Calificacion(models.Model):
    evaluador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones_dadas')
    evaluado = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='calificaciones_recibidas')
    puntaje = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comentario = models.TextField(max_length=500, blank=True, default='')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('evaluador', 'evaluado')  # Solo una calificación por par

    def __str__(self):
        return f"{self.evaluador.username} → {self.evaluado.user.username}: {self.puntaje}⭐"


# ======================
# MENSAJES / CHAT
# ======================
class Mensaje(models.Model):
    emisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_enviados')
    receptor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_recibidos')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='mensajes')
    contenido = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_envio']

    def __str__(self):
        return f'{self.emisor.username} → {self.receptor.username}: {self.contenido[:30]}'