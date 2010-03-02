"""
Created on 22.09.2009

@author: alen
"""
import uuid
import logging
from oauth import oauth

from django.conf import settings
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.utils.translation import gettext as _
from django.utils.hashcompat import md5_constructor
from django.http import HttpResponseRedirect, HttpResponse

from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.sites.models import Site

from socialregistration.forms import UserForm, UserFormEmailOnly
from socialregistration.utils import (OAuthClient, OAuthTwitter, OAuthFriendFeed,
    OpenID)
from socialregistration.models import FacebookProfile, TwitterProfile, OpenIDProfile


FB_ERROR = _('We couldn\'t validate your Facebook credentials')

def _get_next(request):
    """
    Returns a url to redirect to after the login
    """
    if 'next' in request.session:
        next = request.session['next']
        del request.session['next']
        return next
    elif 'next' in request.GET:
        return request.GET.get('next')
    elif 'next' in request.POST:
        return request.POST.get('next')
    else:
        return getattr(settings, 'LOGIN_REDIRECT_URL', '/')


## Helper function, not a view!
def create_default_facebook_profile(request):
    '''
    Called by both facebook_login (if connecting through the website) and synchronise_facebook_profile (if using facebook.require_add in events_fb)
    This is the place to send emails!
    '''

    #
    # Create User
    #
    new_user = User( username = str(uuid.uuid4())[:30] )

    # basic user created, now get some information about him
    fb_profile = request.facebook.users.getInfo([request.facebook.uid], ['first_name', 'last_name', 'pic_square', 'profile_url', 'current_location', 'email'])[0]

    new_user.first_name = fb_profile['first_name']
    new_user.last_name = fb_profile['last_name']
    new_user.email = fb_profile['email']

    new_user.put()

    #
    # Create Profile
    #
    try:
        zip = int(fb_profile['current_location']['zip'])
    except:
        zip = 0
        
    try:
        current_location_city = fb_profile['current_location']['city']
        current_location_state = fb_profile['current_location']['state']
        current_location_country = fb_profile['current_location']['country']
    except:
        current_location_city = None
        current_location_state = None
        current_location_country = None

    new_profile = FacebookProfile(
        user = new_user,
        uid = str(request.facebook.uid),
        pic_square = fb_profile['pic_square'],
        profile_url = fb_profile['profile_url'],
        current_location_city = current_location_city,
        current_location_state = current_location_state,
        current_location_country = current_location_country,
        current_location_zip = zip,
        site = Site.objects.get_current(),
        )

    new_profile.put()
    
    logging.debug("Created user: %s"%new_profile.user)

    if getattr(settings, 'SOCIAL_SEND_EMAIL_ON_NEW_PROFILE', False):
        if not new_user.email:
            logging.debug("Not sending email - user hasn't specified email")
        else:
            logging.debug("Sending email to: %s" % new_user.email)
            
            try:
                from django.core.mail import send_mail
                subject = render_to_string('socialregistration/new_profile_email_subject.txt',
                                               { 'site': new_profile.site })
                # Email subject *must not* contain newlines
                subject = ''.join(subject.splitlines())

                message = render_to_string('socialregistration/new_profile_email.txt',
                                           { 'user': new_user,
                                             'profile': new_profile })

                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_user.email])

            except NotImplementedError:
                logging.error("Failed to send email to %s; subject: %s" %(new_user.email, subject))

    return new_profile


def setup(request, template='socialregistration/setup.html',
    form_class=UserFormEmailOnly, extra_context=dict()):
    """
    Setup view to create a username & set email address after authentication
    """
    profile = request.session['socialregistration_profile']

    if not getattr(settings, 'SOCIAL_GENERATE_USERNAME', False):
        # User can pick own username
        if not request.method == "POST":
            form = form_class(
                profile.user,
                profile
            )
        else:
            form = form_class(
                profile.user,
                profile,
                request.POST
            )
            if form.is_valid():
                form.save()
                user = form.profile.authenticate()
                login(request, user)
                
                del profile
                return HttpResponseRedirect(_get_next(request))
    
        extra_context.update(dict(form=form))

        return render_to_response(
            template,
            extra_context,
            context_instance=RequestContext(request)
        )
    else:
        # Authenticate and login
        user = profile.authenticate()
        login(request, user)
        
        # Clear & Redirect
        del profile
        return HttpResponseRedirect(_get_next(request))
        

def facebook_login(request, template='socialregistration/facebook.html',
    extra_context=dict(), account_inactive_template='socialregistration/account_inactive.html'):
    """
    View to handle the Facebook login 
    """
    if not request.facebook.check_session(request):
        extra_context.update(
            dict(error=FB_ERROR)
        )
        return render_to_response(
            template, extra_context, context_instance=RequestContext(request)
        )

    user = authenticate(uid=request.facebook.uid)

    if user is None:
        new_profile = create_default_facebook_profile(request)

        request.session['socialregistration_profile'] = new_profile

        request.session['next'] = _get_next(request)

        return HttpResponseRedirect(reverse('socialregistration_setup'))

    if not user.is_active:
        return render_to_response(
            account_inactive_template,
            extra_context,
            context_instance=RequestContext(request)
        )

    login(request, user)

    return HttpResponseRedirect(_get_next(request))


