import xml.etree.ElementTree as ET
import os

# Nombre del archivo que funcionará como nuestra base de datos
DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'data.xml')

def inicializar_xml_si_no_existe():
    """Verifica si el archivo XML existe. Si no, crea la estructura base."""
    if not os.path.exists(DB_FILE):
        root = ET.Element('archivoConfiguraciones')
        ET.SubElement(root, 'listaRecursos')
        ET.SubElement(root, 'listaCategorias')
        ET.SubElement(root, 'listaClientes')
        
        tree = ET.ElementTree(root)
        tree.write(DB_FILE, encoding='utf-8', xml_declaration=True)
        print(f"Archivo '{os.path.basename(DB_FILE)}' no encontrado. Creando estructura inicial.")

def procesar_y_guardar_config_xml(xml_string):
    """
    Parsea un string XML, lo guarda en el archivo data.xml y devuelve un resumen.
    Esta función SOBRESCRIBE el contenido anterior de data.xml.
    """
    root = ET.fromstring(xml_string)
    tree = ET.ElementTree(root)
    tree.write(DB_FILE, encoding='utf-8', xml_declaration=True)

    recursos = root.findall('listaRecursos/recurso')
    categorias = root.findall('listaCategorias/categoria')
    clientes = root.findall('listaClientes/cliente')
    total_instancias = root.findall('.//instancia')

    summary = {
        "recursos_cargados": len(recursos),
        "categorias_cargadas": len(categorias),
        "clientes_cargados": len(clientes),
        "total_instancias_registradas": len(total_instancias)
    }
    return summary

def procesar_consumos_xml(consumos_xml_string):
    """
    Lee un XML de consumos, encuentra la instancia correspondiente en data.xml
    y le añade la información del consumo.
    """
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
            errores.append(f"Cliente con NIT '{nit}' no encontrado. Se omitió el consumo.")
            continue

        instancia_target = cliente_target.find(f".//instancia[@id='{id_instancia}']")
        if instancia_target is None:
            errores.append(f"Instancia con ID '{id_instancia}' para el cliente NIT '{nit}' no encontrada. Se omitió el consumo.")
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
    """
    Agrega un nuevo elemento <recurso> al archivo data.xml.
    """
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