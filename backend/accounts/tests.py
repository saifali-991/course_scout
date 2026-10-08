"""Tests for the Google-only auth flow:

* POST /api/auth/google/  — real Google verification is mocked (no network),
  everything downstream (user creation, dedupe, token issue) is exercised.
* GET  /api/auth/me/  and  POST /api/auth/logout/  — token lifecycle.
"""
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .views import username_from_email

User = get_user_model()
GOOGLE_CLIENT_ID = 'test-client.apps.googleusercontent.com'


def fake_payload(**overrides):
    payload = {
        'iss': 'https://accounts.google.com',
        'aud': GOOGLE_CLIENT_ID,
        'sub': '118273645001',
        'email': 'raj.kumar@gmail.com',
        'email_verified': True,
        'name': 'Raj Kumar',
    }
    payload.update(overrides)
    return payload


@override_settings(GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID)
class GoogleLoginTests(APITestCase):
    url = '/api/auth/google/'

    @mock.patch('accounts.views.google_id_token.verify_oauth2_token')
    def test_first_login_creates_user_and_returns_token(self, verify):
        verify.return_value = fake_payload()
        res = self.client.post(self.url, {'credential': 'fake-jwt'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertIn('token', res.data)
        # email dots stripped -> valid Django username
        self.assertEqual(res.data['user']['username'], 'rajkumar')
        self.assertEqual(res.data['user']['email'], 'raj.kumar@gmail.com')
        user = User.objects.get(email='raj.kumar@gmail.com')
        self.assertFalse(user.has_usable_password())  # Google-only account

    @mock.patch('accounts.views.google_id_token.verify_oauth2_token')
    def test_second_login_reuses_the_same_user(self, verify):
        verify.return_value = fake_payload()
        first = self.client.post(self.url, {'credential': 'fake-jwt'}, format='json')
        second = self.client.post(self.url, {'credential': 'fake-jwt'}, format='json')
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.filter(email='raj.kumar@gmail.com').count(), 1)
        # get_or_create token -> same key on both logins
        self.assertEqual(first.data['token'], second.data['token'])

    @mock.patch('accounts.views.google_id_token.verify_oauth2_token')
    def test_username_collision_gets_numeric_suffix(self, verify):
        User.objects.create_user(username='rajkumar', email='other@example.com')
        verify.return_value = fake_payload()
        res = self.client.post(self.url, {'credential': 'fake-jwt'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data['user']['username'], 'rajkumar2')

    @mock.patch('accounts.views.google_id_token.verify_oauth2_token', side_effect=ValueError('bad token'))
    def test_invalid_credential_is_rejected(self, verify):
        res = self.client.post(self.url, {'credential': 'garbage'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(User.objects.count(), 0)

    @mock.patch('accounts.views.google_id_token.verify_oauth2_token')
    def test_unverified_email_is_rejected(self, verify):
        verify.return_value = fake_payload(email_verified=False)
        res = self.client.post(self.url, {'credential': 'fake-jwt'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    @override_settings(GOOGLE_CLIENT_ID='')
    @mock.patch('accounts.views.google_id_token.verify_oauth2_token')
    def test_missing_client_id_returns_500_not_configured(self, verify):
        res = self.client.post(self.url, {'credential': 'fake-jwt'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('not configured', res.data['detail'])
        verify.assert_not_called()

    def test_missing_credential_field_is_400(self):
        res = self.client.post(self.url, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class UsernameFromEmailTests(APITestCase):
    def test_strips_dots_plus_and_symbols(self):
        self.assertEqual(username_from_email('Raj.Kumar+ct@gmail.com'), 'rajkumarct')

    def test_falls_back_to_user_when_local_part_is_empty(self):
        self.assertEqual(username_from_email('@example.com'), 'user')


class TokenFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tester', email='tester@example.com'
        )
        self.token = Token.objects.create(user=self.user)
        self.auth = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}

    def test_me_requires_token(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user_with_token(self):
        res = self.client.get('/api/auth/me/', **self.auth)
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data['user']['username'], 'tester')

    def test_logout_deletes_token_and_blocks_further_me_calls(self):
        res = self.client.post('/api/auth/logout/', **self.auth)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT, res.data)
        self.assertFalse(Token.objects.filter(key=self.token.key).exists())
        self.assertEqual(self.client.get('/api/auth/me/', **self.auth).status_code, status.HTTP_401_UNAUTHORIZED)