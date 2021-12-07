'''
References:
1.
Title: Query Expressions
https://docs.djangoproject.com/en/3.2/ref/models/expressions/

2.
Title: QuerySets
https://docs.djangoproject.com/en/3.2/ref/models/querysets/#django.db.models.query.QuerySet

3.
Title: Django Model Relationships Make Average Ratings be and Average of Ratings number field
https://stackoverflow.com/questions/63406253/django-model-relationships-make-avg-ratings-be-an-average-of-ratings-number-fiel

4. 
Title: How ot compute average of an aggregate in Django
https://stackoverflow.com/questions/38021616/how-to-compute-average-of-an-aggregate-in-django
'''



from requests import get
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg, F
from django.contrib import admin
from datetime import date
import json
from django.core.validators import MaxValueValidator, MinValueValidator
from cloudinary.models import CloudinaryField

class MapPoints(models.Model):
    coordinates = models.CharField(max_length=200)
    title = models.CharField(max_length=200)

    def set_cords(self, coordinates):
        #check = lambda x: True if sum([i for i in x])== 2 else False
        if len(coordinates) == 2 and sum([i for i in (isinstance(x, (int, float)) for x in coordinates)]) == 2:
            self.coordinates = json.dumps(coordinates)
            return True
        else:
            return False

    def get_cords(self):
        if len(self.coordinates) != 0:
            return json.loads(self.coordinates)
        else:
            return []

    def __str__(self):
        return str({'type':'Feature','geometry':{'type':'Point','coordinates':self.get_cords()},'properties':{'title': self.title}}).replace("\'", "\"")

from django.dispatch import receiver
from django.db.models.signals import post_save

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    address = models.CharField(max_length=500)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

    def __str__(self):
        return self.address

class Listing(models.Model):
    address = models.CharField(max_length=500)
    rooms = models.IntegerField()
    bathrooms = models.IntegerField()
    price = models.DecimalField(decimal_places=2, max_digits=6, default=0)
    contact_email = models.CharField(max_length=500)
    description = models.CharField(max_length=1000)
    image = models.ImageField(upload_to='images/', null = True)

    def avg_overall_rating(self):
        avg = Rating.objects.filter(listing_id = self.id).aggregate(avg = Avg('overall_rating'))['avg']
        if avg is None:
            return None
        return round(avg, 1)

    def avg_accuracy_rating(self):
        avg = Rating.objects.filter(listing_id = self.id).aggregate(avg = Avg('accuracy_rating'))['avg']
        if avg is None:
            return None
        return round(avg, 1)

    def avg_listing_rating(self):
        avg = Rating.objects.filter(listing_id = self.id).aggregate(avg = Avg('listing_rating'))['avg']
        if avg is None:
            return None
        return round(avg ,1)

    def getPoint(self):
        base = "https://api.mapbox.com/geocoding/v5/mapbox.places/"
        token="pk.eyJ1IjoiYWNoYXJ5YTg4NDgiLCJhIjoiY2t1bHRvdjVpMHdqaDJxbWJjN2FuOGIxeiJ9.HH-8V6z7s0UPMvcKmwhd_g"

        data = get(base+str(self.address)+".json?types=address&limit=2&access_token="+token).json()
        try:
            name = data["features"][0]["place_name"].split(',')[0].replace('\'', '')
            coords = data["features"][0]["center"]
            return str({'type':'Feature','geometry':{'type':'Point','coordinates':coords},'properties':{'title': name}})
        except:
            return "INVALID"


class Rating(models.Model):
    overall_rating = models.DecimalField(decimal_places=3, max_digits=4)
    accuracy_rating = models.IntegerField(validators=[MaxValueValidator(5), MinValueValidator(0)])
    listing_rating = models.IntegerField(validators=[MaxValueValidator(5), MinValueValidator(0)])
    review = models.CharField(max_length=1000)
    listing_id = models.ForeignKey(Listing, on_delete=models.CASCADE, to_field='id')
    poster_email = models.CharField(max_length = 500)
    poster_first = models.CharField(max_length=200, null=True)
    date_posted = models.DateField(default=date.today, null=True)
