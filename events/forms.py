
import re

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _, ugettext as __
from django.core.files.uploadedfile import UploadedFile

from ragendja.auth.models import UserTraits
from ragendja.forms import FormWithSets, FormSetField

from registration.forms import RegistrationForm, RegistrationFormUniqueEmail
from registration.models import RegistrationProfile

from models import Event, File, RSVP, Country, Region



class FileForm(forms.ModelForm):
    name = forms.CharField(required=False, label='Name (set automatically)')

    def clean(self):
        file = self.cleaned_data.get('file')
        if not self.cleaned_data.get('name'):
            if isinstance(file, UploadedFile):
                self.cleaned_data['name'] = file.name
            else:
                del self.cleaned_data['name']
        return self.cleaned_data

    class Meta:
        model = File
        
attrs_dict = {'class': 'required input.span-3'}
 
class _EventForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(_EventForm, self).__init__(*args, **kwargs)
        self.fields['country'].widget.attrs['readonly'] = True
        self.fields['location'].widget.attrs['readonly'] = True
        self.fields['region'].widget.attrs['readonly'] = True
        if kwargs.has_key('instance'):
            # do the magic to fetch contry/region
            obj = kwargs['instance']
            try:
                self.fields['country'].initial = obj.country.key().name()
                self.fields['region'].initial = obj.region.key().name()
            except AttributeError:
                pass

    class Meta:
        model = Event
        fields = ['type', 'name', 'description', 'address', 'date_start', 'date_end', 'recurrent',
                  'location', 'fees', 'free', 'active']
        exclude = ['country', 'region']

    name = forms.CharField( label='Synopsis', max_length=150, widget = forms.TextInput(attrs={'class':'text'}))
    type = forms.ChoiceField( label='Event type', choices = Event.TYPE_CHOICE, widget = forms.Select(attrs={'class':'text'}) )
    active = forms.BooleanField( initial=True, required=False, widget = forms.CheckboxInput(),
                                 help_text='Uncheck if you don\'t want the event to be visible in search. Events are also automatically deactivated after their end date.' )

    location = forms.CharField(widget = forms.HiddenInput())

    country = forms.CharField(widget = forms.TextInput(attrs={'class': 'text readonly'}) )
    region = forms.CharField(widget = forms.TextInput(attrs={'class': 'text readonly'}), required = False)

    address = forms.CharField( label='Address', max_length=200, widget = forms.TextInput(attrs={'class':'text'}),
                               help_text='IMPORTANT: Make sure address text matches location on the map. Use \'find on map\' to find the address you\'ve typed.' )

    date_start = forms.DateTimeField( label = 'Start date and time',  widget = forms.SplitDateTimeWidget(attrs={'class': 'text veryshort'}),
                                      help_text='Date in format YYYY-MM-DD. Time in 24h format HH:MM' )
    date_end = forms.DateTimeField( label= 'End date and time', widget = forms.SplitDateTimeWidget(attrs={'class': 'text veryshort'}),
                                    help_text='Date in format YYYY-MM-DD. Time in 24h format HH:MM' )
    recurrent = forms.ChoiceField( label='Does it repeat?', choices = Event.RECURRENT_CHOICE, widget = forms.Select(attrs={'class':'text'}),
                                   help_text='Recurrent events will not be deactivated after their end date. Instead start and end dates will be updated.' )
    free = forms.BooleanField( required=False, widget = forms.CheckboxInput() )
    fees = forms.CharField( required=False, label='Fees', widget = forms.Textarea(attrs={'class': 'low'}),
                            help_text='Describe fees if event is not free. Leave empty otherwise.' )
    description = forms.CharField( required=False, label='Description', widget = forms.Textarea(attrs={'class': 'textarea'}),
                            help_text='All other information about the event. This is the place to be creative ;-). Rich text editor will come soon. In the meantime use simple HTML!' )

    files = FormSetField(File, form=FileForm, exclude='content_type')

    def save(self):
        obj = super(_EventForm, self).save()
        # check if this country exists and create if necessary
        country_raw = self.cleaned_data['country']

        # assuming 'country name [SHORT]' format of the name
        result = re.match('(.*)\[(.*)\]', country_raw)
        try:
            country_long = result.group(1).strip()
            country_short = result.group(2).strip()
        except (IndexError, AttributeError):
            country_long = ''
            country_short = country_raw

        country = Country.get_or_insert( country_short, long_name = country_long )
        obj.country = country

        # check region
        region_raw = self.cleaned_data['region']        
        
        if region_raw != '':

            result = re.match('(.*)\[(.*)\]', region_raw)
            try:
                region_long = result.group(1).strip()
                region_short = result.group(2).strip()
            except (IndexError, AttributeError):
                region_long = region_raw
                region_short = region_raw

            region = Region.get_or_insert( region_short, long_name = region_long, country=country )
            obj.region = region

        else:
            obj.region = None

        return obj


