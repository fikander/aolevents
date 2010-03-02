# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext as _
from ragendja.template import render_to_response

from scrapper import UKScrapper

def view_eventscrapper_scrap(request):
    scrapper = UKScrapper()
    log = scrapper.run("http://artoflivinglondon.org/courses_inyourarea.htm")
    return HttpResponse(log)

    