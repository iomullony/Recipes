from django.contrib import admin

from .models import User, Category, Ingredient, Recipe, RecipeIngredient, Follow, Comment, PantryItem

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
admin.site.register(Follow)
admin.site.register(Comment)
admin.site.register(PantryItem)
