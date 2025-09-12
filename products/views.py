# products/views.py - ACTUALIZADO para usar accounts app
import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import ProductForm

base_url = "https://api.escuelajs.co/api/v1/"

def product_list(request):
    try:
        response = requests.get(f"{base_url}products/", timeout=20)
        response.raise_for_status()
        productos = response.json()
    except requests.RequestException:
        productos = []
        messages.error(request, 'Error al cargar los productos desde la API.')

    # Extraer categorías únicas
    categorias = sorted({
        p['category']['name']
        for p in productos
        if p.get('category') and p['category'].get('name')
    })

    # Filtrar por categoría si existe el parámetro GET
    selected = request.GET.get('category', 'All')
    if selected != 'All':
        productos = [
            p for p in productos
            if p.get('category') and p['category'].get('name') == selected
        ]

    # Filtrar por búsqueda si existe el parámetro GET
    search_query = request.GET.get('search', '').strip()
    if search_query:
        productos = [
            p for p in productos
            if (search_query.lower() in p.get('title', '').lower() or 
                search_query.lower() in p.get('description', '').lower() or
                (p.get('category') and search_query.lower() in p['category'].get('name', '').lower()))
        ]

    context = {
        'productos': productos,
        'categorias': ['All'] + categorias,
        'selected': selected,
        'search_query': search_query,
    }
    return render(request, 'products/product_list.html', context)


@login_required(login_url='accounts:login')
def product_create(request):
    # 1. Obtener categorías desde la API
    try:
        resp_cat = requests.get(f'{base_url}categories/', timeout=10)
        resp_cat.raise_for_status()
        cats_json = resp_cat.json()
        # Transformar a lista (id, nombre)
        categories = [(c['id'], c['name']) for c in cats_json if c.get('id') and c.get('name')]
    except requests.RequestException:
        categories = []
        messages.error(request, 'Error al cargar las categorías.')

    if request.method == 'POST':
        form = ProductForm(request.POST, categories=categories)
        if form.is_valid():
            # 2. Construir el payload a enviar
            payload = {
                "title":       form.cleaned_data['title'],
                "price":       float(form.cleaned_data['price']),
                "description": form.cleaned_data['description'],
                "categoryId":  int(form.cleaned_data['category']),
                "images":      [form.cleaned_data['image']],
            }
            try:
                # 3. Consumo del endpoint POST
                headers = {'Content-Type': 'application/json'}
                
                # Si tenemos token en sesión, agregarlo
                if 'api_token' in request.session:
                    headers['Authorization'] = f'Bearer {request.session["api_token"]}'
                
                resp_post = requests.post(
                    f'{base_url}products/',
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                resp_post.raise_for_status()
                
                # 4. Al crear con éxito, redirigir al listado
                product_data = resp_post.json()
                product_title = product_data.get('title', 'Producto')
                messages.success(request, f'✅ "{product_title}" ha sido creado exitosamente.')
                return redirect('products:product_list')
                
            except requests.RequestException as e:
                messages.error(request, 'Error al crear el producto en la API. Intenta nuevamente.')
                form.add_error(None, 'Error al crear el producto en la API')
    else:
        form = ProductForm(categories=categories)

    return render(request, 'products/product_create.html', {
        'form': form
    })


@login_required(login_url='accounts:login')
def product_update(request, product_id):
    # 1. Traer datos del producto actual
    try:
        resp = requests.get(f'{base_url}products/{product_id}', timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        messages.error(request, 'No se pudo cargar el producto solicitado.')
        return redirect('products:product_list')

    # 2. Obtener lista de categorías para el select
    try:
        resp_cat = requests.get(f'{base_url}categories/', timeout=10)
        resp_cat.raise_for_status()
        cats_json = resp_cat.json()
        categories = [(c['id'], c['name']) for c in cats_json if c.get('id') and c.get('name')]
    except requests.RequestException:
        categories = []
        messages.warning(request, 'Error al cargar las categorías.')

    if request.method == 'POST':
        form = ProductForm(request.POST, categories=categories)
        if form.is_valid():
            payload = {
                "title":       form.cleaned_data['title'],
                "price":       float(form.cleaned_data['price']),
                "description": form.cleaned_data['description'],
                "categoryId":  int(form.cleaned_data['category']),
                "images":      [form.cleaned_data['image']],
            }
            try:
                # 3. Enviar PUT a la API
                headers = {'Content-Type': 'application/json'}
                
                # Si tenemos token en sesión, agregarlo
                if 'api_token' in request.session:
                    headers['Authorization'] = f'Bearer {request.session["api_token"]}'
                
                resp_put = requests.put(
                    f'{base_url}products/{product_id}',
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                resp_put.raise_for_status()
                
                product_title = payload.get('title', 'Producto')
                messages.success(request, f'✅ "{product_title}" ha sido actualizado exitosamente.')
                return redirect('products:product_list')
                
            except requests.RequestException:
                messages.error(request, 'Error al actualizar el producto. Intenta nuevamente.')
                form.add_error(None, 'Error al actualizar el producto.')
    else:
        # 4. Cargar datos iniciales en el formulario
        initial = {
            'title':       data.get('title', ''),
            'price':       data.get('price', 0),
            'description': data.get('description', ''),
            'category':    data.get('category', {}).get('id') if data.get('category') else None,
            'image':       data.get('images', [''])[0] if data.get('images') else '',
        }
        form = ProductForm(initial=initial, categories=categories)

    return render(request, 'products/product_update.html', {
        'form': form,
        'product_id': product_id,
        'product_title': data.get('title', f'Producto #{product_id}')
    })


@login_required(login_url='accounts:login')
def product_delete(request, product_id):
    if request.method == 'POST':
        try:
            # Obtener información del producto antes de eliminarlo
            resp_get = requests.get(f'{base_url}products/{product_id}', timeout=5)
            product_title = "Producto"
            if resp_get.status_code == 200:
                product_data = resp_get.json()
                product_title = product_data.get('title', f'Producto #{product_id}')
            
            # Eliminar el producto
            headers = {}
            
            # Si tenemos token en sesión, agregarlo
            if 'api_token' in request.session:
                headers['Authorization'] = f'Bearer {request.session["api_token"]}'
            
            resp = requests.delete(
                f'{base_url}products/{product_id}',
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            
            messages.success(request, f'🗑️ "{product_title}" ha sido eliminado exitosamente.')
            
        except requests.RequestException:
            messages.error(request, 'Error al eliminar el producto. Intenta nuevamente.')

    return redirect('products:product_list')