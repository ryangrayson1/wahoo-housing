'''References 
1.
Title: How to write Django Test Meant To Fail 
URL: https://stackoverflow.com/questions/4218161/how-to-write-django-test-meant-to-fail

2. Django Project Documentation on Testing
URL: https://docs.djangoproject.com/en/3.2/topics/testing/overview/

3.
Title: How should I write tests for Forms in Django
URL: https://stackoverflow.com/questions/7304248/how-should-i-write-tests-for-forms-in-django

4.
Title: How to return 404 page intentionally in Django
https://stackoverflow.com/questions/49465281/how-to-return-404-page-intentionally-in-django

5.
Title: Unittest.mock -mock object library
https://docs.python.org/3/library/unittest.mock.html
'''

# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase

# Create your tests here.

class DummyTestCase(TestCase):
    def setUp(self):
        x = 1
        y = 2

    def test_dummy_test_case(self):
        self.assertEqual(1, 1)


#Allauth tests
from importlib import import_module
from requests.exceptions import HTTPError

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test.client import RequestFactory
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse

from allauth.account import app_settings as account_settings
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount, SocialToken
from allauth.socialaccount.tests import OAuth2TestsMixin
from allauth.tests import MockedResponse, TestCase, patch

from allauth.account.models import EmailAddress
from allauth.socialaccount.app_settings import QUERY_EMAIL
from allauth.socialaccount.providers.base import AuthAction, ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider

from django.contrib.auth.decorators import login_required


class Scope(object):
    EMAIL = "email"
    PROFILE = "profile"


class GoogleAccount(ProviderAccount):
    def get_profile_url(self):
        return self.account.extra_data.get("link")

    def get_avatar_url(self):
        return self.account.extra_data.get("picture")

    def to_str(self):
        dflt = super(GoogleAccount, self).to_str()
        return self.account.extra_data.get("name", dflt)


class GoogleProvider(OAuth2Provider):
    id = "google"
    name = "Google"
    account_class = GoogleAccount

    def get_default_scope(self):
        scope = [Scope.PROFILE]
        if QUERY_EMAIL:
            scope.append(Scope.EMAIL)
        return scope

    def get_auth_params(self, request, action):
        ret = super(GoogleProvider, self).get_auth_params(request, action)
        if action == AuthAction.REAUTHENTICATE:
            ret["prompt"] = "select_account consent"
        return ret

    def extract_uid(self, data):
        return str(data["id"])

    def extract_common_fields(self, data):
        return dict(
            email=data.get("email"),
            last_name=data.get("family_name"),
            first_name=data.get("given_name"),
        )

    def extract_email_addresses(self, data):
        ret = []
        email = data.get("email")
        if email and data.get("verified_email"):
            ret.append(EmailAddress(email=email, verified=True, primary=True))
        return ret


provider_classes = [GoogleProvider]


