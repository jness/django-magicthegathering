from mycards.models import Cards
from django.http import HttpResponse
from django.shortcuts import render

def sets():
    sets = Cards.objects.values_list('mtgset', flat=True).distinct()
    return sets

def index(request):
    if request.method == 'GET':
        if request.GET.has_key('set'):
            s = request.GET['set']
        else:
            # Default to M12
            s = 'M12'
    cards = Cards.objects.filter(mtgset=s).order_by('name')
    mtgsets = sets()
    return render(request, 'index.html', {'cards': cards, 'mtgsets': mtgsets})
