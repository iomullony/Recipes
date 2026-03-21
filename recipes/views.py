from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import User, Category, Recipe, Ingredient, RecipeIngredient, Follow, Liked, PantryItem

units = ['g', 'kg', 'mL', 'L', 'cups', 'tbsp', 'tsp', 'oz', 'lb', 'unit(s)']

def index(request):
    recipes = (
        Recipe.objects.select_related("user")
        .order_by("-id")
    )
    
    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "recipes/index.html", {
        "page_obj": page_obj
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

        return HttpResponseRedirect(reverse("index"))
    else:
        categories = Category.objects.all()
        return render(request, "recipes/new_recipe.html", {
            "categories": categories,
            "units": units,
        })


@login_required
def edit_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if recipe.user != request.user:
        return redirect("recipe", recipe_id=recipe.id)

    categories = Category.objects.all()
    existing_ingredients = RecipeIngredient.objects.filter(recipe=recipe).select_related("ingredient")
    selected_category_ids = list(recipe.categories.values_list("id", flat=True))
    ingredient_rows = [
        {
            "name": row.ingredient.name,
            "quantity": row.quantity,
            "unit": row.quantity.split()[-1] if row.quantity and " " in row.quantity else "",
            "raw_quantity": row.quantity.split()[0] if row.quantity and " " in row.quantity else row.quantity,
        }
        for row in existing_ingredients
    ]

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        preparation = request.POST.get("preparation", "").strip()
        notes = request.POST.get("notes", "").strip()
        category_values = request.POST.getlist("categories")
        ingredient_names = request.POST.getlist("ingredient_name")
        ingredient_quantities = request.POST.getlist("ingredient_qty")
        ingredient_units = request.POST.getlist("ingredient_unit")
        photo = request.FILES.get("photo")
        max_image_bytes = 2 * 1024 * 1024

        if not title:
            return render(request, "recipes/edit_recipe.html", {
                "recipe": recipe,
                "categories": categories,
                "units": units,
                "selected_category_ids": selected_category_ids,
                "ingredient_rows": ingredient_rows,
                "error": "Title is required.",
            })

        if not preparation:
            return render(request, "recipes/edit_recipe.html", {
                "recipe": recipe,
                "categories": categories,
                "units": units,
                "selected_category_ids": selected_category_ids,
                "ingredient_rows": ingredient_rows,
                "error": "Preparation instructions are required.",
            })

        if photo and photo.size > max_image_bytes:
            return render(request, "recipes/edit_recipe.html", {
                "recipe": recipe,
                "categories": categories,
                "units": units,
                "selected_category_ids": selected_category_ids,
                "ingredient_rows": ingredient_rows,
                "error": "Image must be smaller than 2 MB. Please choose a smaller file.",
            })

        recipe.title = title
        recipe.preparation = preparation
        recipe.notes = notes
        if photo:
            recipe.image = photo
        elif request.POST.get("remove_image"):
            if recipe.image:
                recipe.image.delete(save=False)
            recipe.image = None
        recipe.save()

        recipe.categories.clear()
        for value in category_values:
            value = value.strip()
            if not value:
                continue
            if value.isdigit():
                try:
                    category = Category.objects.get(id=value)
                    recipe.categories.add(category)
                except Category.DoesNotExist:
                    continue
            else:
                category, _ = Category.objects.get_or_create(name=value)
                recipe.categories.add(category)

        RecipeIngredient.objects.filter(recipe=recipe).delete()
        for i, ingredient_name in enumerate(ingredient_names):
            ingredient_name = ingredient_name.strip()
            if not ingredient_name:
                continue
            ingredient, _ = Ingredient.objects.get_or_create(name=ingredient_name)
            qty_val = ingredient_quantities[i].strip() if i < len(ingredient_quantities) else ""
            unit_val = ingredient_units[i].strip() if i < len(ingredient_units) else ""
            quantity = qty_val if qty_val else ""
            if qty_val and unit_val:
                quantity = f"{qty_val} {unit_val}"

            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                quantity=quantity,
            )

        return redirect("recipe", recipe_id=recipe.id)

    return render(request, "recipes/edit_recipe.html", {
        "recipe": recipe,
        "categories": categories,
        "units": units,
        "selected_category_ids": selected_category_ids,
        "ingredient_rows": ingredient_rows,
    })


def profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    recipes = Recipe.objects.filter(user=user)

    # Paginate
    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Check if current user follows this user
    is_following = False
    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user
        ).exists()
    
    return render(request, "recipes/profile.html", {
        "user": user,
        "is_following": is_following,
        "recipes": page_obj.object_list,
        "page_obj": page_obj
    })


@login_required
def follow(request):
    if request.method == "POST":
        user_id = request.POST.get('id')
        target_user = get_object_or_404(User, id=user_id)
        
        # Prevent following yourself
        if request.user == target_user:
            return redirect('profile', user_id=user_id)
        
        # Check if already following
        follow_obj = Follow.objects.filter(
            follower=request.user,
            following=target_user
        ).first()
        
        if follow_obj:
            # Unfollow
            follow_obj.delete()
        else:
            # Follow
            Follow.objects.create(
                follower=request.user,
                following=target_user
            )
        
        return redirect('profile', user_id=user_id)
    
    return redirect('index')


@login_required
def pantry(request):
    query = request.GET.get("q", "").strip()
    pantry_items = PantryItem.objects.filter(user=request.user).select_related("ingredient")

    if query:
        pantry_items = pantry_items.filter(ingredient__name__icontains=query)

    if request.method == "POST":
        ingredient_name = request.POST.get("ingredient_name", "").strip()
        quantity_raw = request.POST.get("quantity", "").strip()
        unit = request.POST.get("unit", "").strip()

        if ingredient_name:
            ingredient, _ = Ingredient.objects.get_or_create(name=ingredient_name)

            try:
                quantity = float(quantity_raw) if quantity_raw else 0.0
            except ValueError:
                quantity = 0.0

            pantry_item, created = PantryItem.objects.get_or_create(
                user=request.user,
                ingredient=ingredient,
                defaults={"quantity": quantity, "unit": unit}
            )

            if not created:
                pantry_item.quantity = quantity
                pantry_item.unit = unit
                pantry_item.save()

        return redirect("pantry")

    return render(request, "recipes/pantry.html", {
        "pantry_items": pantry_items,
        "units": units,
        "query": query,
    })


@login_required
def pantry_update(request, item_id):
    if request.method == "POST":
        pantry_item = get_object_or_404(PantryItem, id=item_id, user=request.user)
        quantity_raw = request.POST.get("quantity", "").strip()
        unit = request.POST.get("unit", "").strip()

        try:
            pantry_item.quantity = float(quantity_raw) if quantity_raw else 0.0
        except ValueError:
            pantry_item.quantity = 0.0

        pantry_item.unit = unit
        pantry_item.save()

    return redirect("pantry")


@login_required
def pantry_delete(request, item_id):
    if request.method == "POST":
        pantry_item = get_object_or_404(PantryItem, id=item_id, user=request.user)
        pantry_item.delete()
    return redirect("pantry")


def recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe.objects.select_related("user"), id=recipe_id)
    ingredients = RecipeIngredient.objects.filter(recipe=recipe).select_related("ingredient")

    return render(request, 'recipes/recipe.html', {
        'recipe': recipe,
        'ingredients': ingredients,
    })