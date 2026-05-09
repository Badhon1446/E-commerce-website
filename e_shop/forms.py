from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from . models import User,Rating,Order


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    class Meta:
        model = User
        fields = [ 'username','first_name','last_name', 'email', 'password1', 'password2' ]

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'comment']
        widgets = {
            'rating' : forms.Select(choices=[(i,i) for i in range(1,6)]),
            'comment': forms.Textarea(attrs={'rows':4})
        }

class CheckOutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name','email','address','postal_code','city','note']
        widgets = {
            'note': forms.Textarea(attrs={'rows':3})
        }
        
# from django import forms
# from django.contrib.auth.models import User

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }