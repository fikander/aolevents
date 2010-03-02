# -*- coding: utf-8 -*-
import logging

import facebook.djangofb as facebook

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.views.generic.list_detail import object_detail, object_list

from ragendja.template import render_to_response
from ragendja.dbutils import get_object_or_404

from socialregistration.decorators import synchronise_facebook_profile

from events.models import Event, Favourite
from events.forms import AdvancedEventFilterForm, SimpleEventFilterForm
from events.views import view_event_show, generate_events_per_country_list

from events_fb import get_facebook_app_url

# This is not a view. It should not return anything.
def callback_on_install(request):
    logging.debug('Installed application')
    pass

@facebook.require_add(on_install=callback_on_install)
@synchronise_facebook_profile()
def callback(request):
    if (request.method == 'GET') and len(request.GET) > 0:
        search_form = AdvancedEventFilterForm(request.GET)
    else:
        search_form = AdvancedEventFilterForm(initial = {'country': 'GB', 'forwho': 'members', 'forfree' : False})

    r = RequestContext(request, { 'search_form' : search_form,
                                  'OPEN_EVENTS_MASK': Event.OPEN_EVENTS_MASK,
                                  'MEMBERS_EVENTS_MASK': Event.MEMBERS_EVENTS_MASK,
                                  'in_iframe' : True,
                                  'FACEBOOK_PROFILE_ID' : settings.FACEBOOK_PROFILE_ID,
                               })

    return render_to_response(request, 'canvas.html', r)

@facebook.require_add(on_install=callback_on_install)
@synchronise_facebook_profile()
def main(request):
    events_per_country = generate_events_per_country_list()
    events_count = Event.all().count()
    # TODO: User default country from facebook location
    search_form = SimpleEventFilterForm(initial = {'country': 'GB'})

    r = RequestContext(request, {'events_per_country': events_per_country, 
                                 'events_count' : events_count, 
                                 'search_form' : search_form, 
                                 'mainpage' : True,
                                 'in_iframe' : True,
                                 'FACEBOOK_PROFILE_ID' : settings.FACEBOOK_PROFILE_ID, })

    return render_to_response(request, 'special_events.html', r)

def add(request):
    pass

def change_settings(request):
    pass

@facebook.require_add(on_install=callback_on_install)
@synchronise_facebook_profile()
def event_show(request, key_id):
    key_id = int(key_id, 10)
    if request.user.is_authenticated():
        event = get_object_or_404(Event, id=key_id)
        fav = Favourite.all().filter('event =', event).filter('user =', request.user).get()
    else:
        fav = None

    if request.GET.has_key('invitation'):
        invitation = request.GET['invitation']
    else:
        invitation = 0
    extra_context = { 'is_fav' : fav,
                      'in_iframe' : True,
                      'invitation' : invitation,
                      'invitation_link' : get_facebook_app_url(request.path), }

    return object_detail(request, Event.all(), object_id=key_id, extra_context = extra_context)


@facebook.require_add(on_install=callback_on_install)
@synchronise_facebook_profile()
def favourite(request):
    q = request.user.favourite_set

    extra_context = {'subscription_list': request.user.subscription_set,
                     'in_iframe' : True, }

    return object_list( request, q, paginate_by=20, template_name="event_list_subscribed.html", extra_context = extra_context )


@facebook.require_add(on_install=callback_on_install)
@synchronise_facebook_profile()
def invite_friends(request):
    from cgi import escape
    
    exclude_ids = ",".join([str(a) for a in request.facebook.friends.getAppUsers()])
    
    content = """<fb:name uid="%s" firstnameonly="true" shownetwork="false"/>
       wants to invite you to use Art of Living Events,
       <fb:req-choice url="%s" label="Put Art of Livin Events on your profile!"/>
       """ % (request.facebook.uid, request.facebook.get_add_url())
    
    invitation_content = escape(content, True)
    if request.GET.has_key('next'):
        next = request.GET['next']
    else:
        next = "http://"+request.META['HTTP_HOST']+reverse('events_fb.views.callback')

    return render_to_response(request, 'invite.html',
                              {'content':invitation_content, 'exclude_ids':exclude_ids,
                               'next': escape(next), 'in_iframe' : True} )


@facebook.require_add(on_install=callback_on_install)
@synchronise_facebook_profile()
def invite_friends_for_event(request, key_id):
    from cgi import escape

    key_id = int(key_id, 10)
    event = get_object_or_404(Event, id=key_id)

    # This owuld be external link, but we want it to open inside the app.
    # event_show_url = "http://%s%s?invitation=1"%(request.META['HTTP_HOST'], event.get_facebook_url())
    event_show_url = get_facebook_app_url(event.get_facebook_url()) + '?invitation=' + str(request.facebook.uid)

    content = """<fb:name uid="%s" firstnameonly="true" shownetwork="false"/>
       wants to let you know about Art of Living event: <a href="%s">%s</a>,
       <fb:req-choice url="%s" label="Check out this event"/>
       """ % (request.facebook.uid, event_show_url, event, event_show_url)

    invitation_content = escape(content, True)
    if request.GET.has_key('next'):
        next = request.GET['next']
    else:
        next = "http://" + request.META['HTTP_HOST'] + event.get_facebook_url() + '?invitation=' + str(request.facebook.uid)

# FIXME: Why next doesnt work correctly in real life? Do I need to encode it?

    return render_to_response(request, 'invite_for_event.html',
                              {'content':invitation_content, 'event':event, 'next':escape(next), 'in_iframe' : True} )

