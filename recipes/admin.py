from django.contrib import admin

from .models import User, Category, Ingredient, Recipe

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Ingredient)
admin.site.register(Recipe)
