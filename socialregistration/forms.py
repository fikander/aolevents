"""
Created on 22.09.2009

@author: alen
"""
import uuid

from django import forms
from django.utils.translation import gettext as _

from django.contrib.auth.models import User

class UserForm(forms.Form):
    username = forms.RegexField(r'\w+', max_length=32)
    email = forms.EmailField(required=False)
    
    def __init__(self, user, profile, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = user
        self.profile = profile
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            # GAE implementation
            user = User.all().filter('username =', username).get()
            #user = User.objects.get(username=username)
        except:
            return username
        else:
            if user is None:
                return username
            else:
                raise forms.ValidationError(_('This username is already in use.'))
    
    def save(self):
        self.user.username = self.cleaned_data.get('username')
        self.user.email = self.cleaned_data.get('email')
        self.user.save()
        self.profile.user = self.user
        self.profile.save()        
        return self.user

class UserFormEmailOnly(forms.Form):
    email = forms.EmailField(required=False)
    
    def __init__(self, user, profile, *args, **kwargs):
        super(UserFormEmailOnly, self).__init__(*args, **kwargs)
        self.user = user
        self.profile = profile
    
    def save(self):
        self.user.email = self.cleaned_data.get('email')
        # generate username automatically
        self.user.username = str(uuid.uuid4())[:30]
        self.user.save()
        self.profile.user = self.user
        self.profile.save()        
        return self.user
