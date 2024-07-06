from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('download_balances/', views.download_balances, name='download_balances'),
    path('get_binance_symbols/', views.get_binance_symbols, name='get_binance_symbols')
]
