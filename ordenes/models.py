from djongo import models

class UsuarioSnapshot(models.Model):
    usuario_id = models.IntegerField()
    email = models.EmailField()
    nombre = models.CharField(max_length=255)

    class Meta:
        abstract = True

class ProductoSnapshot(models.Model):
    producto_id = models.IntegerField()
    nombre = models.CharField(max_length=255)
    precio = models.IntegerField()

    class Meta:
        abstract = True 

class ItemCarrito(models.Model):
    producto = models.EmbeddedField(model_container=ProductoSnapshot)
    cantidad = models.IntegerField()

    class Meta:
        abstract = True

class CarritoCompras(models.Model):
    usuario = models.EmbeddedField(model_container=UsuarioSnapshot)
    items = models.ArrayField(model_container=ItemCarrito)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carritocompras'

class ItemOrden(models.Model):
    producto = models.EmbeddedField(model_container=ProductoSnapshot)
    precio_unitario = models.IntegerField()
    cantidad = models.IntegerField()

    class Meta:
        abstract = True

class DireccionEnvio(models.Model):
    calle = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=255)

    class Meta:
        abstract = True

class Orden(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'), 
        ('pagado', 'Pagado'), 
        ('enviado', 'Enviado'), 
        ('entregado', 'Entregado'), 
        ('cancelado', 'Cancelado')
    ]
    
    usuario = models.EmbeddedField(model_container=UsuarioSnapshot)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    items = models.ArrayField(model_container=ItemOrden)
    total = models.IntegerField()
    direccion_envio = models.EmbeddedField(model_container=DireccionEnvio)

    class Meta:
        db_table = 'ordenes'