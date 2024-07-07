from django.contrib import admin
from binance_app.models import DjangoNinjas

class DjangoNinjas_Client(admin.ModelAdmin):
    list_display = ('account_name', 'api_key', 'secret_key')

admin.site.register(DjangoNinjas, DjangoNinjas_Client)