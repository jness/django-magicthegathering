from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'mycards.views.index'),
    url(r'^update$', 'mycards.views.update'),
    url(r'^owned$', 'mycards.views.owned'),
    url(r'^gatherer/(.*)$', 'mycards.views.gatherer_lookup'),
)

urlpatterns += staticfiles_urlpatterns()
