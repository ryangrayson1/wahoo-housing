"""housingapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
#Allauth views import

#Importing the index view from views
from housingapp.views import index, signin, FAQ, search, about
from django.conf import settings #add this
from django.conf.urls.static import static #add this
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

urlpatterns = [
    path('ricehall/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('housingapp.urls')),
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('/images/favicon.ico')))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)