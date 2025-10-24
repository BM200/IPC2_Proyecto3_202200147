import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'data.xml')

def inicializar_xml_si_no_existe():
    if not os.path.exists(DB_FILE):
        root = ET.Element('archivoConfiguraciones')
        ET.SubElement(root, 'listaRecurcursos')
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
    return {
        "recursos_cargados": len(recursos),
        "categorias_cargadas": len(categorias),
        "clientes_cargados": len(clientes),
        "total_instancias_registradas": len(total_instancias)
    }

def procesar_consumos_xml(consumos_xml_string):
    tree_db = ET.parse(DB_FILE)
    root_db = tree_db.getroot()
    root_consumos = ET.fromstring(consumos_xml_string)
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
    return {
        "consumos_procesados_exitosamente": consumos_procesados,
        "errores_encontrados": errores
    }

def agregar_recurso(recurso_data):
    inicializar_xml_si_no_existe()
    tree = ET.parse(DB_FILE)
    root = tree.getroot()
    lista_recursos_node = root.find('listaRecursos')
    nuevo_id = len(lista_recursos_node.findall('recurso')) + 1
    nuevo_recurso_node = ET.SubElement(lista_recursos_node, 'recurso', id=str(nuevo_id))
    ET.SubElement(nuevo_recurso_node, 'nombre').text = recurso_data.get('nombre')
    ET.SubElement(nuevo_recurso_node, 'abreviatura').text = recurso_data.get('abreviatura')
    ET.SubElement(nuevo_recurso_node, 'metrica').text = recurso_data.get('metrica')
    ET.SubElement(nuevo_recurso_node, 'tipo').text = recurso_data.get('tipo')
    ET.SubElement(nuevo_recurso_node, 'valorXhora').text = str(recurso_data.get('valorXhora'))
    tree.write(DB_FILE, encoding='utf-8', xml_declaration=True)
    recurso_data['id'] = nuevo_id
    return recurso_data

def convertir_elemento_a_dict(elemento):
    dict_resultado = {}
    dict_resultado.update(elemento.attrib)
    for hijo in elemento:
        valor_hijo = convertir_elemento_a_dict(hijo)
        if hijo.tag in dict_resultado:
            if type(dict_resultado[hijo.tag]) is not list:
                dict_resultado[hijo.tag] = [dict_resultado[hijo.tag]]
            dict_resultado[hijo.tag].append(valor_hijo)
        else:
            dict_resultado[hijo.tag] = valor_hijo
    texto = elemento.text.strip() if elemento.text else None
    if not dict_resultado and texto:
        return texto
    if texto and 'valor' not in dict_resultado:
        dict_resultado['valor'] = texto
    return dict_resultado

def obtener_datos_completos():
    if not os.path.exists(DB_FILE):
        raise FileNotFoundError("El archivo data.xml no existe.")
    tree = ET.parse(DB_FILE)
    root = tree.getroot()
    return {root.tag: convertir_elemento_a_dict(root)}

def extraer_fecha(texto_fecha):
    """
    Usa una expresión regular para encontrar y convertir una fecha en formato
    dd/mm/yyyy hh:mi o dd/mm/yyyy de un string.
    Devuelve un objeto datetime si la encuentra, o None si no.
    """
    # El patrón busca 'dd/mm/yyyy hh:mi' o 'dd/mm/yyyy'
    patron = r'(\d{2}/\d{2}/\d{4})'
    coincidencia = re.search(patron, texto_fecha)
    
    if coincidencia:
        fecha_str = coincidencia.group(1)
        # Intentamos convertir la fecha a un objeto datetime
        return datetime.strptime(fecha_str, '%d/%m/%Y')
    return None

def generar_facturacion(fecha_inicio_str, fecha_fin_str):
    """
    Calcula la facturación para todos los clientes en un rango de fechas.
    """
    # 1. Convertir las fechas de entrada a objetos datetime
    fecha_inicio_rango = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
    fecha_fin_rango = datetime.strptime(fecha_fin_str, '%Y-%m-%d')

    # 2. Cargar todos los datos del sistema
    datos = obtener_datos_completos()['archivoConfiguraciones']
    recursos_base = {r['id']: r for r in datos['listaRecursos']['recurso']}
    clientes = datos['listaClientes']['cliente']
    # Asegurarnos de que clientes sea una lista
    if not isinstance(clientes, list):
        clientes = [clientes]

    facturas_generadas = []
    numero_factura_actual = int(datetime.now().timestamp()) # Generador simple de ID único

    # 3. Iterar sobre cada cliente para calcular su factura
    for cliente in clientes:
        monto_total_cliente = 0.0
        
        instancias = cliente.get('listaInstancias', {}).get('instancia', [])
        if not isinstance(instancias, list):
            instancias = [instancias]

        for instancia in instancias:
            consumos = instancia.get('listaConsumos', {}).get('consumoRegistrado', [])
            if not isinstance(consumos, list):
                consumos = [consumos]

            for consumo in consumos:
                fecha_consumo = extraer_fecha(consumo['fechaHora'])
                if fecha_consumo and fecha_inicio_rango <= fecha_consumo <= fecha_fin_rango:
                    # --- ¡El consumo está en el rango! Procedemos a calcular el costo ---
                    tiempo_consumido = float(consumo['tiempo'])
                    id_config = instancia['idConfiguracion']
                    
                    # Buscar la configuración de esta instancia
                    config_usada = None
                    for cat in datos['listaCategorias']['categoria']:
                        confs = cat['listaConfiguraciones']['configuracion']
                        if not isinstance(confs, list): confs = [confs]
                        for conf in confs:
                            if conf['id'] == id_config:
                                config_usada = conf
                                break
                        if config_usada: break
                    
                    # Calcular el costo de esta instancia para este consumo
                    if config_usada:
                        costo_instancia_consumo = 0.0
                        recursos_config = config_usada['recursosConfiguracion']['recurso']
                        if not isinstance(recursos_config, list): recursos_config = [recursos_config]
                        
                        for rec_conf in recursos_config:
                            id_rec = rec_conf['id']
                            cantidad_rec = int(rec_conf['valor'])
                            valor_hora_rec = float(recursos_base[id_rec]['valorXhora'])
                            costo_instancia_consumo += cantidad_rec * valor_hora_rec
                        
                        monto_total_cliente += tiempo_consumido * costo_instancia_consumo

        # 4. Si el cliente tuvo consumo, se genera la factura
        if monto_total_cliente > 0:
            facturas_generadas.append({
                "numero_factura": numero_factura_actual,
                "nit_cliente": cliente['nit'],
                "nombre_cliente": cliente['nombre'],
                "fecha_factura": fecha_fin_rango.strftime('%d/%m/%Y'),
                "monto_a_pagar": round(monto_total_cliente, 2)
            })
            numero_factura_actual += 1

    return facturas_generadas