from django.db import models

class Cards(models.Model):
    image = models.CharField(max_length=75)
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    damage = models.CharField(max_length=10, null=True)
    cost = models.CharField(max_length=25, null=True)
    rarity = models.CharField(max_length=25)
    color = models.CharField(max_length=2, null=True)
    mtgset = models.CharField(max_length=75)
    owned = models.IntegerField(max_length=5)
    wanted = models.IntegerField(max_length=5)

class Prices(models.Model):
    cardid = models.OneToOneField(Cards)
    name = models.CharField(max_length=50)
    mtgset = models.CharField(max_length=75)
    price_high = models.CharField(max_length=11)
    price_med = models.CharField(max_length=11)
    price_low = models.CharField(max_length=11)
