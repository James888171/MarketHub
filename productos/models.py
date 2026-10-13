from djongo import models

class CategoriaSnapshot(models.Model):
    _id = models.ObjectIdField()
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

class Producto(models.Model):
    nombre = models.CharField(max_length=255)
    precio = models.IntegerField()
    stock = models.IntegerField()
    categoria = models.EmbeddedModelField(model_container=CategoriaSnapshot)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'productos'

    def __str__(self):
        return self.nombre