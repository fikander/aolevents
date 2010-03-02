

def get_facebook_app_url(absolute_url):
    ''' Strip leading callback url and prefix with canvas url, so the link opens in facebook app '''
    
    from django.conf import settings

    #from django.core.urlresolvers import reverse
    #callback_url = reverse('events_fb.views.callback')    

    callback_url = settings.FACEBOOK_CALLBACK_PATH
    assert(absolute_url.startswith(callback_url))

    return settings.FACEBOOK_CANVAS_PAGE_URL + absolute_url[len(callback_url):]