from django.urls import path
from . import views

# Aquí le decimos a Django el nombre oficial de esta aplicación de URLs
app_name = 'simulador_app'

urlpatterns = [
    path('', views.pagina_inicio, name='inicio'),
    path('consultar-datos/', views.pagina_consulta, name='consulta_datos'),
    path('generar-reporte-ventas/', views.generar_reporte_ventas, name='generar_reporte_ventas'),
    path('detalle-factura/', views.detalle_factura, name='detalle_factura'),

]