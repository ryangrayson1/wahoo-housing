"""
References:
1.
Title: how to get currently logged in user's user ID in Django
https://stackoverflow.com/questions/12615154/how-to-get-the-currently-logged-in-users-user-id-in-django

2.
Title: The Messages Framework
https://docs.djangoproject.com/en/3.2/ref/contrib/messages/#django.contrib.messages.views.SuccessMessageMixin

3.
Title: Django how to delete an object directly from a button in a table
https://stackoverflow.com/questions/44248228/django-how-to-delete-a-object-directly-from-a-button-in-a-table

4. 
Title: Django file image uploads
https://www.ordinarycoders.com/blog/article/django-file-image-uploads

5.
Title: Model Forms
https://docs.djangoproject.com/en/3.2/topics/forms/modelforms/

6.
Title: How do I get the first name and last name of a logged in user in Django
https://stackoverflow.com/questions/42127684/how-do-i-get-the-first-name-and-last-name-of-a-logged-in-user-in-django

7.
title: django.urls utility functoins
https://docs.djangoproject.com/en/3.2/ref/urlresolvers/

8.
Title: Request and response objects
https://docs.djangoproject.com/en/3.2/ref/request-response/#django.http.HttpResponseNotFound

https://anymail.readthedocs.io/en/stable/esps/sendinblue/
"""

from django.shortcuts import render,  get_object_or_404
from django.contrib import messages
from django.views.generic.edit import DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
import json, traceback
#Custom models import
from housingapp.models import MapPoints
from .forms import AddressForm, ListingForm, RatingForm
from django.views import generic
from django.urls import reverse
from .models import Listing, Rating
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import  render
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.utils.safestring import mark_safe

def index(request):
    accessToken = 'pk.eyJ1IjoiYWNoYXJ5YTg4NDgiLCJhIjoiY2t1bHRvdjVpMHdqaDJxbWJjN2FuOGIxeiJ9.HH-8V6z7s0UPMvcKmwhd_g'
    listings = Listing.objects.all()
    context = {
        'accessToken': accessToken,
        'listings' : listings
    }
    points = []

    if len(listings) != 0:
        for listing in listings:
            retval = listing.getPoint().replace("\'", "\"")
            if retval != "INVALID":
                points.append(json.loads(retval))

    context['points'] = points
    return render(request, 'housingapp/index.html', context)

def signin(request):
    return render(request, 'housingapp/signin.html')

class ListingView(generic.ListView):
    model = Listing
    template_name ='housingapp/listings.html'
    context_object_name = 'listings'
    def get_queryset(self):
        return Listing.objects.all()
    #return render(request, 'housingapp/listings.html')



def FAQ(request):
    return render(request, 'housingapp/FAQ.html')

def search(request):
    if request.method == 'POST':
        print("Search request received for:",request.POST['search'])

    return render(request, 'housingapp/listings.html')

def about(request):
    return render(request, 'housingapp/about.html')

def rate_listing(request, listing_id):
    if len(Listing.objects.filter(id=listing_id)) == 0:
        return HttpResponseNotFound("Are you looking for something that doesn't exist?")
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = Rating()
            rating.accuracy_rating = form.cleaned_data['accuracy_rating']
            rating.listing_rating = form.cleaned_data['listing_rating']
            rating.review = form.cleaned_data['review']
            rating.overall_rating = (form.cleaned_data['accuracy_rating'] + form.cleaned_data['listing_rating'])/2
            rating.listing_id = Listing.objects.get(id=listing_id)
            rating.poster_email = request.user.email
            rating.poster_first = request.user.get_short_name()
            rating.save()
            return HttpResponseRedirect(reverse('housingapp:ListingID',args=[listing_id]))
        else:
            print(form.errors)
    else:
        try:
            user_already_rated = (Rating.objects.get(listing_id=listing_id, poster_email=request.user.email) is not None)
        except:
            user_already_rated = None
        form = RatingForm()
    return render(request, 'housingapp/listing_review.html', context={'form':form, 'listing_id':listing_id, 'user_already_rated': user_already_rated})

