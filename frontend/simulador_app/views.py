from django.shortcuts import render
import requests
import json

API_URL_CONFIG = 'http://127.0.0.1:5000/api/cargarConfiguracion'

def pagina_inicio(request):
    context = {}

    if request.method == 'POST':
        # La corrección está aquí: usamos 'request' (el objeto de Django)
        # en lugar de 'requests' (la librería).
        if 'archivo_config' in request.FILES:
            uploaded_file = request.FILES['archivo_config']
            
            xml_content = uploaded_file.read().decode('utf-8')
            
            headers = {'Content-Type': 'application/xml'}
            
            try:
                response = requests.post(API_URL_CONFIG, data=xml_content.encode('utf-8'), headers=headers)
                
                if response.status_code == 200:
                    data_respuesta = response.json()
                    context['tipo_mensaje'] = 'success'
                    context['mensaje'] = data_respuesta.get('mensaje')
                    resumen_dict = data_respuesta.get('resumen_de_carga', {})
                    context['resumen'] = json.dumps(resumen_dict, indent=4, ensure_ascii=False)
                else:
                    context['tipo_mensaje'] = 'error'
                    context['mensaje'] = f"Error del backend (Código: {response.status_code}): {response.text}"

            except requests.exceptions.RequestException as e:
                context['tipo_mensaje'] = 'error'
                context['mensaje'] = f"No se pudo conectar con el backend. ¿Está funcionando? Error: {e}"

    return render(request, 'simulador_app/inicio.html', context)