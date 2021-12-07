'''
References:
1.
Title: Model Forms
https://docs.djangoproject.com/en/3.2/topics/forms/modelforms/
'''
from django.core.validators import MaxValueValidator, MinValueValidator
from typing import List
from django import forms
from .models import Profile, Listing, Rating
class AddressForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['address']

class ListingForm(forms.Form):
    address = forms.CharField(max_length=400)
    address2 = forms.CharField(max_length=100, required=False)
    bathrooms = forms.IntegerField()
    rooms = forms.IntegerField()
    description = forms.CharField(max_length=1000)
    price=forms.DecimalField(max_digits=6, decimal_places=2)


class RatingForm(forms.Form):
    accuracy_rating = forms.IntegerField(validators=[MaxValueValidator(5), MinValueValidator(0)])
    listing_rating = forms.IntegerField(validators=[MaxValueValidator(5), MinValueValidator(0)])
    review = forms.CharField(max_length=1000)