@override_settings(
    SOCIALACCOUNT_AUTO_SIGNUP=True,
    ACCOUNT_SIGNUP_FORM_CLASS=None,
    ACCOUNT_EMAIL_VERIFICATION=account_settings.EmailVerificationMethod.MANDATORY,
)
class GoogleTests(OAuth2TestsMixin, TestCase):
    provider_id = GoogleProvider.id

    def get_mocked_response(
        self,
        family_name="Penners",
        given_name="Raymond",
        name="Raymond Penners",
        email="raymond.penners@example.com",
        verified_email=True,
    ):
        return MockedResponse(
            200,
            """
              {"family_name": "%s", "name": "%s",
               "picture": "https://lh5.googleusercontent.com/photo.jpg",
               "locale": "nl", "gender": "male",
               "email": "%s",
               "link": "https://plus.google.com/108204268033311374519",
               "given_name": "%s", "id": "108204268033311374519",
               "verified_email": %s }
        """
            % (
                family_name,
                name,
                email,
                given_name,
                (repr(verified_email).lower()),
            ),
        )

    def test_google_compelete_login_401(self):
        from allauth.socialaccount.providers.google.views import (
            GoogleOAuth2Adapter,
        )

        class LessMockedResponse(MockedResponse):
            def raise_for_status(self):
                if self.status_code != 200:
                    raise HTTPError(None)

        request = RequestFactory().get(
            reverse(self.provider.id + "_login"), dict(process="login")
        )

        adapter = GoogleOAuth2Adapter(request)
        app = adapter.get_provider().get_app(request)
        token = SocialToken(token="some_token")
        response_with_401 = LessMockedResponse(
            401,
            """
            {"error": {
              "errors": [{
                "domain": "global",
                "reason": "authError",
                "message": "Invalid Credentials",
                "locationType": "header",
                "location": "Authorization" } ],
              "code": 401,
              "message": "Invalid Credentials" }
            }""",
        )
        with patch(
            "allauth.socialaccount.providers.google.views" ".requests"
        ) as patched_requests:
            patched_requests.get.return_value = response_with_401
            with self.assertRaises(HTTPError):
                adapter.complete_login(request, app, token)

    def test_username_based_on_email(self):
        first_name = "明"
        last_name = "小"
        email = "raymond.penners@example.com"
        self.login(
            self.get_mocked_response(
                name=first_name + " " + last_name,
                email=email,
                given_name=first_name,
                family_name=last_name,
                verified_email=True,
            )
        )
        user = User.objects.get(email=email)
        self.assertEqual(user.username, "raymond.penners")

    def test_email_verified(self):
        test_email = "raymond.penners@example.com"
        self.login(self.get_mocked_response(verified_email=True))
        email_address = EmailAddress.objects.get(email=test_email, verified=True)
        self.assertFalse(
            EmailConfirmation.objects.filter(email_address__email=test_email).exists()
        )
        account = email_address.user.socialaccount_set.all()[0]
        self.assertEqual(account.extra_data["given_name"], "Raymond")

    def test_user_signed_up_signal(self):
        sent_signals = []

        def on_signed_up(sender, request, user, **kwargs):
            sociallogin = kwargs["sociallogin"]
            self.assertEqual(sociallogin.account.provider, GoogleProvider.id)
            self.assertEqual(sociallogin.account.user, user)
            sent_signals.append(sender)

        user_signed_up.connect(on_signed_up)
        self.login(self.get_mocked_response(verified_email=True))
        self.assertTrue(len(sent_signals) > 0)

    @override_settings(ACCOUNT_EMAIL_CONFIRMATION_HMAC=False)
    def test_email_unverified(self):
        test_email = "raymond.penners@example.com"
        resp = self.login(self.get_mocked_response(verified_email=False))
        email_address = EmailAddress.objects.get(email=test_email)
        self.assertFalse(email_address.verified)
        self.assertTrue(
            EmailConfirmation.objects.filter(email_address__email=test_email).exists()
        )
        self.assertTemplateUsed(
            resp, "account/email/email_confirmation_signup_subject.txt"
        )

    def test_email_verified_stashed(self):
        # http://slacy.com/blog/2012/01/how-to-set-session-variables-in-django-unit-tests/
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
        request = RequestFactory().get("/")
        request.session = self.client.session
        adapter = get_adapter(request)
        test_email = "raymond.penners@example.com"
        adapter.stash_verified_email(request, test_email)
        request.session.save()

        self.login(self.get_mocked_response(verified_email=False))
        email_address = EmailAddress.objects.get(email=test_email)
        self.assertTrue(email_address.verified)
        self.assertFalse(
            EmailConfirmation.objects.filter(email_address__email=test_email).exists()
        )

    def test_account_connect(self):
        email = "user@example.com"
        user = User.objects.create(username="user", is_active=True, email=email)
        user.set_password("test")
        user.save()
        EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
        self.client.login(username=user.username, password="test")
        self.login(self.get_mocked_response(verified_email=True), process="connect")
        # Check if we connected...
        self.assertTrue(
            SocialAccount.objects.filter(user=user, provider=GoogleProvider.id).exists()
        )
        # For now, we do not pick up any new e-mail addresses on connect
        self.assertEqual(EmailAddress.objects.filter(user=user).count(), 1)
        self.assertEqual(EmailAddress.objects.filter(user=user, email=email).count(), 1)

        ## test if Profile model was auto-created upon connecting
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)

    @override_settings(
        ACCOUNT_EMAIL_VERIFICATION=account_settings.EmailVerificationMethod.MANDATORY,
        SOCIALACCOUNT_EMAIL_VERIFICATION=account_settings.EmailVerificationMethod.NONE,
    )
    def test_social_email_verification_skipped(self):
        test_email = "raymond.penners@example.com"
        self.login(self.get_mocked_response(verified_email=False))
        email_address = EmailAddress.objects.get(email=test_email)
        self.assertFalse(email_address.verified)
        self.assertFalse(
            EmailConfirmation.objects.filter(email_address__email=test_email).exists()
        )

    @override_settings(
        ACCOUNT_EMAIL_VERIFICATION=account_settings.EmailVerificationMethod.OPTIONAL,
        SOCIALACCOUNT_EMAIL_VERIFICATION=account_settings.EmailVerificationMethod.OPTIONAL,
    )
    def test_social_email_verification_optional(self):
        self.login(self.get_mocked_response(verified_email=False))
        self.assertEqual(len(mail.outbox), 1)
        self.login(self.get_mocked_response(verified_email=False))
        self.assertEqual(len(mail.outbox), 1)
