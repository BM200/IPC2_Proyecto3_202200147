# --- frontend/simulador_app/views.py ---

from django.shortcuts import render
from django.http import HttpResponse
import requests
import json

# --- URLs de los Endpoints del Backend ---
API_URL_CONFIG = 'http://127.0.0.1:5000/api/cargarConfiguracion'
API_URL_CONSUMO = 'http://127.0.0.1:5000/api/registrarConsumo'
API_URL_CONSULTA = 'http://127.0.0.1:5000/api/consultarDatos'
API_URL_FACTURA = 'http://127.0.0.1:5000/api/generarFactura'
API_URL_RESETEAR = 'http://127.0.0.1:5000/api/resetear'
API_URL_DETALLE_FACTURA = 'http://127.0.0.1:5000/api/detalleFactura'
API_URL_REPORTE_VENTAS = 'http://127.0.0.1:5000/api/reporteVentas'


# --- Vista Principal (Página de Inicio) ---
def pagina_inicio(request):
    """
    Maneja la página de inicio, incluyendo la lógica para procesar todos los formularios.
    """
    context = {}
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        api_url = ''
        headers = {}
        payload = None

        # --- Lógica para cada tipo de formulario ---
        if form_type == 'configuracion' and 'archivo_config' in request.FILES:
            api_url = API_URL_CONFIG
            payload = request.FILES['archivo_config'].read()
            headers = {'Content-Type': 'application/xml; charset=utf-8'}
        
        elif form_type == 'consumo' and 'archivo_consumo' in request.FILES:
            api_url = API_URL_CONSUMO
            payload = request.FILES['archivo_consumo'].read()
            headers = {'Content-Type': 'application/xml; charset=utf-8'}

        elif form_type == 'facturacion':
            api_url = API_URL_FACTURA
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_fin = request.POST.get('fecha_fin')
            payload = json.dumps({"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin})
            headers = {'Content-Type': 'application/json'}

        elif form_type == 'resetear':
            api_url = API_URL_RESETEAR
            payload = None
            headers = {}
        
        else:
            context['tipo_mensaje'] = 'error'
            context['mensaje'] = 'Formulario no válido o archivo no encontrado.'
            return render(request, 'simulador_app/inicio.html', context)

        # --- Lógica común de envío de petición y manejo de respuesta ---
        try:
            response = requests.post(api_url, data=payload, headers=headers)
            data_respuesta = response.json()

            if response.status_code in [200, 201]:
                context['tipo_mensaje'] = 'success'
                context['mensaje'] = data_respuesta.get('mensaje')
                
                # Manejo de los diferentes tipos de resúmenes o datos
                if 'resumen_de_carga' in data_respuesta: context['resumen'] = json.dumps(data_respuesta['resumen_de_carga'], indent=4)
                if 'resumen_del_proceso' in data_respuesta: context['resumen'] = json.dumps(data_respuesta['resumen_del_proceso'], indent=4)
                
                # Si se generaron facturas, las mostramos y las guardamos en la sesión
                if 'facturas' in data_respuesta:
                    context['facturas'] = data_respuesta['facturas']
                    request.session['facturas_generadas'] = data_respuesta.get('facturas', [])
                    request.session['detalles_facturacion'] = data_respuesta.get('detalles_consumo', [])
            else:
                context['tipo_mensaje'] = 'error'
                context['mensaje'] = f"Error del backend (Código: {response.status_code})"
                context['resumen'] = data_respuesta.get('error', response.text)

        except requests.exceptions.RequestException as e:
            context['tipo_mensaje'] = 'error'
            context['mensaje'] = f"No se pudo conectar con el backend. ¿Está funcionando? Error: {e}"

    return render(request, 'simulador_app/inicio.html', context)


# --- Vista para Consultar Datos ---
def pagina_consulta(request):
    """
    Obtiene todos los datos del backend y los prepara para ser mostrados en la plantilla.
    """
    context = {}
    try:
        response = requests.get(API_URL_CONSULTA)
        if response.status_code == 200:
            datos_json = response.json()
            config = datos_json.get('archivoConfiguraciones', {})
            
            # Lógica para asegurar que los elementos a iterar siempre sean listas
            if 'listaClientes' in config and 'cliente' in config['listaClientes']:
                clientes_data = config['listaClientes']['cliente']
                if not isinstance(clientes_data, list): config['listaClientes']['cliente'] = [clientes_data]
                for cliente in config['listaClientes']['cliente']:
                    if 'listaInstancias' in cliente and 'instancia' in cliente['listaInstancias']:
                        instancias_data = cliente['listaInstancias']['instancia']
                        if not isinstance(instancias_data, list): cliente['listaInstancias']['instancia'] = [instancias_data]
            
            if 'listaRecursos' in config and 'recurso' in config['listaRecursos']:
                 recursos_data = config['listaRecursos']['recurso']
                 if not isinstance(recursos_data, list): config['listaRecursos']['recurso'] = [recursos_data]

            context['datos'] = datos_json
        else:
            context['error'] = f"Error del backend (Código: {response.status_code}): {response.json().get('error')}"
    except requests.exceptions.RequestException as e:
        context['error'] = f"No se pudo conectar con el backend. ¿Está funcionando? Error: {e}"
        
    return render(request, 'simulador_app/consulta_datos.html', context)


# --- Vista para Generar Reporte de Ventas en PDF ---
def generar_reporte_ventas(request):
    """
    Recibe un rango de fechas y solicita el PDF de análisis de ventas al backend.
    """
    if request.method == 'POST':
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        payload = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
        
        try:
            response = requests.post(API_URL_REPORTE_VENTAS, json=payload)
            if response.status_code == 200:
                response_pdf = HttpResponse(response.content, content_type='application/pdf')
                response_pdf['Content-Disposition'] = 'attachment; filename="reporte_ventas.pdf"'
                return response_pdf
            else:
                return HttpResponse(f"Error del backend: {response.text}", status=500)
        except requests.exceptions.RequestException as e:
            return HttpResponse(f"Error de conexión: {e}", status=500)
    return HttpResponse("Método no permitido", status=405)


# --- Vista para Generar Detalle de Factura en PDF ---
def detalle_factura(request):
    """
    Recupera los datos de la sesión y solicita un PDF con el detalle de una factura específica.
    """
    if request.method == 'POST':
        numero_factura = request.POST.get('numero_factura')
        
        facturas_generadas = request.session.get('facturas_generadas', [])
        todos_los_detalles = request.session.get('detalles_facturacion', [])
        
        factura_info = next((f for f in facturas_generadas if str(f['numero_factura']) == numero_factura), None)
        
        if not factura_info:
            return HttpResponse("Error: No se encontró la información de la factura en la sesión.", status=404)

        nit_cliente_factura = factura_info['nit_cliente']
        detalles_filtrados = [d for d in todos_los_detalles if d['nit_cliente'] == nit_cliente_factura]
        
        payload = { "factura_info": factura_info, "detalles_consumo": detalles_filtrados }

        try:
            response = requests.post(API_URL_DETALLE_FACTURA, json=payload)
            if response.status_code == 200:
                response_pdf = HttpResponse(response.content, content_type='application/pdf')
                response_pdf['Content-Disposition'] = f'attachment; filename="factura_{numero_factura}.pdf"'
                return response_pdf
            else:
                return HttpResponse(f"Error del backend: {response.text}", status=500)
        except requests.exceptions.RequestException as e:
            return HttpResponse(f"Error de conexión: {e}", status=500)
            
    return HttpResponse("Método no permitido", status=405)