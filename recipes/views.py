from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef, Count, Q

from .models import User, Category, Recipe, Ingredient, RecipeIngredient

units = ['g', 'kg', 'mL', 'L', 'cups', 'tbsp', 'tsp', 'oz', 'lb', 'unit(s)']

def index(request):
    return render(request, "recipes/index.html", {
        "recipes": Recipe.objects.all()
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "recipes/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "recipes/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "recipes/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "recipes/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "recipes/register.html")
    

@login_required
def new_recipe(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        preparation = request.POST.get("preparation", "").strip()
        notes = request.POST.get("notes", "").strip()
        categories = request.POST.getlist('categories')
        ingredient_names = request.POST.getlist('ingredient_name')
        ingredient_quantities = request.POST.getlist('ingredient_qty')
        ingredient_units = request.POST.getlist('ingredient_unit')
        photo = request.FILES.get("photo")
        max_image_bytes = 2 * 1024 * 1024  # 2 MB limit to match front-end check

        # Validate required fields - ensure they're not just whitespace
        if not title or not title.strip():
            categories = Category.objects.all()
            return render(request, "recipes/new_recipe.html", {
                "categories": categories,
                "units": units,
                "error": "Title is required."
            })
        
        if not preparation or not preparation.strip():
            categories = Category.objects.all()
            return render(request, "recipes/new_recipe.html", {
                "categories": categories,
                "units": units,
                "error": "Preparation instructions are required."
            })

        # Validate image size if provided
        if photo and photo.size > max_image_bytes:
            categories = Category.objects.all()
            return render(request, "recipes/new_recipe.html", {
                "categories": categories,
                "units": units,
                "error": "Image must be smaller than 2 MB. Please choose a smaller file."
            })

        # Create the recipe
        recipe = Recipe.objects.create(
            user=request.user,
            title=title,
            preparation=preparation,
            notes=notes,
            image=photo
        )

        for value in categories:
            if not value.strip():
                continue
            if value.isdigit():
                try:
                    category = Category.objects.get(id=value)
                    recipe.categories.add(category)
                except Category.DoesNotExist:
                    pass
            else:
                # New category created via Tom Select
                category, created = Category.objects.get_or_create(name=value.strip())
                recipe.categories.add(category)

        # Handle ingredients
        # Match ingredient names with their quantities by index
        for i, ingredient_name in enumerate(ingredient_names):
            ingredient_name = ingredient_name.strip()
            if not ingredient_name:
                continue
            
            # Get or create the ingredient
            ingredient, created = Ingredient.objects.get_or_create(name=ingredient_name)
            
            # Build quantity string: number + unit (e.g. "2 cups", "100 g")
            quantity = ""
            qty_val = ingredient_quantities[i].strip() if i < len(ingredient_quantities) else ""
            unit_val = ingredient_units[i].strip() if i < len(ingredient_units) else ""
            if qty_val:
                quantity = qty_val
                if unit_val:
                    quantity = f"{qty_val} {unit_val}"
            
            # Create RecipeIngredient relationship
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                quantity=quantity
            )

        # Redirect to recipe detail page or index
        return HttpResponseRedirect(reverse("index"))
    else:
        # GET request - show the form
        categories = Category.objects.all()
        return render(request, "recipes/new_recipe.html", {
            "categories": categories,
            "units": units,
        })