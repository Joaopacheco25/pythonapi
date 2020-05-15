from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test the authorization is required"""
        result = self.client.get(INGREDIENT_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@londonappdev.com',
            password='test123'
        )
        self.client.force_authenticate(self.user)

    def test_retrive_ingredient(self):
        Ingredient.objects.create(user=self.user, name='garlic')
        Ingredient.objects.create(user=self.user, name='rucula')

        result = self.client.get(INGREDIENT_URL)

        ing = Ingredient.objects.all().order_by('-name')

        serializer = IngredientSerializer(ing, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            'other@londonappdev.com',
            'test123')

        Ingredient.objects.create(user=user2, name='cenoura')
        ing = Ingredient.objects.create(user=self.user, name='cebola')

        result = self.client.get(INGREDIENT_URL)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.data[0]['name'], ing.name)

    def test_create_ingredient_successful(self):
        payload = {'name': 'garlic'}

        result = self.client.post(INGREDIENT_URL, payload)

        ing = Ingredient.objects.filter(
            user=self.user, name=payload['name']).exists()

        self.assertTrue(ing)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

    def test_create_ingredient_invalid_payload(self):
        payload = {'name': ''}

        result = self.client.post(INGREDIENT_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
