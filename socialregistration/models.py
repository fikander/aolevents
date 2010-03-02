"""
Created on 22.09.2009

@author: alen
"""

#from django.db import models
from google.appengine.ext import db

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.sites.models import Site 

class FacebookProfile(db.Model):

#    user = models.ForeignKey(User)
#    site = models.ForeignKey(Site, default=Site.objects.get_current)
#    uid = models.CharField(max_length=255, blank=False, null=False)
    user = db.ReferenceProperty(User)
    site = db.ReferenceProperty(Site)
    uid = db.StringProperty()
    pic_square = db.StringProperty()
    profile_url = db.StringProperty()
    current_location_city = db.StringProperty()
    current_location_state = db.StringProperty()
    current_location_country = db.StringProperty()
    current_location_zip = db.IntegerProperty()

    def __unicode__(self):
        return '%s: %s' % (self.user, self.uid)
    
    def authenticate(self):
        return authenticate(uid=self.uid)

class TwitterProfile(db.Model):
#    user = models.ForeignKey(User)
#    site = models.ForeignKey(Site, default=Site.objects.get_current)
#    twitter_id = models.PositiveIntegerField()
    user = db.ReferenceProperty(User)
    site = db.ReferenceProperty(Site, default=Site.objects.get_current)
    twitter_id = db.IntegerProperty()

    def __unicode__(self):
        return '%s: %s' % (self.user, self.twitter_id)
    
    def authenticate(self):
        return authenticate(twitter_id=self.twitter_id)

class FriendFeedProfile(db.Model):
#    user = models.ForeignKey(User)
#    site = models.ForeignKey(Site, default=Site.objects.get_current)
    user = db.ReferenceProperty(User)
    site = db.ReferenceProperty(Site, default=Site.objects.get_current)

class OpenIDProfile(db.Model):
#    user = models.ForeignKey(User)
#    site = models.ForeignKey(Site, default=Site.objects.get_current)
#    identity = models.TextField()
    user = db.ReferenceProperty(User)
    site = db.ReferenceProperty(Site, default=Site.objects.get_current)
    identity = db.StringProperty()
    
    def authenticate(self):
        return authenticate(identity=self.identity)

class OpenIDStore(db.Model):
#    site = models.ForeignKey(Site, default=Site.objects.get_current)
#    server_url = models.CharField(max_length=255)
#    handle = models.CharField(max_length=255)
#    secret = models.TextField()
#    issued = models.IntegerField()
#    lifetime = models.IntegerField()
#    assoc_type = models.TextField()
    site = db.ReferenceProperty(Site, default=Site.objects.get_current)
    server_url = db.StringProperty()
    handle = db.StringProperty()
    secret = db.TextProperty()
    issued = db.IntegerProperty()
    lifetime = db.IntegerProperty()
    assoc_type = db.TextProperty()

class OpenIDNonce(db.Model):
#    server_url = models.CharField(max_length=255)
#    timestamp = models.IntegerField()
#    salt = models.CharField(max_length=255)
#    date_created = models.DateTimeField(auto_now_add=True)
    server_url = db.StringProperty()
    timestamp = db.IntegerProperty()
    salt = db.StringProperty()
    date_created = db.DateTimeProperty(auto_now_add=True)

