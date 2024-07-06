# import csv
# from django.http import HttpResponse
# from django.shortcuts import render
# from binance.client import Client
# from binance.exceptions import BinanceAPIException
# from .models import DjangoNinjas, BalanceData

# def index(request):
#     data = None
#     error = None
    

#     acc_data = DjangoNinjas.objects.all()

#     if request.method == 'POST':
#         ClientName = request.POST.get('client_name')
#         AccountName = request.POST.get('account_name')
#         wallet = request.POST.get('wallet')
        

#         for i in acc_data:
#             if ClientName == 'DjangoNinjas' and i.account_name == AccountName:
#                 api_key = i.api_key
#                 secret_key = i.secret_key

#                 client = Client(api_key, secret_key)

#                 try:
#                     account_info = client.get_account()
#                     balances = account_info['balances']
                    

#                     for balance in balances:
#                         asset = balance['asset']
#                         free = balance['free']
#                         locked = balance['locked']

#                         # Create or update DjangoNinjasBalance entry
#                         ninja_balance, created = BalanceData.objects.update_or_create(
#                             client=i,
#                             asset=asset,
#                             defaults={'free': free, 'locked': locked, 'wallet': wallet}
#                         )
                        

#                     data = balances
#                     print(data)

#                 except BinanceAPIException as e:
#                     error = str(e)

#     return render(request, 'binance_app/index.html', {'data': data, 'error': error, 'form_value': True})

# def download_balances(request):
#     # Query the balance data
#     balances = BalanceData.objects.all()

#     # Create the HttpResponse object with the appropriate CSV header.
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = 'attachment; filename="balances.csv"'

#     writer = csv.writer(response)
#     writer.writerow(['Asset', 'Free', 'Locked', 'Wallet'])

#     for balance in balances:
#         writer.writerow([balance.asset, balance.free, balance.locked, balance.wallet])

#     return response



import csv
import logging
from django.http import HttpResponse
from django.shortcuts import render
from binance.client import Client
from binance.exceptions import BinanceAPIException
from django.db import connection
import time
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def get_binance_symbols(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, account_name, api_key, secret_key FROM client_account_data")
        acc_data = cursor.fetchall()
    for account in acc_data:
        api_key = account[2]
        secret_key = account[3]
    try:
        client = Client(api_key=api_key, api_secret=secret_key)
        exchange_info = client.get_exchange_info()
        symbols = [symbol['symbol'] for symbol in exchange_info['symbols']]
        return JsonResponse({'symbols': symbols})
    except BinanceAPIException as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def index(request):
    data = None
    error = None
    context = {'show_download': False}

    with connection.cursor() as cursor:
        cursor.execute("SELECT id, account_name, api_key, secret_key FROM client_account_data")
        acc_data = cursor.fetchall()

    if request.method == 'POST':
        ClientName = request.POST.get('client_name')
        AccountName = request.POST.get('account_name')
        endpoint = request.POST.get('endpoint')  
        symbol = request.POST.get('symbol')      

        if not (ClientName and AccountName):
            error = "All fields are required."
        else:
            for account in acc_data:
                if ClientName == 'DjangoNinjas' and account[1] == AccountName:
                    api_key = account[2]
                    secret_key = account[3]
                    client = Client(api_key, secret_key)

                    try:
                        res = client.get_server_time()
                        client.timestamp_offset = res['serverTime'] - int(time.time()*1000)

                        if endpoint in ['spot', 'funding']:
                            if endpoint == 'spot':
                                account_info = client.get_account()
    
                                balances = account_info['balances']

                                with connection.cursor() as cursor:
                                    for balance in balances:
                                        asset = balance['asset']
                                        free = balance['free']
                                        locked = balance['locked']

                                        cursor.execute(
                                            """
                                            INSERT INTO spot_data (client_id, asset, free, locked)
                                            VALUES (%s, %s, %s, %s)
                                            ON DUPLICATE KEY UPDATE
                                                free = VALUES(free),
                                                locked = VALUES(locked)
                                            """,
                                            (account[0], asset, free, locked)
                                        )

                                data = balances
                                logger.info(f"Spot Balances for {AccountName} updated successfully.")

                            elif endpoint == 'funding':
                                account_info = client.funding_wallet()
                                balances = account_info

                                with connection.cursor() as cursor:
                                    for balance in balances:
                                        asset = balance['asset']
                                        free = balance['free']
                                        locked = balance['locked']

                                        cursor.execute(
                                            """
                                            INSERT INTO funding_data (client_id, asset, free, locked)
                                            VALUES (%s, %s, %s, %s)
                                            ON DUPLICATE KEY UPDATE
                                                free = VALUES(free),
                                                locked = VALUES(locked)
                                            """,
                                            (account[0], asset, free, locked)
                                        )

                                data = balances
                                logger.info(f"Funding Balances for {AccountName} updated successfully.")

                            context = {'data': data, 'error': error, 'show_download': True, 'form_value': True}

                        elif endpoint == "recent_trades":
                            recent_trades = client.get_recent_trades(symbol = symbol)

                            with connection.cursor() as cursor:
                                for trade in recent_trades:
                                    cursor.execute(
                                        """
                                        INSERT INTO recent_trades_data (client_id, trade_id, symbol, price, quantity, quote_qty, isBuyerMaker, isBestMaker)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                        """,
                                        (account[0], trade['id'], symbol, trade['price'], trade['qty'], trade['quoteQty'], trade['isBuyerMaker'], trade['isBestMatch'])
                                    )
                            data = recent_trades
                            logger.info(f"Recent Trades for {symbol} updated successfully.")

                            context = {'data': data, 'error': error, 'show_download': True, 'form_value': True}

                    except BinanceAPIException as e:
                        error = str(e)
                        logger.error(f"Binance API Exception: {error}")

    return render(request, 'binance_app/index.html', context)

@csrf_exempt
def download_balances(request):
    if request.method == 'POST':
        account_name = request.POST.get('account_name')
        endpoint = request.POST.get('endpoint')

        balances = None

        if endpoint in ['spot', 'funding']:
            if endpoint == 'spot':
                with connection.cursor() as cursor:
                    cursor.execute("SELECT client_id, asset, free, locked FROM spot_data")
                    balances = cursor.fetchall()
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="spot_data.csv"'

            elif endpoint == 'funding':
                with connection.cursor() as cursor:
                    cursor.execute("SELECT client_id, asset, free, locked FROM funding_data")
                    balances = cursor.fetchall()
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="funding_data.csv"'

            writer = csv.writer(response)
            writer.writerow(['client_id','Asset', 'Free', 'Locked'])

            for balance in balances:
                writer.writerow(balance)

        if endpoint == 'recent_trades':
            with connection.cursor() as cursor:
                cursor.execute("SELECT client_id, trade_id, symbol, price, quantity, quote_qty, isBuyerMaker, isBestMaker from recent_trades_data")
                trades_data = cursor.fetchall()
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="recent_trades_data.csv"'

            writer = csv.writer(response)
            writer.writerow(['client_id', 'trade_id', 'symbol', 'price', 'quantity', 'quote_qty', 'isBuyerMaker', 'isBestMaker'])

            for trades in trades_data:
                writer.writerow(trades)

    return response
