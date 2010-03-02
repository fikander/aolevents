
import string

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Message
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, HttpResponseNotFound, HttpResponseRedirect
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, \
    update_object, redirect, get_model_and_form_class, apply_extra_context
from django.utils.translation import ugettext    
from django.template import RequestContext, loader
from django.shortcuts import render_to_response
from google.appengine.ext import db
from mimetypes import guess_type

from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response as ragendja_render_to_response

from models import Event, Country, Region, File, Favourite, RSVP, Subscription
from forms import EventForm, SimpleEventFilterForm, AdvancedEventFilterForm

#pyfacebook
#from django.utils.decorators import decorator_from_middleware
#from facebook.djangofb import FacebookMiddleware


def prepare_for_csv(s):
    ''' helper function'''
    return s.strip().replace(',', ' ').replace('\n', ' ')




#@decorator_from_middleware(FacebookMiddleware)
def view_events_main(request):
    events_per_country = generate_events_per_country_list()
    events_count = Event.all().count()
    search_form = SimpleEventFilterForm(initial = {'country': 'GB'})

    r = RequestContext(request, {'events_per_country': events_per_country, 
                                 'events_count' : events_count, 
                                 'search_form' : search_form, 
                                 'mainpage' : True })
    return render_to_response('homepage.html', r)



def view_event_show(request, key_id):
    key_id = int(key_id, 10)
    if request.user.is_authenticated():
        event = get_object_or_404(Event, id=key_id)
        fav = Favourite.all().filter('event =', event).filter('user =', request.user).get()
    else:
        fav = None
#    from django.template import RequestContext
#    c = RequestContext(request)
    
    extra_context = { 'is_fav' : fav  }
    return object_detail(request, Event.all(), object_id=key_id, extra_context = extra_context)



def view_event_list(request, subscription_id = None):
    search_form = None
    if (request.method == 'GET') and len(request.GET) > 0:
        search_form = AdvancedEventFilterForm(request.GET)
    elif subscription_id:
        if isinstance(subscription_id, int):
            s = Subscription.get_by_id(subscription_id)
        else:
            s = Subscription.get_by_id( int(subscription_id, 10) )
        if s:
            if s.country:
                country_id = s.country.key().name()
            else:
                country_id = None

            if s.region:
                region_id = s.region.key().name()
            else:
                region_id = None

            typelist = []
            # See if subscription is generalised, so that we can use forwho = everyone or members
            if s.event_types == Event.OPEN_EVENTS_MASK:
                forwho = 'everyone'
            elif s.event_types == Event.MEMBERS_EVENTS_MASK:
                forwho = 'members'
            else:
                forwho = 'custom'

                # convert bit mask into list of numbers
                bit = 1
                counter = 0
                typelist = []
                while bit < Event.MEMBERS_EVENTS_MASK:
                    if bit & s.event_types:
                        typelist.append(counter)
                    counter += 1
                    bit = bit << 1

            search_form = AdvancedEventFilterForm(initial = {
                                                             'country': country_id,
                                                             'region': region_id,
                                                             'forwho': forwho,
                                                             'forfree': s.free,
                                                             'typelist': typelist })

    if not search_form:
        search_form = AdvancedEventFilterForm(initial = {'country': 'GB', 'forwho': 'members', 'forfree' : False})

    subscription_list = None
    if request.user.is_authenticated():
        subscription_list = request.user.subscription_set

    r = RequestContext(request, { 'search_form' : search_form,
                                  'OPEN_EVENTS_MASK': Event.OPEN_EVENTS_MASK,
                                  'MEMBERS_EVENTS_MASK': Event.MEMBERS_EVENTS_MASK,
                                  'subscription_list': subscription_list,
                               })

    return render_to_response('event_list.html', r)


def my_create_object(request, model=None, template_name=None, 
        template_loader=loader, extra_context=None, post_save_redirect=None, 
        login_required=False, context_processors=None, form_class=None):
    """
    Generic object-creation function.

    Templates: ``<app_label>/<model_name>_form.html``
    Context:
        form
            the form for the object
    """
    model, form_class = get_model_and_form_class(model, form_class)
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            new_object = form.save()
            new_object.creator = request.user
            new_object.save()
            if request.user.is_authenticated():
                Message(user=request.user, message=ugettext("The %(verbose_name)s was created successfully.") % {"verbose_name": model._meta.verbose_name}).put()
            return redirect(post_save_redirect, new_object)
    else:
        form = form_class()

    # Create the template, context, response
    if not template_name:
        template_name = "%s/%s_form.html" % (model._meta.app_label, model._meta.object_name.lower())
    t = template_loader.get_template(template_name)
    c = RequestContext(request, {
        'form': form, 
    }, context_processors)
    return HttpResponse(t.render(c))