EventForm = FormWithSets(_EventForm)

class BaseEventFilterForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(BaseEventFilterForm, self).__init__(*args, **kwargs)

        q = Country.all().order('long_name')
        choices = [('all', 'All')]
        for c in q:
            choices.append( (c.key().name(), '%s [%s]'%(c.long_name, c.key().name())) )
        self.fields['country'].choices = choices
        
        q = Region.all().order('long_name')
        choices = [('all', 'All')]
        for r in q:
            choices.append( (r.key().name(), '%s'%(r.long_name)) )
        self.fields['region'].choices = choices

    country = forms.ChoiceField(widget=forms.Select(attrs=attrs_dict))
    region = forms.ChoiceField(widget=forms.Select(attrs=attrs_dict))

    #advance = forms.ChoiceField(choices=[('all', 'All'),('week','Next 7 days'),('month','Next 30 days'),('3months','Next 90 days')], widget=forms.Select(attrs=attrs_dict))

class SimpleEventFilterForm(BaseEventFilterForm):
    '''
    Visible on the main page
    '''

    def __init__(self, *args, **kwargs):
        super(SimpleEventFilterForm, self).__init__(*args, **kwargs)

    forwho   = forms.ChoiceField(label="For who",
                                 choices=[('everyone', 'I haven\'t taken Part I'),('members', 'I\'m Part I graduate!')],
                                 initial='everyone',
                                 widget = forms.RadioSelect(attrs={'class':'nobullets'}))


class AdvancedEventFilterForm(BaseEventFilterForm):
    '''
    Visible on the search page
    '''

    def __init__(self, *args, **kwargs):
        super(AdvancedEventFilterForm, self).__init__(*args, **kwargs)

    forwho   = forms.ChoiceField(label="For who",
                                 choices=[('everyone', 'I haven\'t taken Part I'),('members', 'I\'m Part I graduate!'),('custom', 'Choose event types')],
                                 initial='members',
                                 widget = forms.RadioSelect(attrs={'class':'nobullets'}),
                                 required = False)

    typelist = forms.MultipleChoiceField(label="List of types",
                                 choices=Event.TYPE_CHOICE,
                                 initial = '0',
                                 widget = forms.SelectMultiple(attrs={'style':'width:%dpx;' % (6*40-20)}),
                                 required = False)

    forfree = forms.BooleanField(label="Only free events", initial=False, widget = forms.CheckboxInput(),
                                 required = False )
    
  


#################################################################
#
# User registration
#
#################################################################


class UserRegistrationForm(forms.ModelForm):
    username = forms.RegexField(regex=r'^\w+$', max_length=30,
        label=_(u'Username'))
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(maxlength=75)),
         label=_(u'Email address'))
    password1 = forms.CharField(widget=forms.PasswordInput(render_value=False),
        label=_(u'Password'))
    password2 = forms.CharField(widget=forms.PasswordInput(render_value=False),
        label=_(u'Password (again)'))

    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        
        """
        user = User.get_by_key_name("key_"+self.cleaned_data['username'].lower())
        if user and user.is_active:
            raise forms.ValidationError(__(u'This username is already taken. Please choose another.'))
        return self.cleaned_data['username']

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(__(u'You must type the same password each time'))
        return self.cleaned_data
    
    def save(self, domain_override=""):
        """
        Create the new ``User`` and ``RegistrationProfile``, and
        returns the ``User``.
        
        This is essentially a light wrapper around
        ``RegistrationProfile.objects.create_inactive_user()``,
        feeding it the form data and a profile callback (see the
        documentation on ``create_inactive_user()`` for details) if
        supplied.
        
        """
        new_user = RegistrationProfile.objects.create_inactive_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            email=self.cleaned_data['email'],
            domain_override=domain_override,
            send_email=True)
        self.instance = new_user
        return super(UserRegistrationForm, self).save()

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.
        
        """
        email = self.cleaned_data['email'].lower()
        if User.all().filter('email =', email).filter(
                'is_active =', True).count(1):
            raise forms.ValidationError(__(u'This email address is already in use. Please supply a different email address.'))
        return email

    class Meta:
        model = User
        exclude = UserTraits.properties().keys()
