import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'data.xml')

# --- (Las funciones de inicializar, guardar config y procesar consumos se quedan igual) ---
def inicializar_xml_si_no_existe():
    if not os.path.exists(DB_FILE):
        root = ET.Element('archivoConfiguraciones')
        ET.SubElement(root, 'listaRecursos')
        ET.SubElement(root, 'listaCategorias')
        ET.SubElement(root, 'listaClientes')
        tree = ET.ElementTree(root)
        tree.write(DB_FILE, encoding='utf-8', xml_declaration=True)

def procesar_y_guardar_config_xml(xml_string):
    root = ET.fromstring(xml_string)
    tree = ET.ElementTree(root)
    tree.write(DB_FILE, encoding='utf-8', xml_declaration=True)
    recursos = root.findall('.//listaRecursos/recurso')
    categorias = root.findall('.//listaCategorias/categoria')
    clientes = root.findall('.//listaClientes/cliente')
    total_instancias = root.findall('.//instancia')
    return {"recursos_cargados": len(recursos), "categorias_cargadas": len(categorias), "clientes_cargados": len(clientes), "total_instancias_registradas": len(total_instancias)}

def procesar_consumos_xml(consumos_xml_string):
    tree_db = ET.parse(DB_FILE)
    root_db = tree_db.getroot()
    root_consumos = ET.fromstring(consumos_xml_string)
    # ... (resto de la función sin cambios)
    consumos_procesados = 0
    errores = []
    for consumo_node in root_consumos.findall('consumo'):
        nit = consumo_node.get('nitCliente')
        id_instancia = consumo_node.get('idInstancia')
        tiempo = consumo_node.find('tiempo').text
        fecha_hora = consumo_node.find('fechaHora').text
        cliente_target = root_db.find(f".//cliente[@nit='{nit}']")
        if cliente_target is None:
            errores.append(f"Cliente con NIT '{nit}' no encontrado.")
            continue
        instancia_target = cliente_target.find(f".//instancia[@id='{id_instancia}']")
        if instancia_target is None:
            errores.append(f"Instancia con ID '{id_instancia}' para cliente '{nit}' no encontrada.")
            continue
        lista_consumos_node = instancia_target.find('listaConsumos')
        if lista_consumos_node is None:
            lista_consumos_node = ET.SubElement(instancia_target, 'listaConsumos')
        nuevo_consumo = ET.SubElement(lista_consumos_node, 'consumoRegistrado')
        ET.SubElement(nuevo_consumo, 'tiempo').text = tiempo
        ET.SubElement(nuevo_consumo, 'fechaHora').text = fecha_hora
        consumos_procesados += 1
    tree_db.write(DB_FILE, encoding='utf-8', xml_declaration=True)
    return {"consumos_procesados_exitosamente": consumos_procesados, "errores_encontrados": errores}

def convertir_elemento_a_dict(elemento):
    dict_resultado = {}
    dict_resultado.update(elemento.attrib)
    for hijo in elemento:
        valor_hijo = convertir_elemento_a_dict(hijo)
        if hijo.tag in dict_resultado:
            if type(dict_resultado[hijo.tag]) is not list: dict_resultado[hijo.tag] = [dict_resultado[hijo.tag]]
            dict_resultado[hijo.tag].append(valor_hijo)
        else:
            dict_resultado[hijo.tag] = valor_hijo
    texto = elemento.text.strip() if elemento.text else None
    if not dict_resultado and texto: return texto
    if texto and 'valor' not in dict_resultado: dict_resultado['valor'] = texto
    return dict_resultado

def obtener_datos_completos():
    if not os.path.exists(DB_FILE): raise FileNotFoundError("El archivo data.xml no existe.")
    tree = ET.parse(DB_FILE)
    root = tree.getroot()
    return {root.tag: convertir_elemento_a_dict(root)}

def extraer_fecha(texto_fecha):
    patron = r'(\d{2}/\d{2}/\d{4})'
    coincidencia = re.search(patron, texto_fecha)
    if coincidencia:
        fecha_str = coincidencia.group(1)
        return datetime.strptime(fecha_str, '%d/%m/%Y')
    return None

def generar_facturacion_detallada(fecha_inicio_str, fecha_fin_str):
    fecha_inicio_rango = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
    fecha_fin_rango = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
    datos = obtener_datos_completos()['archivoConfiguraciones']
    
    recursos_base_list = datos.get('listaRecursos', {}).get('recurso', [])
    if not isinstance(recursos_base_list, list): recursos_base_list = [recursos_base_list]
    recursos_base = {r['id']: r for r in recursos_base_list}
    
    clientes = datos.get('listaClientes', {}).get('cliente', [])
    if not isinstance(clientes, list): clientes = [clientes]
    
    categorias = datos.get('listaCategorias', {}).get('categoria', [])
    if not isinstance(categorias, list): categorias = [categorias]

    facturas_generadas = []
    detalles_consumo = []
    numero_factura_actual = int(datetime.now().timestamp())

    for cliente in clientes:
        monto_total_cliente = 0.0
        instancias = cliente.get('listaInstancias', {}).get('instancia', [])
        if not isinstance(instancias, list): instancias = [instancias]
        for instancia in instancias:
            consumos = instancia.get('listaConsumos', {}).get('consumoRegistrado', [])
            if not isinstance(consumos, list): consumos = [consumos]
            for consumo in consumos:
                fecha_consumo = extraer_fecha(consumo['fechaHora'])
                if fecha_consumo and fecha_inicio_rango <= fecha_consumo <= fecha_fin_rango:
                    tiempo_consumido = float(consumo['tiempo'])
                    id_config_instancia = instancia['idConfiguracion']
                    
                    config_usada = None
                    categoria_usada_nombre = "N/A"
                    for categoria in categorias:
                        configuraciones = categoria.get('listaConfiguraciones', {}).get('configuracion', [])
                        if not isinstance(configuraciones, list): configuraciones = [configuraciones]
                        for conf in configuraciones:
                            if conf['id'] == id_config_instancia:
                                config_usada = conf
                                categoria_usada_nombre = categoria['nombre']
                                break
                        if config_usada: break
                    
                    if config_usada:
                        recursos_config = config_usada.get('recursosConfiguracion', {}).get('recurso', [])
                        if not isinstance(recursos_config, list): recursos_config = [recursos_config]
                        
                        for rec_conf in recursos_config:
                            id_rec = rec_conf['id']
                            cantidad_rec = int(rec_conf['valor'])
                            recurso_info = recursos_base[id_rec]
                            valor_hora_rec = float(recurso_info['valorXhora'])
                            costo_total_consumo = tiempo_consumido * cantidad_rec * valor_hora_rec
                            monto_total_cliente += costo_total_consumo
                            detalles_consumo.append({
                                                        "nit_cliente": cliente['nit'],
                                                        "instancia_id": instancia['id'], # <-- Añadir
                                                        "instancia_nombre": instancia['nombre'], # <-- Añadir
                                                        "recurso_id": id_rec,
                                                        "recurso_nombre": recurso_info['nombre'],
                                                        "categoria_nombre": categoria_usada_nombre,
                                                        "costo_total_consumo": costo_total_consumo
                                                    })  

        if monto_total_cliente > 0:
            facturas_generadas.append({"numero_factura": numero_factura_actual, "nit_cliente": cliente['nit'], "nombre_cliente": cliente['nombre'], "fecha_factura": fecha_fin_rango.strftime('%d/%m/%Y'), "monto_a_pagar": round(monto_total_cliente, 2)})
            numero_factura_actual += 1
    return {"facturas": facturas_generadas, "detalles_consumo": detalles_consumo}