@login_required
def view_event_add(request):
    return my_create_object(request, form_class=EventForm)

@login_required
def view_event_mine(request):
    if request.user.is_superuser:
        q = Event.all()
    else:
        q = request.user.event_set

    return object_list(request, q, paginate_by=20, template_name="event_list_mine.html")

@login_required
def view_event_subscribed(request):
    q = request.user.favourite_set

    extra_context = {'subscription_list': request.user.subscription_set }

    return object_list( request, q, paginate_by=20, template_name="event_list_subscribed.html", extra_context = extra_context )


@login_required
def view_event_stats(request):
    return HttpResponse('not implemented')

@login_required
def view_event_edit(request, key_id):
    return update_object(request, object_id=int(key_id, 10), form_class=EventForm)

@login_required
def view_event_delete(request, key_id):
    return delete_object(request, Event, object_id=int(key_id, 10), 
        post_delete_redirect=reverse('events.views.view_event_mine'))

@login_required
def view_event_toggle(request, key_id):
    event = get_object_or_404(Event, id=int(key_id, 10))
    if event:
        event.active = not event.active
        event.put()
    return view_event_mine(request)

@login_required
def view_event_nonmoderated(request):
    if not request.user.is_superuser:
        raise Http404('You have to be administrator to access this page')
    q = Event.all().filter('moderated =', False)
    return object_list(request, q, paginate_by=20, template_name="event_list_moderate.html")

@login_required
def view_event_moderate_toggle(request):
    '''
    hybrid AJAX
    '''
    # result in case of ajax query
    result = 0

    if request.method == 'POST':
        key_id = request.POST.get('key_id', None)
    elif request.method == 'GET':
        key_id = request.GET.get('key_id', None)
    else:
        key_id = None

    if key_id:
        event = Event.get_by_id( int(key_id, 10) )
        if not event:
            return HttpResponseNotFound()

        event.moderated = not event.moderated
        event.put()

        result = int(event.moderated)

    if not request.is_ajax():
        next = request.GET.get('next', None)
        if not next:
            next = reverse('view_event_nonmoderated')

        return HttpResponseRedirect(next)
    else:
        return HttpResponse(result)



def download_file(request, key, name):
    file = get_object_or_404(File, key)
    if file.name != name:
        raise Http404('Could not find file with this name!')
    return HttpResponse(file.file, 
        content_type=guess_type(file.name)[0] or 'application/octet-stream')


# TODO: cache this list rather than generting it on every request!
def generate_events_per_country_list():
    result=[]
    for c in Country.all():
        result.append([c.key().name(), c.long_name, c.event_set.count()])
    return result


def serialise_events_for_query(query, user = None, facebook = False, provide_favourite_state = False, provide_rsvp_state = False):
    ''' only shows active events!
    '''

    contents = ''

    query.filter('active =', True)
    query.filter('moderated =', True)

    for e in query:
        if e.name and e.location and e.type:
            if facebook is True:
                absolute_url = e.get_facebook_url()
            else:
                absolute_url = e.get_absolute_url()

            contents_list = [
                             '[' + e.country.key().name() + '] ' + prepare_for_csv(e.name),
                             e.type,
                             # numeric value out of type string
                             str( e.fields()['type'].make_value_from_form(e.type) ),
                             # sorting needs nice arranged format...
                             e.date_start.strftime('%Y-%m-%d (%a) at %H:%M%Z'),
                             e.date_end.strftime('%Y-%m-%d (%a) at %H:%M%Z'),
                             #e.date_end.strftime('%a %d %b %Y at %H:%M%Z'),
                             #e.date_end.isoformat(' '), 
                             e.recurrent, 
                             e.location.__str__(), 
                             absolute_url,
                             str(e.key().id()),
                             str(e.featured_priority),
                             str(int(e.free)),
                             ]

            if provide_favourite_state:
                if user and user.is_authenticated():
                    is_fav = (Favourite.all().filter('event =', e).filter('user =', user).get() != None)
                else:
                    is_fav = False
                contents_list.append( str(int(is_fav)) )

            if provide_rsvp_state:
                rsvp_state = RSVP.UNKNOWN
                if user and user.is_authenticated():
                    rsvp = RSVP.all().filter('event =', e).filter('user =', user).get()
                    if rsvp:
                        rsvp_state = rsvp.state
                contents_list.append(str(rsvp_state))

            contents += string.join(contents_list, ',')
            contents += '\n'

    return contents

def view_events_serialise_featured(request, featured_priority):

    if request.method == 'GET':
        if request.GET.has_key('format') and request.GET['format'] == 'csv':

            q = Event.all().filter('featured_priority >=', int(featured_priority)).order('-featured_priority')

            in_iframe = request.GET.has_key('in_iframe')
            return HttpResponse(serialise_events_for_query(q, request.user, in_iframe, True, True))

    return HttpResponseNotFound()

            
