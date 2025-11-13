from django.db import models
from django.contrib.auth.models import User

# ======================
# PERFIL DE USUARIO
# ======================
class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cedula = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.user.username} - {self.cedula}"


# ======================
# PRODUCTOS PARA TRUEQUES
# ======================
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='productos/')
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


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
        ordering = ['fecha_envio']  # los mensajes se muestran en orden cronológico

    def __str__(self):
        return f'{self.emisor.username} → {self.receptor.username}: {self.contenido[:30]}'