def facebook_connect(request, template='socialregistration/facebook.html',
    extra_context=dict()):
    """
    View to handle connecting existing accounts with facebook
    """
    if not request.facebook.check_session(request) \
        or not request.user.is_authenticated():
        extra_context.update(
            dict(error=FB_ERROR)
        )
        return render_to_response(
            template,
            extra_context,
            context_instance=RequestContext(request)
        )
    
    profile, created = FacebookProfile.objects.get_or_create(
        user=request.user, uid=request.facebook.uid
    )

    return HttpResponseRedirect(_get_next(request))


def facebook_get_ext_perm(request):

    fb = request.facebook
    if 'ext_perm' in request.GET:
        ext_perm = request.GET['ext_perm']
    else:
        ext_perm = 'email'

    redirect_url = fb.get_ext_perm_url(ext_perm=ext_perm, next=_get_next(request), popup=True)

    return fb.redirect( redirect_url )


def logout(request, redirect_url=None):
    """
    Logs the user out of django. This is only a wrapper around 
    django.contrib.auth.logout. Logging users out of Facebook for instance
    should be done like described in the developer wiki on facebook.
    http://wiki.developers.facebook.com/index.php/Connect/Authorization_Websites#Logging_Out_Users
    """
    auth_logout(request)

    url = redirect_url or getattr(settings, 'LOGOUT_REDIRECT_URL', '/') 
    
    return HttpResponseRedirect(url)

def twitter(request, account_inactive_template='socialregistration/account_inactive.html',
    extra_context=dict()):
    """
    Actually setup/login an account relating to a twitter user after the oauth 
    process is finished successfully
    """
    client = OAuthTwitter(
        request, settings.TWITTER_CONSUMER_KEY,
        settings.TWITTER_CONSUMER_SECRET_KEY,
        settings.TWITTER_REQUEST_TOKEN_URL,
    )
    
    user_info = client.get_user_info()

    user = authenticate(twitter_id=user_info['id'])
    
    if user is None:
        profile = TwitterProfile(twitter_id=user_info['id'],
                                 )
        user = User()
        request.session['socialregistration_profile'] = profile
        request.session['socialregistration_user'] = user
        request.session['next'] = _get_next(request)
        return HttpResponseRedirect(reverse('socialregistration_setup'))
    
    if not user.is_active:
        return render_to_response(
            account_inactive_template,
            extra_context,
            context_instance=RequestContext(request)
        )
    
    login(request, user)
    
    return HttpResponseRedirect(_get_next(request))

def friendfeed(request):
    """
    Actually setup an account relating to a friendfeed user after the oauth process
    is finished successfully
    """
    raise NotImplementedError()

def oauth_redirect(request, consumer_key=None, secret_key=None,
    request_token_url=None, access_token_url=None, authorization_url=None,
    callback_url=None, parameters=None):
    """
    View to handle the OAuth based authentication redirect to the service provider
    """
    request.session['next'] = _get_next(request)
    client = OAuthClient(request, consumer_key, secret_key,
        request_token_url, access_token_url, authorization_url, callback_url, parameters)
    return client.get_redirect()

def oauth_callback(request, consumer_key=None, secret_key=None,
    request_token_url=None, access_token_url=None, authorization_url=None,
    callback_url=None, template='socialregistration/oauthcallback.html',
    extra_context=dict(), parameters=None):
    """
    View to handle final steps of OAuth based authentication where the user 
    gets redirected back to from the service provider
    """
    client = OAuthClient(request, consumer_key, secret_key, request_token_url,
        access_token_url, authorization_url, callback_url, parameters)

    extra_context.update(dict(oauth_client=client))

    if not client.is_valid():
        return render_to_response(
            template, extra_context, context_instance=RequestContext(request)
        )
    
    # We're redirecting to the setup view for this oauth service
    return HttpResponseRedirect(reverse(client.callback_url))

def openid_redirect(request):
    """
    Redirect the user to the openid provider
    """
    request.session['next'] = _get_next(request)
    request.session['openid_provider'] = request.GET.get('openid_provider')
    
    client = OpenID(
        request,
        'http://%s%s' % (
            Site.objects.get_current().domain,
            reverse('openid_callback')
        ),
        request.GET.get('openid_provider')
    )
    return client.get_redirect()

def openid_callback(request, template='socialregistration/openid.html',
    extra_context=dict(), account_inactive_template='socialregistration/account_inactive.html'):
    """
    Catches the user when he's redirected back from the provider to our site
    """
    client = OpenID(
        request,
        'http://%s%s' % (
            Site.objects.get_current().domain,
            reverse('openid_callback')
        ),
        request.session.get('openid_provider')
    )
    
    if client.is_valid():
        user = authenticate(identity=request.GET.get('openid.claimed_id'))
        if user is None:
            request.session['socialregistration_user'] = User()
            request.session['socialregistration_profile'] = OpenIDProfile(
                identity=request.GET.get('openid.claimed_id')
            )
            return HttpResponseRedirect(reverse('socialregistration_setup'))
        
        if not user.is_active:
            return render_to_response(
                account_inactive_template,
                extra_context,
                context_instance=RequestContext(request)
            )
        
        login(request, user)
        return HttpResponseRedirect(_get_next(request))            
    
    return render_to_response(
        template,
        dict(),
        context_instance=RequestContext(request)
    )
