from django.urls import path
from . import views
#aqui se llama a la pagina de inicio de views.py
urlpatterns = [
    path('', views.pagina_inicio, name='inicio'),
]