from django.conf.urls.defaults import *

urlpatterns = patterns('events.views',
    (r'^$',                     'view_event_list', {'subscription_id': None} ),
    (r'^subscription/(?P<subscription_id>\d+)$', 'view_event_list' ),
    (r'^add/$',                 'view_event_add'),
    (r'^show/(?P<key_id>\d+)/$',   'view_event_show'),
    (r'^edit/(?P<key_id>\d+)/$',     'view_event_edit'),
    (r'^delete/(?P<key_id>\d+)/$',   'view_event_delete'),
    (r'^toggle/(?P<key_id>\d+)/$',   'view_event_toggle'),
    (r'^mine/$',                'view_event_mine'),
    (r'^subscribed/$',          'view_event_subscribed'),
    (r'^stats/$',               'view_event_stats'),
    (r'^nonmoderated/$',                'view_event_nonmoderated'),
    (r'^moderate_toggle/$',   'view_event_moderate_toggle'),

    (r'^download/(?P<key>.+)/(?P<name>.+)$', 'download_file'),

    # service
    # GET parameters
    #    format = [xml|csv|JSON]
    (r'^serialise/_featured/(?P<featured_priority>[0-9]+)/$', 'view_events_serialise_featured'),

    (r'^serialise/_regions/(?P<country>[a-zA-Z0-9_ ]+)/$', 'view_regions_serialise'),

    (r'^serialise/(?P<country>[a-zA-Z0-9_ ]+)/(?P<region>[a-zA-Z0-9_ ]+)/$', 'view_events_serialise'),

    # favourite and RSVP
    (r'^favourite/toggle/$', 'view_favourite_toggle'),
    # subscriptions
    (r'^subscribe/$', 'view_subscribe'),
    (r'^delete_subscription/(?P<key_id>\d+)/$', 'view_delete_subscription'),

)