@override_settings(
    SOCIALACCOUNT_PROVIDERS={
        "google": {
            "APP": {
                "client_id": "app123id",
                "key": "google",
                "secret": "dummy",
            }
        }
    }
)
class AppInSettingsTests(GoogleTests):
    """
    Run the same set of tests but without having a SocialApp entry.
    """

    pass

#Map points test
from housingapp.models import MapPoints

class MapPointsTests(TestCase):
    def test_str_response_equivalence(self):
        point = MapPoints(title="Test1")
        point.set_cords([10.00,10.00])
        pointStr = str(point)
        self.assertEqual('{"type": "Feature", "geometry": {"type": "Point", "coordinates": [10.0, 10.0]}, "properties": {"title": "Test1"}}', pointStr)

    def test_str_response_empty(self):
        point = MapPoints()
        pointStr = str(point)
        self.assertEqual('{"type": "Feature", "geometry": {"type": "Point", "coordinates": []}, "properties": {"title": ""}}', pointStr)

    def test_str_response_emptyCoords(self):
        point = MapPoints(title="Test3")
        pointStr = str(point)
        self.assertEqual('{"type": "Feature", "geometry": {"type": "Point", "coordinates": []}, "properties": {"title": "Test3"}}', pointStr)

    def test_str_response_emptyTitle(self):
        point = MapPoints()
        point.set_cords([10.00,10.00])
        pointStr = str(point)
        self.assertEqual('{"type": "Feature", "geometry": {"type": "Point", "coordinates": [10.0, 10.0]}, "properties": {"title": ""}}', pointStr)

    def test_wrong_coords(self):
        point = MapPoints()
        self.assertFalse(point.set_cords(["a", "b"]))

    def test_int_float_coords(self):
        point = MapPoints()
        self.assertTrue(point.set_cords([10.00,10]))

from .models import Listing, Rating, Profile

class RatingModelTest(TestCase):
    def test_rating_correct_inputs(self):
        listing = create_listing(1)
        listing.save()
        rating = Rating(listing_id = listing, overall_rating = 5, accuracy_rating = 4, listing_rating = 5, review = "good", poster_email="test@sample.com", poster_first="Test")
        rating.save()
        self.assertEqual(rating.overall_rating, 5)
        self.assertAlmostEqual(listing.avg_overall_rating(), 5.0)
        self.assertAlmostEqual(listing.avg_accuracy_rating(), 4.0)
        self.assertAlmostEqual(listing.avg_overall_rating(), 5.0)
    
    def test_rating_too_high(self):
        listing = create_listing(1)
        listing.save()
        rating = Rating(listing_id = listing, overall_rating = 6, accuracy_rating= 4, listing_rating = 3, review = "good", poster_email="test@sample.com", poster_first="Test")
        try:
            rating.save()
            self.fail("Did not throw exception to a rating too high")
        except:
            pass

    # testing multiple ratings to make sure both listing and rating models work
    def test_multiple_ratings_regression(self):
        listing = create_listing(1)
        listing.save()
        rating1 = Rating(listing_id = listing, overall_rating=5, accuracy_rating=5, listing_rating=5, review="good", poster_email="test@sample.com", poster_first= "test")
        rating2 = Rating(listing_id = listing, overall_rating=4, accuracy_rating=4, listing_rating=2, review="good", poster_email="test@sample.com", poster_first= "test")
        rating3 = Rating(listing_id = listing, overall_rating=1, accuracy_rating=3, listing_rating=5, review="good", poster_email="test@sample.com", poster_first= "test")
        rating1.save()
        rating2.save()
        rating3.save()
        self.assertAlmostEqual(float(listing.avg_accuracy_rating()), round((5 + 4 + 3)/3, 1))
        self.assertAlmostEqual(float(listing.avg_overall_rating()), round((5 + 4 + 1)/3, 1))
        self.assertAlmostEqual(float(listing.avg_listing_rating()), round((5 + 2 + 5)/3,1))





# helper function for tests
def create_listing(listing_id):
    listing = Listing(address = str(listing_id) + "test address", rooms = listing_id, bathrooms = listing_id, price = 1000, 
    contact_email= "test" + str(listing_id) + "@email.com", description = "test description no. " + str(listing_id))
    return listing

