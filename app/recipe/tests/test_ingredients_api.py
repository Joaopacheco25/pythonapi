from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENT_API = reverse('recipe:ingredient-list')


class PublicTestIngredient(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test the authorization is required"""
        result = self.client.get(INGREDIENT_API)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)
