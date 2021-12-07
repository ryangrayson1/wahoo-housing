from django.urls import path, include
from . import views
from .views import index, signin, ListingView, FAQ, search, about, profile, address_update, add_listing, delete_listing, listingID, contact, rate_listing
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static 
app_name = 'housingapp'
urlpatterns = [
    path('', index, name='MainIndex'),
    #path('accounts/', include('allauth.urls')),
    path('signin/', signin, name='account_signin'),
    path('listings/', ListingView.as_view(), name='PostedListings'),
    path('listings/<int:listing_id>', listingID, name='ListingID'),
    path('rate_listing/<int:listing_id>', rate_listing, name='RateListing'),
    path('FAQ/', FAQ, name='FrequentlyAskedQuestions'),
    path('search/', search, name='Search'),
    path('about/', about, name='About'),
    path('address-update/', address_update, name='AddressUpdate'),
    path('profile/', profile, name='profile'),
    path('add-listing/', add_listing, name='AddListing'),
    path('contact/', contact, name='Contact'),
    path('delete-listing/<int:listing_id>', delete_listing, name='delete_listing')
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