def view_events_serialise(request, country, region):
    '''
    AJAX
    return list of events for given country and region
    if user is registered, than provide information about favorite and RSVP state
    '''

    if request.method == 'GET':
        if request.GET.has_key('format') and request.GET['format'] == 'csv':

            r = None
            c = None

            if country != u'all':
                c = Country.get_by_key_name(country.strip())
                if c is None:
                    return HttpResponse('')

                if region != u'all':
                    r = Region.get_by_key_name(region.strip())
                    if r is None:
                        return HttpResponse('')

            # if r defined, then c has to be defined as well
            assert(not r or (r and c))
            q = Event.all()
            if c:
                q.filter('country =', c)
            if r:
                q.filter('region =', r)

            in_iframe = request.GET.has_key('in_iframe')
            return HttpResponse(serialise_events_for_query(q, request.user, in_iframe, True, True))

    return HttpResponseNotFound()


def view_regions_serialise(request, country):
    
    if request.method == 'GET':
        if request.GET.has_key('format') and request.GET['format'] == 'csv':
            contents = '';
            c = Country.get_by_key_name(country)
            if c is not None:

                for r in Country.get_by_key_name(country).region_set:
                    contents_list = [
                                     r.key().name(), 
                                     r.long_name
                                     ]
                    contents += string.join(contents_list, ',')
                    contents += '\n'

            return HttpResponse(contents)

    return HttpResponseNotFound()

#------------------------------------
def view_favourite_toggle(request):
    '''AJAX'''

    # login is required here
    if not ( request.user and request.user.is_authenticated() ):
        return HttpResponseNotFound()

    result = '0'

    if request.method == 'POST':
        key_id = request.POST.get('key_id', None)
        if key_id:
            event = Event.get_by_id( int(key_id, 10) )
            if not event:
                return HttpResponseNotFound()

            #check this favourite exists and toggle it
            fav = Favourite.all().filter('event =', event).filter('user =', request.user).get()
            if fav:
                fav.delete()
            else:
                f = Favourite(user = request.user, event = event)
                f.put()
                result = '1'

    return HttpResponse(result)
#------------------------------------

@login_required
def view_subscribe(request):

    # login is required here
    #if not ( request.user and request.user.is_authenticated() ):
    #    return HttpResponseRedirect()
    
    if request.user.subscription_set.count() >= Subscription._MAX_SUBSCRIPTIONS_PER_USER:
        Message(user = request.user, message = ugettext('You\'ve reached maximum number of subscriptions. Delete some and try again.')).put()
    elif request.method == 'GET':
        search_form = AdvancedEventFilterForm(request.GET)

        if search_form.is_valid():

            country = Country.get_by_key_name( search_form.cleaned_data['country'] )
            region = Region.get_by_key_name( search_form.cleaned_data['region'] )
            free = search_form.cleaned_data['forfree']

            if search_form.cleaned_data['forwho'] == 'custom':
                event_types = 0
                for t in search_form.cleaned_data['typelist']:
                    event_types += 1 << int(t)
            elif search_form.cleaned_data['forwho'] == 'everyone':
                event_types = Event.OPEN_EVENTS_MASK
            else:
                #assert(search_form.cleaned_data['forwho'] == 'members')
                event_types = Event.MEMBERS_EVENTS_MASK

            s = Subscription(user = request.user, country = country, region = region, event_types = event_types, free = free)
            s.put()

            Message(user = request.user, message = ugettext('Subscription created')).put()

            return HttpResponseRedirect( reverse('events.views.view_event_list', kwargs={'subscription_id': s.key().id()}) )

    return HttpResponseRedirect( reverse('events.views.view_event_list') )

@login_required
def view_delete_subscription(request, key_id):
    s = Subscription.get_by_id( int(key_id, 10) )
    if (s and (s.user == request.user or request.user.is_superuser) ):
        s.delete()
    return HttpResponseRedirect( reverse('events.views.view_event_subscribed') )


#------------------------------------

def create_admin_user(request):
    user = User.get_by_key_name('admin')
    if not user or user.username != 'admin' or not (user.is_active and
            user.is_staff and user.is_superuser and
            user.check_password('admin')):
        user = User(key_name='admin', username='admin', 
            email='admin@localhost', first_name='Boss', last_name='Admin', 
            is_active=True, is_staff=True, is_superuser=True)
        user.set_password('WsduhQODFNNCuweg3862geFGHoshi')
        user.put()
    return ragendja_render_to_response(request, 'events/admin_created.html')

