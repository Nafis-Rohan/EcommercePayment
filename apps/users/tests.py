from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserModelTests(TestCase):
    """Unit test for the model."""

    def test_email_must_be_unique(self):
        User.objects.create_user(username='a', email='dup@example.com', password='pass12345')
        with self.assertRaises(IntegrityError):
            User.objects.create_user(username='b', email='dup@example.com', password='pass12345')


class AuthAPITests(APITestCase):
    """API tests for authentication (register + login)."""

    def test_register_creates_user(self):
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'strongpass123',
            'password_confirm': 'strongpass123',
        }
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')

    def test_login_returns_tokens(self):
        User.objects.create_user(username='loginuser', email='login@example.com', password='testpass123')
        response = self.client.post(
            reverse('login'), {'email': 'login@example.com', 'password': 'testpass123'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_with_wrong_password_fails(self):
        User.objects.create_user(username='loginuser2', email='login2@example.com', password='testpass123')
        response = self.client.post(
            reverse('login'), {'email': 'login2@example.com', 'password': 'wrongpass'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
