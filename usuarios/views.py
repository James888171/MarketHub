from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.shortcuts import render, redirect
from ordenes.models import Orden
from .forms import FormularioIngresar, FormularioRegistro, FormularioUsuario
from .models import Usuario


def usuario_actual(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return None
    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except ObjectDoesNotExist:
        return None
    if not usuario.activo:
        return None
    return usuario


def pagina_inicio(usuario):
    if usuario.rol == 'admin':
        return redirect('categorias:categoria_listar')
    return redirect('productos:catalogo')


def ingresar(request):
    usuario = usuario_actual(request)
    if usuario:
        return pagina_inicio(usuario)

    error = None
    email = ''

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        usuario = Usuario.objects.filter(email=email).first()

        if not email or not password:
            error = 'Escribe tu email y tu contraseña.'
        elif not usuario or not check_password(password, usuario.password):
            error = 'Email o contraseña incorrectos.'
        elif not usuario.activo:
            error = 'Tu cuenta esta desactivada.'
        else:
            request.session['usuario_id'] = usuario.id
            request.session['usuario_nombre'] = usuario.nombre
            request.session['usuario_rol'] = usuario.rol
            return pagina_inicio(usuario)

    formulario = FormularioIngresar(initial={'email': email})
    return render(request, 'usuarios/ingresar.html', {'error': error, 'formulario': formulario})


def registrarse(request):
    usuario = usuario_actual(request)
    if usuario:
        return pagina_inicio(usuario)

    error = None
    datos = {'nombre': '', 'email': '', 'calle': '', 'ciudad': ''}

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirmar = request.POST.get('confirmar', '')
        calle = request.POST.get('calle', '').strip()
        ciudad = request.POST.get('ciudad', '').strip()
        datos = {'nombre': nombre, 'email': email, 'calle': calle, 'ciudad': ciudad}

        if not nombre or not email or not password:
            error = 'Nombre, email y contraseña son obligatorios.'
        elif '@' not in email:
            error = 'El email no es valido.'
        elif len(password) < 6:
            error = 'La contraseña debe tener al menos 6 caracteres.'
        elif password != confirmar:
            error = 'Las contraseñas no coinciden.'
        elif Usuario.objects.filter(email=email).first():
            error = 'Ya existe una cuenta con ese email.'
        else:
            direccion = None
            if calle and ciudad:
                direccion = {'calle': calle, 'ciudad': ciudad}

            try:
                usuario = Usuario.objects.create(
                    email=email,
                    password=make_password(password),
                    nombre=nombre,
                    rol='cliente',
                    activo=True,
                    direccion=direccion,
                )
                request.session['usuario_id'] = usuario.id
                request.session['usuario_nombre'] = usuario.nombre
                request.session['usuario_rol'] = usuario.rol
                return pagina_inicio(usuario)
            except DatabaseError:
                error = 'Los datos no cumplen con la validacion de la base de datos.'

    formulario = FormularioRegistro(initial=datos)
    return render(request, 'usuarios/registro.html', {'error': error, 'formulario': formulario})


def salir(request):
    request.session.flush()
    return redirect('usuarios:ingresar')


def mostrar_usuario(request, usuario, persona, error):
    ordenes = Orden.objects.filter(usuario={'usuario_id': persona.id}).order_by('-fecha')

    contexto = {
        'persona': persona,
        'ordenes': ordenes,
        'es_yo': persona.id == usuario.id,
        'error': error,
    }
    return render(request, 'usuarios/usuario_detalle.html', contexto)


def usuario_listar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('productos:catalogo')

    busqueda = request.GET.get('q', '').strip().lower()
    rol = request.GET.get('rol', '')

    usuarios = Usuario.objects.all()
    if busqueda:
        usuarios = usuarios.filter(email=busqueda)
    if rol:
        usuarios = usuarios.filter(rol=rol)
    usuarios = usuarios.order_by('nombre')

    contexto = {
        'usuarios': usuarios,
        'busqueda': busqueda,
        'rol': rol,
        'roles': Usuario.ROL_CHOICES,
        'total': Usuario.objects.count(),
    }
    return render(request, 'usuarios/usuario_lista.html', contexto)


def usuario_detalle(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('productos:catalogo')

    try:
        persona = Usuario.objects.get(id=id)
    except ObjectDoesNotExist:
        return redirect('usuarios:usuario_listar')

    return mostrar_usuario(request, usuario, persona, None)


def usuario_editar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('productos:catalogo')

    try:
        persona = Usuario.objects.get(id=id)
    except ObjectDoesNotExist:
        return redirect('usuarios:usuario_listar')

    error = None
    calle = ''
    ciudad = ''
    if persona.direccion:
        calle = persona.direccion['calle']
        ciudad = persona.direccion['ciudad']

    datos = {
        'nombre': persona.nombre,
        'rol': persona.rol,
        'calle': calle,
        'ciudad': ciudad,
        'activo': persona.activo,
    }

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        rol = request.POST.get('rol', '')
        calle = request.POST.get('calle', '').strip()
        ciudad = request.POST.get('ciudad', '').strip()
        activo = request.POST.get('activo') == 'on'
        datos = {'nombre': nombre, 'rol': rol, 'calle': calle, 'ciudad': ciudad, 'activo': activo}

        es_yo = persona.id == usuario.id

        if not nombre:
            error = 'El nombre es obligatorio.'
        elif rol != 'cliente' and rol != 'admin':
            error = 'El rol no es valido.'
        elif es_yo and rol != 'admin':
            error = 'No puedes quitarte tu propio rol de admin.'
        elif es_yo and not activo:
            error = 'No puedes desactivar tu propia cuenta.'
        elif (calle and not ciudad) or (ciudad and not calle):
            error = 'La direccion debe tener calle y ciudad.'
        else:
            direccion = None
            if calle and ciudad:
                direccion = {'calle': calle, 'ciudad': ciudad}

            persona.nombre = nombre
            persona.rol = rol
            persona.direccion = direccion
            persona.activo = activo

            try:
                persona.save()
                if es_yo:
                    request.session['usuario_nombre'] = nombre
                return redirect('usuarios:usuario_detalle', id=id)
            except DatabaseError:
                error = 'Los datos no cumplen con la validacion de la base de datos.'

    contexto = {
        'persona': persona,
        'formulario': FormularioUsuario(initial=datos),
        'error': error,
    }
    return render(request, 'usuarios/usuario_form.html', contexto)


def usuario_desactivar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario.rol != 'admin':
        return redirect('productos:catalogo')

    try:
        persona = Usuario.objects.get(id=id)
    except ObjectDoesNotExist:
        return redirect('usuarios:usuario_listar')

    if persona.id == usuario.id:
        return mostrar_usuario(request, usuario, persona, 'No puedes desactivar tu propia cuenta.')

    if request.method == 'POST':
        persona.activo = False
        persona.save()
        return redirect('usuarios:usuario_listar')

    return render(request, 'usuarios/usuario_desactivar.html', {'persona': persona})
