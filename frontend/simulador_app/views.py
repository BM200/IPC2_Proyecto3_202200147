from django.shortcuts import render
import requests
import json

API_URL_CONFIG = 'http://127.0.0.1:5000/api/cargarConfiguracion'
API_URL_CONSUMO = 'http://127.0.0.1:5000/api/registrarConsumo'
API_URL_CONSULTA = 'http://127.0.0.1:5000/api/consultarDatos'

def pagina_inicio(request):
    context = {}
    
    if request.method == 'POST':
        #identicamos que formulario se envio en el frontend 
        form_type = request.POST.get('form_type')
        
        if form_type == 'configuracion' and 'archivo_config' in request.FILES:

            uploaded_file = request.FILES['archivo_config']
            api_url = API_URL_CONFIG
            success_key = 'resumen_de_carga'
        
        elif form_type == 'consumo' and 'archivo_consumo' in request.FILES:
            uploaded_file = request.FILES['archivo_consumo']
            api_url = API_URL_CONSUMO
            success_key = 'resumen_del_proceso'

        else:
            #mensaje de error si no se encuentra el archivo. 
            context['tipo_mensaje'] = 'error'
            context['mensaje'] = 'No se envió un archivo válido o el formulario es incorrecto. '

            return render(request, 'simulador_app/inicio.html', context)
        
            #Logica para ambos formularios. 
        xml_content = uploaded_file.read()
            
        headers = {'Content-Type': 'application/xml; charset = utf-8'}

        try:
            response = requests.post(api_url, data=xml_content, headers=headers)
                
            if response.status_code in [ 200, 201]:
                data_respuesta = response.json()
                context['tipo_mensaje'] = 'success'
                context['mensaje'] = data_respuesta.get('mensaje')
                resumen_dict = data_respuesta.get(success_key, {})
                context['resumen'] = json.dumps(resumen_dict, indent=4, ensure_ascii=False)
            else:
                context['tipo_mensaje'] = 'error'
                context['mensaje'] = f"Error del backend (Código: {response.status_code})"
                context['resumen'] = response.text


        except requests.exceptions.RequestException as e:
                context['tipo_mensaje'] = 'error'
                context['mensaje'] = f"No se pudo conectar con el backend. ¿Está funcionando? Error: {e}"

    return render(request, 'simulador_app/inicio.html', context)

def pagina_consulta(request):
    """
    Vista para obtener y mostrar todos los datos del backend.
    """
    context = {}
    try:
        response = requests.get(API_URL_CONSULTA)

        if response.status_code == 200:
            datos_json = response.json()
            
            # --- LÓGICA CLAVE PARA CORREGIR LOS DATOS ---
            # Navegamos hasta la sección de clientes
            config = datos_json.get('archivoConfiguraciones', {})
            lista_clientes = config.get('listaClientes', {})
            
            # Verificamos si existe la clave 'cliente'
            if 'cliente' in lista_clientes:
                clientes_data = lista_clientes['cliente']
                
                # Si 'cliente' NO es una lista (es un solo diccionario), lo convertimos en una lista
                if not isinstance(clientes_data, list):
                    lista_clientes['cliente'] = [clientes_data]

                # Hacemos lo mismo para las instancias dentro de cada cliente
                for cliente in lista_clientes['cliente']:
                    if 'listaInstancias' in cliente and 'instancia' in cliente['listaInstancias']:
                        instancias_data = cliente['listaInstancias']['instancia']
                        if not isinstance(instancias_data, list):
                            cliente['listaInstancias']['instancia'] = [instancias_data]
            
            context['datos'] = datos_json
        else:
            context['error'] = f"Error del backend (Código: {response.status_code}): {response.json().get('error')}"

    except requests.exceptions.RequestException as e:
        context['error'] = f"No se pudo conectar con el backend. ¿Está funcionando? Error: {e}"
        
    return render(request, 'simulador_app/consulta_datos.html', context)