from django.conf.urls.defaults import *

urlpatterns = patterns('',

    (r'^$',                 'events_fb.views.callback'),
    (r'^main/$',            'events_fb.views.main'),

    (r'^add/$',                      'events_fb.views.add'),
    (r'^settings/$',                 'events_fb.views.change_settings'),

    (r'^show/(?P<key_id>\d+)/$',     'events_fb.views.event_show'),
    (r'^favourite/$',     'events_fb.views.favourite'),

    (r'^invite/$',                   'events_fb.views.invite_friends'),
    (r'^invite_for_event/(?P<key_id>\d+)/$',   'events_fb.views.invite_friends_for_event'),

)