def listingID(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    ratings = Rating.objects.filter(listing_id=listing_id)
    accuracy_avg = listing.avg_accuracy_rating()
    listing_avg = listing.avg_listing_rating()
    overall_avg = listing.avg_overall_rating()
    num_ratings = len(ratings)
    try:
        user_already_rated = (Rating.objects.get(listing_id=listing_id, poster_email=request.user.email) is not None)
    except:
        user_already_rated = None
    return render(request, 'housingapp/listing_id.html', context={'listing': listing,'listing_id': listing_id, 'ratings': ratings, 'accuracy_avg': accuracy_avg,
        'listing_avg': listing_avg, 'overall_avg': overall_avg, 'num_ratings': num_ratings, 'user_already_rated': user_already_rated})

def profile(request):
    try:
        listings_from_current_user = Listing.objects.filter(contact_email=request.user.email)
    except:
        listings_from_current_user = None
    return render(request, 'housingapp/profile.html', context={'listings':listings_from_current_user})

def address_update(request):
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('housingapp:profile'))
        else:
            print("form is invalid")
    else:
        form = AddressForm()
    return render(request, 'housingapp/address_update.html', context={'form': form})

def map(request):
    return render(request, 'housingapp/map.html')

def contact(request):
    if request.method == 'POST':
        #send_mail("Subject", "text body", "from@example.com", ["to@example.com"], html_message="<html>html body</html>")
        #print(request.POST)
        try:
            to_email = request.POST["to_email"]
            context = {
                'toEmail': to_email
            }
            return render(request, 'housingapp/contact.html', context)
        except KeyError:
            try:
                message = request.POST["message"]
                print(message)
                fromEmail = request.POST["email"]
                to = request.POST["to_email2"]
                name = request.POST["name"]
                last = request.POST["surname"]
                send_mail("New Message from Wahoo Housing", message, fromEmail, [to], html_message="<html>"+ name + " " + last + " (" + fromEmail + ") Sent you a message:<br><br>" + message + "<br><br><a href = 'https://wahoo-housing.herokuapp.com'>Wahoo Housing</a></html>")
                messages.success(request, mark_safe("<h3>Message sent.</h3>"))
                s = True
            except:
                traceback.print_exc()
                messages.error(request, "Message failed to be sent." )

            accessToken = 'pk.eyJ1IjoiYWNoYXJ5YTg4NDgiLCJhIjoiY2t1bHRvdjVpMHdqaDJxbWJjN2FuOGIxeiJ9.HH-8V6z7s0UPMvcKmwhd_g'
            listings = Listing.objects.all()
            context = {
                'accessToken': accessToken,
                'listings' : listings
            }
            if s:
                return HttpResponseRedirect(reverse('housingapp:MainIndex'))
            else:
                return render(request, 'housingapp/contact.html')
    else:
        return render(request, 'housingapp/contact.html')

def add_listing(request):
    if request.method == 'POST' and request.FILES['upload']:
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = Listing()
            address_text = form.cleaned_data['address']
            extra = form.cleaned_data['address2']
            raw_address = form.cleaned_data['address'].split(',')
            if extra != "" and len(raw_address) == 4:
                address_text = raw_address[0]+", "+extra+","+raw_address[1]+","+raw_address[2]+","+raw_address[3]
            listing.address = address_text
            upload = request.FILES['upload']
            listing.image = upload
            listing.rooms = form.cleaned_data['rooms']
            listing.bathrooms = form.cleaned_data['bathrooms']
            listing.price = form.cleaned_data.get('price')
            listing.description = form.cleaned_data.get('description')
            listing.contact_email = request.user.email
            listing.save()
            return HttpResponseRedirect(reverse('housingapp:PostedListings'))
        else:
            print("Please enter valid address")
    else:
        #form = AddressForm()
        form = ListingForm()
    return render(request, 'housingapp/addlisting.html', context={'form': form})

def delete_listing(request, listing_id = None):
    if len(Listing.objects.filter(id=listing_id)) == 0:
        return HttpResponseNotFound("Are you looking for a listing that doesn't exist?")
    if len(Listing.objects.filter(id=listing_id, contact_email=request.user.email))  == 0:
        return HttpResponseNotFound("You can't delete a listing that isn't yours!")
    listing = Listing.objects.get(id = listing_id)
    listing.delete()
    return HttpResponseRedirect(reverse('housingapp:profile'))
