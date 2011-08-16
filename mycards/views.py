from django.contrib.sessions.backends.file import SessionStore
from django.http import HttpResponseRedirect
from django.conf import settings

from mycards.models import Cards
from django.shortcuts import render

from recaptcha.client import captcha
import smtplib
from socket import error
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
            allowed = ['name', 'type', 'rarity', 'owned', 'price']
            if request.GET['order_by'] in allowed:
                if request.GET['order_by'] == 'price':
                    order = 'prices__price_med'
                else:
                    order = request.GET['order_by']

    # check for color request
    colors = False
    if request.method == 'GET':
        if request.GET.has_key('color'):
            allowed = ['U', 'B', 'W', 'R', 'G', 'NULL']
            if request.GET['color'] in allowed:
                colors = request.GET['color']

    s = get_working_set(request)
    try:
        display = int(get_display_all(request))
        if display > 1:
            display = 1
    except ValueError:
        display = 0

    if colors:
        if colors == 'NULL':
            cards = Cards.objects.filter(mtgset=s).order_by(order).filter(owned__gte='%s' % display).filter(color__isnull=True)
        else:
            cards = Cards.objects.filter(mtgset=s).order_by(order).filter(owned__gte='%s' % display).filter(color=colors)
    else:
        cards = Cards.objects.filter(mtgset=s).order_by(order).filter(owned__gte='%s' % display)
    mtgsets = sets()
    return render(request, 'index.html', {'colors': colors, 'order': order, 'display': display, 'working_set': s, 'cards': cards, 'mtgsets': mtgsets})

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

def contact(request):

    # if we didnt add our reCaptcha keys contact form is disabled
    if not settings.RECAPTCHA_PRIVATE_KEY:
        return HttpResponseRedirect('/')

    captcha_response = ''
    message = ''
    name = ''

    if request.method == 'POST':
        if request.POST.has_key('message'):
            message = request.POST.get('message')
        if request.POST.has_key('name'):
            name = request.POST.get('name')
        response = captcha.submit(
            request.POST.get('recaptcha_challenge_field'),
            request.POST.get('recaptcha_response_field'),
            settings.RECAPTCHA_PRIVATE_KEY,
            request.META['REMOTE_ADDR'],)

        if name and message:
            if response.is_valid:
                from django.http import HttpResponse
                captcha_response = 'Message Sent'
                header = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n"
                        % (name, settings.EMAILTO, '[mtg.flip-edesign.com] Contact'))
                msg = header + message
                server = smtplib.SMTP(settings.HOST)
                server.set_debuglevel(0)
                server.sendmail(name, settings.EMAILTO, msg)
                server.quit()
            else:
                from django.http import HttpResponse
                captcha_response = 'You typed in the Captcha wrong'
        else:
            captcha_response = 'Please fill in your name and message'

    return render(request, 'contact.html', {'name': name, 'message': message, 'captcha_response': captcha_response, 'key': settings.RECAPTCHA_PUBLIC_KEY})


