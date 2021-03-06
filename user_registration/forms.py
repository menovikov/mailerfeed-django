"""
Forms and validation code for user registration.

Note that all of these forms assume Django's bundle default ``User``
model; since it's not possible for a form to anticipate in advance the
needs of custom user models, you will need to write your own forms if
you're using a custom model.

"""
from __future__ import unicode_literals


from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserCreationForm

from .users import UserModel, UsernameField
from django.contrib.auth.models import User as User_django


User = UserModel()


class RegistrationForm1(UserCreationForm):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """
    required_css_class = 'required'
    email = forms.EmailField(label=_("E-mail"))

    class Meta:
        model = User
        fields = (UsernameField(), "first_name", "email")

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.

        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']) \
            or User_django.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(_("Этот имейл уже используется"))
            #raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
        return self.cleaned_data['email']

class RegistrationForm(forms.ModelForm):
    name = forms.CharField(label="", required=True)
    email = forms.EmailField(label="", required=True)
    phone = forms.CharField(label="", required=True)
    password = forms.CharField(
        label="", 
        widget=forms.PasswordInput,
        required=True)
    password2 = forms.CharField(
        label="", 
        widget=forms.PasswordInput,
        required=True)

    class Meta:
        model = User_django
        fields = (
            'name', 
            'email', 
            'phone',
            'password',
            'password2'
            )

    def clean_email(self):
        if User.objects.filter(email__iexact=self.cleaned_data['email']) \
            or User_django.objects.filter(email__iexact=self.cleaned_data['email']):
            #raise forms.ValidationError(_("Этот имейл уже используется"))
            raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
        return self.cleaned_data['email']

    def clean_password2(self):
        data = self.cleaned_data
        password1 = data['password']
        password2 = data['password2']
        if password1 != password2:
            raise forms.ValidationError(_("Passwords do not match"))
        return password1
        
class RegistrationFormTermsOfService(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which adds a required checkbox
    for agreeing to a site's Terms of Service.

    """
    tos = forms.BooleanField(widget=forms.CheckboxInput,
                             label=_('I have read and agree to the Terms of Service'),
                             error_messages={'required': _("You must agree to the terms to register")})


class RegistrationFormUniqueEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which enforces uniqueness of
    email addresses.

    """
    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.

        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(_("Этот имейл уже используется"))
            #raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
        return self.cleaned_data['email']


class RegistrationFormNoFreeEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which disallows registration with
    email addresses from popular free webmail services; moderately
    useful for preventing automated spam registrations.

    To change the list of banned domains, subclass this form and
    override the attribute ``bad_domains``.

    """
    bad_domains = ['aim.com', 'aol.com', 'email.com', 'gmail.com',
                   'googlemail.com', 'hotmail.com', 'hushmail.com',
                   'msn.com', 'mail.ru', 'mailinator.com', 'live.com',
                   'yahoo.com']

    def clean_email(self):
        """
        Check the supplied email address against a list of known free
        webmail domains.

        """
        email_domain = self.cleaned_data['email'].split('@')[1]
        if email_domain in self.bad_domains:
            raise forms.ValidationError(_("егистрация с использованием свободных имейлов запрещена"))
            # raise forms.ValidationError(_("Registration using free email addresses is prohibited. Please supply a different email address."))
        return self.cleaned_data['email']

class LoginForm(forms.ModelForm):
    email = forms.EmailField(label="")
    password = forms.CharField(label="", widget=forms.PasswordInput)

    class Meta:
        model = User_django
        fields = ('email', 'password')



