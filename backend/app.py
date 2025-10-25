# --- backend/app.py ---

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import xml.etree.ElementTree as ET
import os
from services.pdf_generator import generar_analisis_ventas_pdf
from services.pdf_generator import generar_detalle_factura_pdf


# Importamos TODAS las funciones que los endpoints van a necesitar
from services.xml_manager import (
    procesar_y_guardar_config_xml,
    procesar_consumos_xml,
    obtener_datos_completos,
    generar_facturacion_detallada  # <-- La nueva función
)

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "¡Servidor Backend de Tecnologías Chapinas funcionando!"

@app.route('/api/cargarConfiguracion', methods=['POST'])
def cargar_configuracion():
    xml_data_string = request.data.decode('utf-8')
    try:
        summary = procesar_y_guardar_config_xml(xml_data_string)
        return jsonify({"mensaje": "Archivo de configuración cargado exitosamente.", "resumen_de_carga": summary}), 200
    except Exception as e:
        return jsonify({"error": f"Error al procesar configuración: {e}"}), 500

@app.route('/api/registrarConsumo', methods=['POST'])
def registrar_consumo():
    xml_data_string = request.data.decode('utf-8')
    try:
        resumen = procesar_consumos_xml(xml_data_string)
        return jsonify({"mensaje": "Se procesó el listado de consumos.", "resumen_del_proceso": resumen}), 200
    except FileNotFoundError:
        return jsonify({"error": "El archivo data.xml no existe. Cargue una configuración primero."}), 404
    except Exception as e:
        return jsonify({"error": f"Error al registrar consumo: {e}"}), 500

@app.route('/api/consultarDatos', methods=['GET'])
def consultar_datos():
    try:
        datos_completos = obtener_datos_completos()
        return jsonify(datos_completos)
    except FileNotFoundError:
        return jsonify({"error": "No se han cargado datos. El archivo data.xml no existe."}), 404
    except Exception as e:
        return jsonify({"error": f"Error interno al leer los datos: {e}"}), 500

# --- 
#  ENDPOINT PARA FACTURACIÓN ---
@app.route('/api/generarFactura', methods=['POST'])
def endpoint_generar_factura():
    data = request.get_json()
    fecha_inicio = data.get('fecha_inicio')
    fecha_fin = data.get('fecha_fin')

    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Debe proporcionar fecha_inicio y fecha_fin"}), 400
    
    try:
        resultado = generar_facturacion_detallada(fecha_inicio, fecha_fin)

        return jsonify({

             "mensaje": f"Se generaron {len(resultado['facturas'])} facturas...",
            "facturas": resultado['facturas'], # Extraemos solo las facturas
            "detalles_consumo": resultado['detalles_consumo']
        })
    except Exception as e:
        print(f"Error al generar facturación: {e}")
        return jsonify({"error": "Ocurrió un error interno al generar la facturación."}), 500


@app.route('/api/reporteVentas', methods=['POST'])
def endpoint_reporte_ventas():
    data = request.get_json()
    fecha_inicio = data.get('fecha_inicio')
    fecha_fin = data.get('fecha_fin')
    try:
        pdf_path = generar_analisis_ventas_pdf(fecha_inicio, fecha_fin)
        # Esta línea mágica envía el archivo al navegador para que se descargue
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        print(f"Error al generar reporte PDF: {e}")
        return jsonify({"error": "Ocurrió un error al generar el reporte."}), 500
# Al final de app.py

@app.route('/api/resetear', methods=['POST'])
def endpoint_resetear_sistema():
    """
    Endpoint para eliminar el archivo data.xml y reiniciar el estado del sistema.
    """
    try:
        # La ruta a nuestro archivo de "base de datos"
        db_file_path = os.path.join(os.path.dirname(__file__), 'data.xml')
        if os.path.exists(db_file_path):
            os.remove(db_file_path)
        return jsonify({"mensaje": "El sistema ha sido reseteado. Todos los datos han sido eliminados."})
    except Exception as e:
        print(f"Error al resetear el sistema: {e}")
        return jsonify({"error": "Ocurrió un error al intentar resetear los datos."}), 500
    

@app.route('/api/detalleFactura', methods=['POST'])
def endpoint_detalle_factura():
    # Esta vez, el frontend nos enviará los datos ya calculados
    datos_factura = request.get_json()
    if not datos_factura:
        return jsonify({"error": "No se recibieron datos de la factura"}), 400
    
    try:
        pdf_path = generar_detalle_factura_pdf(datos_factura)
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        print(f"Error al generar detalle de factura: {e}")
        return jsonify({"error": "Ocurrió un error al generar el detalle de la factura."}), 500
    

if __name__ == '__main__':
    app.run(port=5000, debug=True)