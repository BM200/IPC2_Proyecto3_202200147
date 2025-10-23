from django.shortcuts import render
import requests
import json

API_URL_CONFIG = 'http://127.0.0.1:5000/api/cargarConfiguracion'
API_URL_CONSUMO = 'http://127.0.0.1:5000/api/registrarConsumo'

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