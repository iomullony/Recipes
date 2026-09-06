from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_category_name_ci",
            )
        ]


class Ingredient(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_ingredient_name_ci",
            )
        ]


class Recipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipes")
    title = models.CharField(max_length=200)
    categories = models.ManyToManyField(Category, related_name="categories", blank=True)
    ingredients = models.ManyToManyField("Ingredient", through="RecipeIngredient", related_name="recipes")
    preparation = models.TextField()
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to='recipes/', null=True, blank=True)
    date_time = models.DateTimeField(auto_now_add=True)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="item_comments")
    comment = models.CharField(max_length=200)
    date_time = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')


class SavedRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "recipe"], name="unique_user_recipe_saved")
        ]
        ordering = ["-saved_at"]


class PantryItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pantry_items")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="pantry_items")
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "ingredient"], name="unique_user_ingredient_pantry")
        ]
        ordering = ["ingredient__name"]


class ShoppingNeed(models.Model):
    """How much of an ingredient a given recipe still requires for a user's shopping list.

    Kept per-recipe (rather than a single running total) so clicking "I want to cook
    this" again for the same recipe overwrites its own contribution instead of piling
    another copy of the requirement on top of it.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shopping_needs")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="shopping_needs")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="shopping_needs")
    quantity = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "ingredient", "recipe"], name="unique_user_ingredient_recipe_need")
        ]
        ordering = ["ingredient__name"]

