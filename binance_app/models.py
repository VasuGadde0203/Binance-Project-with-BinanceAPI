from django.db import models

class DjangoNinjas(models.Model):
    account_name = models.CharField(max_length=50)
    api_key = models.CharField(max_length=100)
    secret_key = models.CharField(max_length=100)

    def __str__(self):
        return self.account_name

class BalanceData(models.Model):
    client = models.ForeignKey(DjangoNinjas, on_delete=models.CASCADE)
    asset = models.CharField(max_length=50)
    free = models.DecimalField(max_digits=20, decimal_places=5)
    locked = models.DecimalField(max_digits=20, decimal_places=5)
    wallet = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = 'BalancesData'

    def __str__(self):
        return f'{self.client.account_name} - Asset: {self.asset}, Free: {self.free}, Locked: {self.locked}, Wallet: {self.wallet}'
