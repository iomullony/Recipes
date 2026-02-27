from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)


class Ingredient(models.Model):
    name = models.CharField(max_length=80, unique=True)


class Recipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipes")
    title = models.CharField(max_length=200)
    categories = models.ManyToManyField(Category, related_name="categories", blank=True)
    ingredients = models.ManyToManyField("Ingredient", through="RecipeIngredient", related_name="recipes")
    preparation = models.TextField()
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to='recipes/', null=True, blank=True)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=40, blank=True)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="item_comments")
    comment = models.CharField(max_length=200)