class ListingModelTest(TestCase):
    def test_listing_correct_inputs(self):
        listing = Listing()
        listing.address = "1234 test drive"
        listing.rooms = 1
        listing.bathrooms = 1
        listing.price = 1000
        listing.contact_email = "test@test.com"
        listing.description = "test description"
        listing.save()
        self.assertEqual(listing.address, "1234 test drive")
        self.assertEqual(listing.rooms, 1)
        self.assertEqual(listing.price, 1000)
        ## some basic integration testing since rating functions should return none
        self.assertIsNone(listing.avg_accuracy_rating())
        self.assertIsNone(listing.avg_listing_rating())
        self.assertIsNone(listing.avg_overall_rating())

    def test_listing_incorrect_input(self):
        listing = Listing()
        try:
            listing.rooms = "wrong input"
            self.fail("Did not throw expected exception")
        except:
            pass
        try:
            listing.address = 1
            self.fail("Did not throw excepted exception")
        except:
            pass
    
    def test_more_than_1_lising(self):
        listing = Listing(address="1234 test", rooms = 1, bathrooms = 1, price = 1000, contact_email = "test2@email.com", description = "test description")
        listing2 = Listing(address="12345 test", rooms = 2, bathrooms = 3, price = 1053, contact_email = "test2@email.com", description = "test description")
        listing.save()
        listing2.save()
        self.assertEqual(len(Listing.objects.all()), 2)

## additional views testing
class RatingViewTest(TestCase):
    # test should return 200 if accessing a rating page for a listing that exists
    def test_rating_view(self):
        c = Client()
        listing = create_listing(1)
        listing.save()
        response = c.get(reverse('housingapp:RateListing', kwargs={'listing_id': listing.id}))
        self.assertEqual(response.status_code, 200)
    
    # expect 404 error if accessing rating page for invalid listing id
    def test_invalid_rating_view(self):
        c = Client()
        response = c.get(reverse('housingapp:RateListing', kwargs={'listing_id': 1000}))
        self.assertEqual(response.status_code, 404)

class DeleteViewTest(TestCase):
    # should not be able to delete a listing that isn't the users, 404 error 
    
    def test_delete_listing_is_not_requesters(self):
        self.user = User.objects.create_user(username = 'test', password = 'test')
        login = self.client.login(username='test', password='test')
        listing = create_listing(1)
        listing.save()
        num_listings =len(Listing.objects.filter(id=listing.id)) # listings before getting delete URL
        response = self.client.get(reverse('housingapp:delete_listing', kwargs={'listing_id': listing.id}), {'request.user.email':'wrong_email@test.com'})
        self.assertEqual(response.status_code, 404)
        # make sure no listings were deleted
        self.assertEqual(num_listings,len(Listing.objects.filter(id=listing.id)) )

    # should be able to delete a listing that is the users, 302 redirect is expected
    def test_delete_listing_is_requesters(self):
        self.user = User.objects.create_user(username = 'test', password = 'test',email='test1@email.com')
        login = self.client.login(username='test', password='test', email='test1@email.com')
        listing = create_listing(1)
        listing.save()
        #print(Listing.objects.filter(id=listing.id, contact_email=self.user.email))
        response = self.client.get(reverse('housingapp:delete_listing', kwargs={'listing_id': listing.id}), {'request.user.email':'test1@email.com'})
        #print(response.content)
        self.assertEqual(response.status_code, 302)
        # check if the listing was deleted
        self.assertEqual(len(Listing.objects.filter(id=listing.id, contact_email=self.user.email)), 0)

from .forms import ListingForm, RatingForm

class ListingFormTest(TestCase):
    def test_listing_form(self):
        form_data = {'address':'123 test drive', 'bathrooms':1, 'rooms': 1, 'description':'test description', 'price':'1000'}
        form = ListingForm(data = form_data)
        self.assertTrue(form.is_valid())
    
    def test_listing_form_empty_field(self):
        form_data = {'address':'123 test drive', 'rooms': 1, 'description':'test description', 'price':'1000'}
        form = ListingForm(data = form_data)
        self.assertFalse(form.is_valid())
    def test_listing_form_incorrect_field(self):
        form_data = {'address':'123 test drive', 'rooms': 1, 'description':'test description', 'price':'1000000'}
        form = ListingForm(data = form_data)
        self.assertFalse(form.is_valid())

class RatingFormTest(TestCase):
    def test_rating_form(self):
        form_data = {'accuracy_rating':5, 'listing_rating': 3, 'review':'test review'}  
        form = RatingForm(data = form_data)
        self.assertTrue(form.is_valid())

    def test_rating_form_decimal(self):
        form_data = {'accuracy_rating':3.48, 'listing_rating': 3, 'review':'test review'}  
        form = RatingForm(data = form_data)
        self.assertFalse(form.is_valid())

    def test_rating_form_toohigh(self):
        form_data = {'accuracy_rating':6, 'listing_rating': 3, 'review':'test review'}  
        form = RatingForm(data = form_data)
        self.assertFalse(form.is_valid())