from django.contrib.sessions.backends.file import SessionStore
from mycards.models import Cards
from django.http import HttpResponse
from django.shortcuts import render

def get_working_set(request):
    if request.method == 'GET':
        try:
            working_set = request.GET['set']
        except KeyError:
            try:
                working_set = request.session['set']
            except KeyError:
                working_set = 'M12'
    else:
        try:
            working_set = request.session['set']
        except KeyError:
            working_set = 'M12'

    request.session['working_set'] = working_set
    return working_set

def sets():
    sets = Cards.objects.values_list('mtgset', flat=True).distinct()
    return sets

def index(request):
    s = get_working_set(request)
    cards = Cards.objects.filter(mtgset=s).order_by('name')
    mtgsets = sets()
    return render(request, 'index.html', {'working_set': s, 'cards': cards, 'mtgsets': mtgsets})
