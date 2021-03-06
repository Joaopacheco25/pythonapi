from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_API_USER = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            'email': 'joao@gmail.com',
            'password': 'testpass',
            'name': 'Test name'
        }

        result = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**result.data)
        self.assertTrue(user.check_password(payload['password']))

    def test_create_user_already_exists(self):
        """Test creating user that already exists"""
        payload = {
            'email': 'joao@gmail.com',
            'password': 'testpass',
        }

        create_user(**payload)
        user = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(user.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_password_too_short(self):
        """Test the user password have 5 chars"""
        payload = {
            'email': 'joao@gmail.com',
            'password': 'pw',
        }

        result = self.client.post(CREATE_USER_URL, payload)
        user = get_user_model().objects.filter(email=payload['email']).exists()

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user)

    def test_create_token_for_user(self):
        """Test the a token is created for user"""
        payload = {'email': 'joao@gmail.com', 'password': 'testpass'}

        create_user(**payload)
        result = self.client.post(TOKEN_API_USER, payload)

        self.assertIn('token', result.data)
        self.assertEqual(result.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that when is not created if invalid credentials are given"""
        create_user(email='joao@gmail.com', password='testpassword')
        payload = {'email': 'joao@gmail.com', 'password': 'wrong'}

        result = self.client.post(TOKEN_API_USER, payload)

        self.assertNotIn('token', result.data)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that token is not create if user doesn't exists"""
        payload = {'email': 'test@gmail.com', 'password': 'test123'}

        result = self.client.post(TOKEN_API_USER, payload)

        self.assertNotIn('token', result.data)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_missing_fields(self):
        """Test that token is not create if user doesn't exists"""
        payload = {'email': 'test@gmail.com', 'password': ''}

        result = self.client.post(TOKEN_API_USER, payload)

        self.assertNotIn('token', result.data)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users"""
        result = self.client.get(ME_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API request that require authentication"""

    def setUp(self):
        self.user = create_user(
            email='tes@gmail.com',
            password='testpass',
            name='name'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieve profile for logged in used"""
        result = self.client.get(ME_URL)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me url"""
        result = self.client.post(ME_URL, {})

        self.assertEqual(result.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authentication user"""
        payload = {'name': 'new name', 'password': 'newpassword123'}

        result = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
