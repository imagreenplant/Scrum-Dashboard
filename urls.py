from django.conf.urls.defaults import *
from django.conf import settings
from django.views.decorators.cache import cache_page
from dash.views import status,root,iteration, member_iteration, backlogs, planning, tags, tag, team_root, backlog

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Team Root Pages
    (r'^$', root),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Team Root Pages
    (r'^team/([^/]+)/$', team_root),
    
    #Summary pages
    (r'^team/([^/]+)/backlogs/$', backlogs),
    (r'^product/([^/]+)/tags/$', tags),
    
    #Backlog
    (r'^backlog/([^/]+)/$', backlog),
    
    #Project summary
    (r'^team/([^/]+)/planning/$', planning),
    
    #Tag for project
    (r'^product/([^/]+)/tag/([^/]+)/$', tag),

    #The dashboard pages for members and iterations, also a catch-all
    (r'^product/([^/]+)/([^/]+)/([^/]+)/$', member_iteration),
    (r'^product/([^/]+)/([^/]+)/$',iteration),

)
