from djongo import models

class Direccion(models.Model):
    calle = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=255)

    class Meta:
        abstract = True

class Usuario(models.Model):
    ROL_CHOICES = [('cliente', 'Cliente'), ('admin', 'Admin')]
    
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    rol = models.CharField(max_length=10, choices=ROL_CHOICES)
    activo = models.BooleanField(default=True)
    
    direccion = models.EmbeddedModelField(model_container=Direccion, null=True, blank=True)

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return self.nombre