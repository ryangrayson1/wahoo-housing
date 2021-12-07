from django.contrib import admin

# Register your models here.

from .models import Profile, Listing

class ProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        ('user', {'fields': ['user']}),
        ('address', {'fields': ['address']}),
    ]

    list_display = ('user', 'address')
    list_filter = ['user']

class ListingAdmin(admin.ModelAdmin):
    fieldsets = [
        ('address', {'fields': ['address']}),
        ('rooms', {'fields': ['rooms']}),
        ('bathrooms', {'fields': ['bathrooms']}),
        ('price', {'fields': ['price']}),
        ('contact email', {'fields': ['contact_email']}),
        ('description', {'fields': ['description']}),
    ]

    list_display = ('address', 'rooms', 'bathrooms', 'price', 'contact_email', 'description')
    list_filter = ['address']
    search_fields = ['address', 'description', 'contact_email']


admin.site.register(Profile, ProfileAdmin)

admin.site.register(Listing, ListingAdmin)
