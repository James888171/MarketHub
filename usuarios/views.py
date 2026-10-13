from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import render, redirect
from MarketHub.conexion import db, siguiente_id
from .models import Usuario


def usuario_actual(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return None
    return db.usuarios.find_one({'id': usuario_id, 'activo': True})


def pagina_inicio(usuario):
    if usuario['rol'] == 'admin':
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

        usuario = db.usuarios.find_one({'email': email})

        if not email or not password:
            error = 'Escribe tu email y tu contraseña.'
        elif not usuario or not check_password(password, usuario['password']):
            error = 'Email o contraseña incorrectos.'
        elif not usuario['activo']:
            error = 'Tu cuenta esta desactivada.'
        else:
            request.session['usuario_id'] = usuario['id']
            request.session['usuario_nombre'] = usuario['nombre']
            request.session['usuario_rol'] = usuario['rol']
            return pagina_inicio(usuario)

    return render(request, 'usuarios/ingresar.html', {'error': error, 'email': email})


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
        elif db.usuarios.find_one({'email': email}):
            error = 'Ya existe una cuenta con ese email.'
        else:
            direccion = None
            if calle and ciudad:
                direccion = {'calle': calle, 'ciudad': ciudad}

            usuario = {
                'id': siguiente_id(db.usuarios),
                'email': email,
                'password': make_password(password),
                'nombre': nombre,
                'rol': 'cliente',
                'activo': True,
                'direccion': direccion,
            }
            db.usuarios.insert_one(usuario)
            request.session['usuario_id'] = usuario['id']
            request.session['usuario_nombre'] = usuario['nombre']
            request.session['usuario_rol'] = usuario['rol']
            return pagina_inicio(usuario)

    return render(request, 'usuarios/registro.html', {'error': error, 'datos': datos})


def salir(request):
    request.session.flush()
    return redirect('usuarios:ingresar')


def mostrar_usuario(request, usuario, persona, error):
    ordenes = list(db.ordenes.find({'usuario._id': persona['_id']}).sort('fecha', -1))

    contexto = {
        'persona': persona,
        'ordenes': ordenes,
        'es_yo': persona['id'] == usuario['id'],
        'error': error,
    }
    return render(request, 'usuarios/usuario_detalle.html', contexto)


def usuario_listar(request):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario['rol'] != 'admin':
        return redirect('productos:catalogo')

    busqueda = request.GET.get('q', '').strip().lower()
    rol = request.GET.get('rol', '')

    filtro = {}
    if busqueda:
        filtro['email'] = busqueda
    if rol:
        filtro['rol'] = rol

    usuarios = list(db.usuarios.find(filtro).sort('nombre', 1))

    contexto = {
        'usuarios': usuarios,
        'busqueda': busqueda,
        'rol': rol,
        'roles': Usuario.ROL_CHOICES,
        'total': db.usuarios.count_documents({}),
    }
    return render(request, 'usuarios/usuario_lista.html', contexto)


def usuario_detalle(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario['rol'] != 'admin':
        return redirect('productos:catalogo')

    persona = db.usuarios.find_one({'id': id})
    if not persona:
        return redirect('usuarios:usuario_listar')

    return mostrar_usuario(request, usuario, persona, None)


def usuario_editar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario['rol'] != 'admin':
        return redirect('productos:catalogo')

    persona = db.usuarios.find_one({'id': id})
    if not persona:
        return redirect('usuarios:usuario_listar')

    error = None
    calle = ''
    ciudad = ''
    if persona.get('direccion'):
        calle = persona['direccion']['calle']
        ciudad = persona['direccion']['ciudad']

    datos = {
        'nombre': persona['nombre'],
        'rol': persona['rol'],
        'calle': calle,
        'ciudad': ciudad,
        'activo': persona['activo'],
    }

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        rol = request.POST.get('rol', '')
        calle = request.POST.get('calle', '').strip()
        ciudad = request.POST.get('ciudad', '').strip()
        activo = request.POST.get('activo') == 'on'
        datos = {'nombre': nombre, 'rol': rol, 'calle': calle, 'ciudad': ciudad, 'activo': activo}

        es_yo = persona['id'] == usuario['id']

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

            db.usuarios.update_one(
                {'id': id},
                {'$set': {
                    'nombre': nombre,
                    'rol': rol,
                    'direccion': direccion,
                    'activo': activo,
                }}
            )

            if es_yo:
                request.session['usuario_nombre'] = nombre

            return redirect('usuarios:usuario_detalle', id=id)

    contexto = {
        'persona': persona,
        'datos': datos,
        'roles': Usuario.ROL_CHOICES,
        'error': error,
    }
    return render(request, 'usuarios/usuario_form.html', contexto)


def usuario_desactivar(request, id):
    usuario = usuario_actual(request)
    if not usuario:
        return redirect('usuarios:ingresar')
    if usuario['rol'] != 'admin':
        return redirect('productos:catalogo')

    persona = db.usuarios.find_one({'id': id})
    if not persona:
        return redirect('usuarios:usuario_listar')

    if persona['id'] == usuario['id']:
        return mostrar_usuario(request, usuario, persona, 'No puedes desactivar tu propia cuenta.')

    if request.method == 'POST':
        db.usuarios.update_one({'id': id}, {'$set': {'activo': False}})
        return redirect('usuarios:usuario_listar')

    return render(request, 'usuarios/usuario_desactivar.html', {'persona': persona})
