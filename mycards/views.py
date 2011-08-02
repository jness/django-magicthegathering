from django.contrib.sessions.backends.file import SessionStore
from django.http import HttpResponseRedirect
from mycards.models import Cards
from django.shortcuts import render

import urllib, urllib2
import re

def get_display_all(request):
    if request.method == 'GET':
        if request.GET.has_key('display'):
            display_all = request.GET['display']
        elif request.session.has_key('display'):
            display_all = request.session['display']
        else:
            display_all = 0
    else:
        if request.session.has_key('display'):
            display_all = request.session['display']
        else:
            display_all = 0

    request.session['display'] = display_all
    return display_all

def get_working_set(request):
    mtgsets = sets()
    if request.method == 'GET':
        if request.GET.has_key('set'):
            working_set = request.GET['set']
        elif request.session.has_key('set'):
            working_set = request.session['set']
        else:
            working_set = 'M12 - Magic 2012'
    else:
        if request.session.has_key('set'):
            working_set = request.session['set']
        else:
            working_set = 'M12 - Magic 2012'

    if working_set in mtgsets:
        request.session['set'] = working_set
        return working_set
    else:
        request.session['set'] = 'M12 - Magic 2012'
        return 'M12 - Magic 2012'

def sets():
    sets = Cards.objects.values_list('mtgset', flat=True).distinct()
    return sets

def gatherer_lookup(request, card):
    page = urllib2.urlopen('http://gatherer.wizards.com/Pages/Default.aspx').read()
    viewstat = re.compile('<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="(.*)"').findall(page)
    eventval = re.compile('<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="(.*)"').findall(page)

    button = 'ctl00$ctl00$MainContent$Content$SearchControls$searchSubmitButton'
    searchbox = 'ctl00$ctl00$MainContent$Content$SearchControls$CardSearchBoxParent$CardSearchBox'
    post = {button: 'Search', searchbox: card, '__VIEWSTATE': viewstat[0], '__EVENTVALIDATION': eventval[0]}

    req = urllib2.Request('http://gatherer.wizards.com/Pages/Default.aspx')
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    req.add_data(urllib.urlencode(post))
    results = urllib2.urlopen(req)
    return HttpResponseRedirect(results.geturl())

def index(request):
    # check for ordering request
    order = 'name'
    if request.method == 'GET':
        if request.GET.has_key('order_by'):
            allowed = ['name', 'type', 'rarity']
            if request.GET['order_by'] in allowed:
                order = request.GET['order_by']

    s = get_working_set(request)
    try:
        display = int(get_display_all(request))
        if display > 1:
            display = 1
    except ValueError:
        display = 0

    cards = Cards.objects.filter(mtgset=s).order_by(order).filter(owned__gte='%s' % display)
    mtgsets = sets()
    return render(request, 'index.html', {'display': display, 'working_set': s, 'cards': cards, 'mtgsets': mtgsets})

def update(request):
    # default order is by name
    order = 'name'

    # check for ordering request
    if request.method == 'GET':
        if request.GET.has_key('order_by'):
            order = request.GET['order_by']

    s = get_working_set(request)
    cards = Cards.objects.filter(mtgset=s).order_by(order)
    mtgsets = sets()
    return render(request, 'update.html', {'working_set': s, 'cards': cards, 'mtgsets': mtgsets})


def owned(request):
    s = get_working_set(request)
    # check for ordering request
    for i in request.POST:
        if i.isdigit():
            card = Cards.objects.get(id=i)
            card.owned = request.POST[i]
            card.save()
    return HttpResponseRedirect('/update')

def search(request):
    if request.method == 'GET':
        if request.GET.has_key('name'):
            search = request.GET['name']
        else:
            return index(request)

        if request.GET.has_key('search_type'):
            search_type = request.GET['search_type']
        else:
            return index(request)

    s = get_working_set(request)
    try:
        display = int(get_display_all(request))
        if display > 1:
            display = 1
    except ValueError:
        display = 0

    if search_type == 'name':
        sets_with_cards = Cards.objects.filter(name__icontains=search).values_list('mtgset', flat=True).distinct()
        cards = Cards.objects.all().filter(name__icontains=search)
    elif search_type =='type':
        sets_with_cards = Cards.objects.filter(type__icontains=search).values_list('mtgset', flat=True).distinct()
        cards = Cards.objects.all().filter(type__icontains=search)

    mtgsets = sets()
    return render(request, 'search.html', {'display': display, 'sets_with_cards': sets_with_cards, 'working_set': s, 'cards': cards, 'mtgsets': mtgsets})

