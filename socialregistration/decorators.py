
import logging

from django.contrib.auth import login, logout, authenticate
from socialregistration.views import create_default_facebook_profile

def synchronise_facebook_profile():
    """
    """
    def decorator(view):

        def newview(request, *args, **kwargs):
            user = request.user

            # Fast test whether we need to synchronise
            try:
                if user.is_authenticated() and (user.get_profile().uid == str(request.facebook.uid)):
                    return view(request, *args, **kwargs)
            except AttributeError:
                pass

            logout(request)

            user = authenticate(uid=request.facebook.uid)
            if not user:
                profile = create_default_facebook_profile(request)
                user = profile.authenticate()
                logging.debug('Created profile and user obejcts for FB user: %s'%request.facebook.uid)
            else:
                logging.debug('Profile and user for FB user %s already exist. Logging in user: %s'%(request.facebook.uid, user))

            assert(user)        

            login(request, user)

            return view(request, *args, **kwargs)

        return newview

    return decorator
