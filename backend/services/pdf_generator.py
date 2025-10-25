from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os
from .xml_manager import generar_facturacion_detallada

def generar_analisis_ventas_pdf(fecha_inicio_str, fecha_fin_str):
    """
    Genera un reporte en PDF del análisis de ventas por recurso y categoría.
    """
    resultados = generar_facturacion_detallada(fecha_inicio_str, fecha_fin_str)
    
    # ... (la lógica de agregación de datos se queda igual) ...
    ingresos_por_recurso = {}
    ingresos_por_categoria = {}
    for detalle in resultados['detalles_consumo']:
        recurso_nombre = detalle['recurso_nombre']
        costo = detalle['costo_total_consumo']
        if recurso_nombre not in ingresos_por_recurso: ingresos_por_recurso[recurso_nombre] = 0
        ingresos_por_recurso[recurso_nombre] += costo
        categoria_nombre = detalle['categoria_nombre']
        if categoria_nombre not in ingresos_por_categoria: ingresos_por_categoria[categoria_nombre] = 0
        ingresos_por_categoria[categoria_nombre] += costo
    recursos_ordenados = sorted(ingresos_por_recurso.items(), key=lambda item: item[1], reverse=True)
    categorias_ordenadas = sorted(ingresos_por_categoria.items(), key=lambda item: item[1], reverse=True)
    
    # --- Creación del Documento PDF ---
    pdf_path = os.path.join(os.path.dirname(__file__), '..', 'reporte_ventas.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Análisis de Ventas", styles['h1']))
    story.append(Paragraph(f"Período del {fecha_inicio_str} al {fecha_fin_str}", styles['h2']))
    story.append(Spacer(1, 24))

    # --- CORRECCIÓN CLAVE: Definimos el estilo de la tabla UNA SOLA VEZ ---
    estilo_tabla = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])

    # Tabla de Ingresos por Recurso
    story.append(Paragraph("Ingresos Generados por Recurso", styles['h3']))
    data_recursos = [["Recurso", "Ingreso Total"]]
    for nombre, total in recursos_ordenados:
        data_recursos.append([nombre, f"Q {total:.2f}"])
    
    table_recursos = Table(data_recursos)
    table_recursos.setStyle(estilo_tabla) # <-- Aplicamos el estilo
    story.append(table_recursos)
    story.append(Spacer(1, 24))

    # Tabla de Ingresos por Categoría
    story.append(Paragraph("Ingresos Generados por Categoría", styles['h3']))
    data_categorias = [["Categoría", "Ingreso Total"]]
    for nombre, total in categorias_ordenadas:
        data_categorias.append([nombre, f"Q {total:.2f}"])

    table_categorias = Table(data_categorias)
    table_categorias.setStyle(estilo_tabla) # <-- Reutilizamos la variable del estilo
    story.append(table_categorias)

    doc.build(story)
    return pdf_path
    
# Al final de pdf_generator.py

def generar_detalle_factura_pdf(datos_factura):
    """
    Genera un PDF con el desglose detallado de una factura específica.
    """
    # --- Extraer datos ---
    factura_info = datos_factura['factura_info']
    detalles_consumo = datos_factura['detalles_consumo']
    
    # --- Agrupar consumos por instancia ---
    costos_por_instancia = {}
    for detalle in detalles_consumo:
        instancia_id = detalle['instancia_id']
        instancia_nombre = detalle['instancia_nombre']
        
        if instancia_id not in costos_por_instancia:
            costos_por_instancia[instancia_id] = {
                'nombre': instancia_nombre,
                'recursos': [],
                'total_instancia': 0
            }
        
        costo_consumo = detalle['costo_total_consumo']
        costos_por_instancia[instancia_id]['recursos'].append({
            'nombre': detalle['recurso_nombre'],
            'costo': costo_consumo
        })
        costos_por_instancia[instancia_id]['total_instancia'] += costo_consumo

    # --- Creación del Documento PDF ---
    pdf_path = os.path.join(os.path.dirname(__file__), '..', f"factura_{factura_info['numero_factura']}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Cabecera
    story.append(Paragraph(f"Factura No. {factura_info['numero_factura']}", styles['h1']))
    story.append(Paragraph(f"Cliente: {factura_info['nombre_cliente']}", styles['h2']))
    story.append(Paragraph(f"NIT: {factura_info['nit_cliente']}", styles['Normal']))
    story.append(Paragraph(f"Fecha de Emisión: {factura_info['fecha_factura']}", styles['Normal']))
    story.append(Spacer(1, 24))

    # Detalle por instancia
    for instancia_id, data in costos_por_instancia.items():
        story.append(Paragraph(f"Detalle para Instancia: {data['nombre']} (ID: {instancia_id})", styles['h3']))
        
        tabla_data = [['Recurso Consumido', 'Aporte al Costo']]
        for recurso in data['recursos']:
            tabla_data.append([recurso['nombre'], f"Q {recurso['costo']:.2f}"])
        
        tabla_data.append(['', '']) # Espacio
        tabla_data.append(['Subtotal Instancia', f"Q {data['total_instancia']:.2f}"])

        table = Table(tabla_data, colWidths=[300, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (-1,-1), (-1,-1), 'Helvetica-Bold'), # Bold para el total
            ('GRID', (0,0), (-1,-2), 1, colors.black),
            ('GRID', (-2,-1), (-1,-1), 1, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    # Total Final
    story.append(Paragraph(f"MONTO TOTAL A PAGAR: Q {factura_info['monto_a_pagar']:.2f}", styles['h2']))
    
    doc.build(story)
    return pdf_path