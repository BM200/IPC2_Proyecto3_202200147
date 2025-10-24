# -----------------------------------------------------------------------------
# app.py - Archivo Principal del Backend (Servicio 2)
# -----------------------------------------------------------------------------
# Este archivo inicializa la aplicación Flask y define todos los endpoints
# de la API requeridos por el proyecto de Tecnologías Chapinas, S.A.
# -----------------------------------------------------------------------------

# --- Importaciones de Librerías ---
from flask import Flask, request, jsonify
from flask_cors import CORS
import xml.etree.ElementTree as ET

# --- Importaciones de Módulos Locales ---
# Importamos las funciones de nuestro módulo de servicios que contienen la
# lógica de negocio para manipular los archivos XML.
from services.xml_manager import (procesar_y_guardar_config_xml, procesar_consumos_xml, agregar_recurso, obtener_datos_completos )


# --- Inicialización de la Aplicación Flask ---
# Creamos la instancia principal de nuestra aplicación.
app = Flask(__name__)

# Configuramos CORS (Cross-Origin Resource Sharing) para permitir que el
# frontend (que se ejecuta en un dominio/puerto diferente) pueda comunicarse
# con este backend sin problemas de seguridad del navegador.
CORS(app)


# --- Ruta de Bienvenida (para pruebas) ---
@app.route('/')
def index():
    """
    Ruta raíz simple para verificar rápidamente que el servidor está en línea
    y respondiendo a peticiones.
    """
    return "¡Servidor Backend de Tecnologías Chapinas funcionando!"


# -----------------------------------------------------------------------------
# Definición de Rutas (Endpoints) de la API
# Todas las rutas de la API comienzan con el prefijo /api para mantenerlas
# -----------------------------------------------------------------------------

@app.route('/api/cargarConfiguracion', methods=['POST'])
def cargar_configuracion():
    """
    Endpoint principal para recibir y procesar el archivo XML de configuración
    que define el estado completo del sistema (recursos, clientes, etc.).
    Este endpoint sobrescribe la configuración existente.
    """
    # 1. Validar que la petición contenga datos XML.
    if 'application/xml' not in request.content_type:
        return jsonify({"error": "La cabecera Content-Type debe ser 'application/xml'"}), 415

    # 2. Decodificar los datos XML del cuerpo de la petición.
    xml_data_string = request.data.decode('utf-8')
    if not xml_data_string:
        return jsonify({"error": "No se recibió contenido en el cuerpo de la petición"}), 400

    # 3. Intentar procesar los datos llamando a la función de servicio.
    try:
        summary = procesar_y_guardar_config_xml(xml_data_string)
        # Si tiene éxito, devolver un resumen de los datos cargados.
        return jsonify({
            "mensaje": "Archivo de configuración cargado y procesado exitosamente.",
            "resumen_de_carga": summary
        }), 200 # 200 OK
    except ET.ParseError:
        # Si el XML está mal formado, devolver un error claro.
        return jsonify({"error": "El XML recibido está mal formado."}), 400
    except Exception as e:
        # Capturar cualquier otro error inesperado.
        print(f"Error inesperado al procesar el archivo de configuración: {e}")
        return jsonify({"error": "Ocurrió un error interno en el servidor"}), 500


@app.route('/api/registrarConsumo', methods=['POST'])
def registrar_consumo():
    """
    Endpoint para registrar uno o más consumos para instancias existentes.
    Este endpoint modifica la configuración existente añadiendo datos de consumo.
    """
    # 1. Validar que la petición contenga datos XML.
    if 'application/xml' not in request.content_type:
        return jsonify({"error": "La cabecera Content-Type debe ser 'application/xml'"}), 415

    # 2. Decodificar los datos XML del cuerpo de la petición.
    xml_data_string = request.data.decode('utf-8')
    if not xml_data_string:
        return jsonify({"error": "No se recibió contenido en el cuerpo de la petición"}), 400

    # 3. Intentar procesar los consumos.
    try:
        resumen = procesar_consumos_xml(xml_data_string)
        # Devolver un resumen de los consumos procesados y los errores encontrados.
        return jsonify({
            "mensaje": "Se procesó el listado de consumos.",
            "resumen_del_proceso": resumen
        }), 200 # 200 OK
    except FileNotFoundError:
        # Error específico si se intenta registrar un consumo sin haber cargado antes una configuración.
        return jsonify({"error": "El archivo de configuración (data.xml) no existe. Cargue una configuración primero."}), 404
    except Exception as e:
        # Capturar cualquier otro error inesperado.
        print(f"Error inesperado al registrar consumo: {e}")
        return jsonify({"error": "Ocurrió un error interno en el servidor"}), 500


@app.route('/api/crearRecurso', methods=['POST'])
def crear_recurso():
    """
    Endpoint auxiliar para crear un único recurso. A diferencia de los otros,
    este endpoint espera recibir los datos en formato JSON.
    """
    # 1. Obtener los datos JSON de la petición.
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibieron datos en formato JSON"}), 400

    # 2. Intentar agregar el recurso al archivo XML.
    try:
        recurso_creado = agregar_recurso(data)
        # Devolver el recurso creado con el ID asignado.
        return jsonify({
            "mensaje": "Recurso almacenado en XML exitosamente",
            "recurso": recurso_creado
        }), 201 # 201 Created
    except Exception as e:
        # Capturar cualquier error durante la escritura del archivo.
        print(f"Error al escribir en XML: {e}")
        return jsonify({"error": "Ocurrió un error al procesar la solicitud"}), 500
    
   
#ENDPOINT PARA CONSULTAR DATOS

@app.route('/api/consultarDatos', methods=['GET'])
def consultar_datos():
    """
    Endpoint para leer y devolver todo el contenido del archivo data.xml
    en formato JSON.
    """
    try:
        # Llama a la función del servicio que lee y convierte el XML a diccionario
        datos_completos = obtener_datos_completos()
        return jsonify(datos_completos)
    except FileNotFoundError:
        return jsonify({"error": "No se han cargado datos. El archivo data.xml no existe."}), 404
    except Exception as e:
        print(f"Error inesperado al consultar datos: {e}")
        return jsonify({"error": "Ocurrió un error interno al leer los datos."}), 500



# Al final de app.py, antes del if __name__ == '__main__':

@app.route('/api/generarFactura', methods=['POST'])
def endpoint_generar_factura():
    data = request.get_json()
    fecha_inicio = data.get('fecha_inicio') # Formato esperado: YYYY-MM-DD
    fecha_fin = data.get('fecha_fin')     # Formato esperado: YYYY-MM-DD

    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Debe proporcionar fecha_inicio y fecha_fin"}), 400
    
    try:
        facturas = generar_facturacion(fecha_inicio, fecha_fin)
        return jsonify({
            "mensaje": f"Se generaron {len(facturas)} facturas para el período del {fecha_inicio} al {fecha_fin}.",
            "facturas": facturas
        })
    except Exception as e:
        print(f"Error al generar facturación: {e}")
        return jsonify({"error": "Ocurrió un error interno al generar la facturación."}), 500

# --- Punto de Entrada para Ejecutar el Servidor ---
# Este bloque de código solo se ejecuta cuando el script es llamado directamente
# (es decir, con 'python app.py'), y no cuando es importado por otro módulo.
if __name__ == '__main__':
    # Inicia el servidor de desarrollo de Flask.
    # port=5000: El servidor escuchará en el puerto 5000.
    # debug=True: Activa el modo de depuración, que reinicia automáticamente
    #             el servidor cada vez que guardas un cambio en el código.
    app.run(port=5000, debug=True)