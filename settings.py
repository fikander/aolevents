# -*- coding: utf-8 -*-
from ragendja.settings_pre import *

# Increase this when you update your media on the production site, so users
# don't have to refresh their cache. By setting this your MEDIA_URL
# automatically becomes /media/MEDIA_VERSION/
MEDIA_VERSION = 2

# By hosting media on a different domain we can get a speedup (more parallel
# browser connections).
#if on_production_server or not have_appserver:
#    MEDIA_URL = 'http://media.mydomain.com/media/%d/'

# Add base media (jquery can be easily added via INSTALLED_APPS)
COMBINE_MEDIA = {
    'combined-%(LANGUAGE_CODE)s.js': (
        # See documentation why site_data can be useful:
        # http://code.google.com/p/app-engine-patch/wiki/MediaGenerator
        '.site_data.js',
    ),
    'combined-%(LANGUAGE_DIR)s.css': (
        'global/look.css',
    ),
}

# Change your email settings
if on_production_server:
    #EMAIL_HOST = 'localhost'
    #EMAIL_PORT = 25
    #EMAIL_HOST_USER = 'user'
    #EMAIL_HOST_PASSWORD = 'password'
    #EMAIL_USE_TLS = True    
    DEFAULT_FROM_EMAIL = 'art.of.living.events.app@gmail.com'
    SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'jidf@#%*$Jh4923$HNBbufEWHRew98423ywfeh2#$K#@"3hgf@#$3h3r'

#ENABLE_PROFILER = True
#ONLY_FORCED_PROFILE = True
#PROFILE_PERCENTAGE = 25
#SORT_PROFILE_RESULTS_BY = 'cumulative' # default is 'time'
# Profile only datastore calls
#PROFILE_PATTERN = 'ext.db..+\((?:get|get_by_key_name|fetch|count|put)\)'

# Enable I18N and set default language to 'en'
USE_I18N = True
LANGUAGE_CODE = 'en'

# Restrict supported languages (and JS media generation)
LANGUAGES = (
    ('de', 'German'),
    ('en', 'English'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'django.core.context_processors.debug',
)

MIDDLEWARE_CLASSES = (
    'ragendja.middleware.ErrorMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Django authentication
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Google authentication
    #'ragendja.auth.middleware.GoogleAuthenticationMiddleware',
    # Hybrid Django/Google authentication
    #'ragendja.auth.middleware.HybridAuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'ragendja.sites.dynamicsite.DynamicSiteIDMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',

    'facebook.djangofb.FacebookMiddleware',
    'socialregistration.middleware.FacebookMiddleware',
    
)

# Google authentication
#AUTH_USER_MODULE = 'ragendja.auth.google_models'
#AUTH_ADMIN_MODULE = 'ragendja.auth.google_admin'
# Hybrid Django/Google authentication
#AUTH_USER_MODULE = 'ragendja.auth.hybrid_models'

LOGIN_URL = '/account/login/'
LOGOUT_URL = '/account/logout/'
LOGIN_REDIRECT_URL = '/'

INSTALLED_APPS = (
    # Add jquery support (app is in "common" folder). This automatically
    # adds jquery to your COMBINE_MEDIA['combined-%(LANGUAGE_CODE)s.js']
    # Note: the order of your INSTALLED_APPS specifies the order in which
    # your app-specific media files get combined, so jquery should normally
    # come first.
    'jquery',

    # Add blueprint CSS (http://blueprintcss.org/)
    'blueprintcss',

    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.webdesign',
    'django.contrib.flatpages',
    'django.contrib.redirects',
    'django.contrib.sites',
    'appenginepatcher',
    'ragendja',
    'socialregistration',
    'events',
    'events_fb',
    'eventscrapper',
#    'myapp',    
    'registration',
    'mediautils',
)

# List apps which should be left out from app settings and urlsauto loading
IGNORE_APP_SETTINGS = IGNORE_APP_URLSAUTO = (
    # Example:
    # 'django.contrib.admin',
    # 'django.contrib.auth',
    # 'yetanotherapp',
#socialregistration doesnt have urlsauto
    'socialregistration'
)

# Remote access to production server (e.g., via manage.py shell --remote)
DATABASE_OPTIONS = {
    # Override remoteapi handler's path (default: '/remote_api').
    # This is a good idea, so you make it not too easy for hackers. ;)
    # Don't forget to also update your app.yaml!
    #'remote_url': '/remote-secret-url',

    # !!!Normally, the following settings should not be used!!!

    # Always use remoteapi (no need to add manage.py --remote option)
    #'use_remote': True,

    # Change appid for remote connection (by default it's the same as in
    # your app.yaml)
    #'remote_id': 'otherappid',

    # Change domain (default: <remoteid>.appspot.com)
    #'remote_host': 'bla.com',
}



GOOGLE_MAPS_API_KEY = "ABQIAAAAaWgLMjYjCd9cnfFttPaF1hQx7qQFRhdJFGxKHYMUX8NAUdfgERQb9VMepS3ZTcAYSS06rGR41rYLAQ"

if DEBUG:
    FACEBOOK_API_KEY = "ecaa57469eb41f0860897e8a487cc2d4"
    FACEBOOK_SECRET_KEY = "4c3e980f55155bdcf6e76e45a85f7e6d"
    FACEBOOK_PROFILE_ID = "333665084144"
    FACEBOOK_CANVAS_PAGE_URL = "http://apps.facebook.com/devartoflivingevents/"
    FACEBOOK_APP_NAME = 'devartoflivingevents'
else:
    FACEBOOK_API_KEY = "b9e1b3beccad3e37035c3fb3dae62c55"
    FACEBOOK_SECRET_KEY = "52bf849af0d5458a45fae749fd78ece1"
    FACEBOOK_PROFILE_ID = "302986300176"
    FACEBOOK_CANVAS_PAGE_URL = "http://apps.facebook.com/artoflivingevents/"
    FACEBOOK_APP_NAME = 'artoflivingevents'

FACEBOOK_CALLBACK_PATH = '/fb/'
FACEBOOK_INTERNAL = True

SOCIAL_GENERATE_USERNAME = True
SOCIAL_SEND_EMAIL_ON_NEW_PROFILE = True

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'socialregistration.auth.FacebookAuth',
)

AUTH_PROFILE_MODULE = 'socialregistration.FacebookProfile'

from ragendja.settings_post import *
