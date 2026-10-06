"""End-to-end tests for the /api/auth/ endpoints (register → me → logout → login)."""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class AuthFlowTests(APITestCase):
    def setUp(self):
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.logout_url = '/api/auth/logout/'
        self.me_url = '/api/auth/me/'
        self.credentials = {
            'username': 'learner1',
            'email': 'learner1@example.com',
            'password': 'Str0ngPass!23',
        }

    def test_register_creates_user_and_returns_token(self):
        res = self.client.post(self.register_url, self.credentials, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertIn('token', res.data)
        self.assertEqual(res.data['user']['username'], 'learner1')
        self.assertTrue(User.objects.filter(username='learner1').exists())

    def test_register_rejects_weak_password(self):
        res = self.client.post(
            self.register_url,
            {**self.credentials, 'password': '123'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_rejects_duplicate_username(self):
        User.objects.create_user(**self.credentials)
        res = self.client.post(self.register_url, self.credentials, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_username_returns_token(self):
        User.objects.create_user(**self.credentials)
        res = self.client.post(
            self.login_url,
            {'identifier': 'learner1', 'password': self.credentials['password']},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertIn('token', res.data)

    def test_login_with_email_returns_token(self):
        User.objects.create_user(**self.credentials)
        res = self.client.post(
            self.login_url,
            {'identifier': self.credentials['email'], 'password': self.credentials['password']},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)

    def test_login_with_wrong_password_fails(self):
        User.objects.create_user(**self.credentials)
        res = self.client.post(
            self.login_url,
            {'identifier': 'learner1', 'password': 'wrong-password'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_token(self):
        self.assertEqual(self.client.get(self.me_url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user_with_token(self):
        user = User.objects.create_user(**self.credentials)
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data['user']['username'], user.username)

    def test_logout_deletes_token_and_blocks_further_me_calls(self):
        user = User.objects.create_user(**self.credentials)
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        res = self.client.post(self.logout_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT, res.data)
        self.assertFalse(Token.objects.filter(key=token.key).exists())
        # The same (now deleted) token must no longer authenticate.
        self.assertEqual(self.client.get(self.me_url).status_code, status.HTTP_401_UNAUTHORIZED)
