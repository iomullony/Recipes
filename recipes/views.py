from decimal import Decimal

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Avg, Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.http import url_has_allowed_host_and_scheme

from .models import User, Category, Recipe, Ingredient, RecipeIngredient, Follow, Comment, PantryItem, SavedRecipe, ShoppingNeed, Rating
from .units import unit_family_and_factor

units = ['g', 'kg', 'mL', 'L', 'cups', 'tbsp', 'tsp', 'oz', 'lb', 'unit(s)']


def get_or_create_ingredient_ci(name):
    cleaned = name.strip()
    if not cleaned:
        return None, False
    normalized = cleaned.capitalize()
    existing = Ingredient.objects.filter(name__iexact=normalized).first()
    if existing:
        if existing.name != normalized:
            existing.name = normalized
            existing.save(update_fields=["name"])
        return existing, False
    return Ingredient.objects.create(name=normalized), True


def get_or_create_category_ci(name):
    cleaned = name.strip()
    if not cleaned:
        return None, False
    normalized = cleaned.capitalize()
    existing = Category.objects.filter(name__iexact=normalized).first()
    if existing:
        if existing.name != normalized:
            existing.name = normalized
            existing.save(update_fields=["name"])
        return existing, False
    return Category.objects.create(name=normalized), True


def index(request):
    query = request.GET.get("q", "").strip()
    recipes = (
        Recipe.objects.select_related("user")
        .order_by("-id")
    )

    if query:
        recipes = recipes.filter(
            Q(title__icontains=query)
            | Q(categories__name__icontains=query)
            | Q(ingredients__name__icontains=query)
        ).distinct()
    
    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "recipes/index.html", {
        "page_obj": page_obj,
        "query": query,
        "pagination_query": request.GET.copy(),
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
                category, _ = get_or_create_category_ci(value)
                if not category:
                    continue
                recipe.categories.add(category)

        # Handle ingredients
        # Match ingredient names with their quantities by index
        for i, ingredient_name in enumerate(ingredient_names):
            ingredient_name = ingredient_name.strip()
            if not ingredient_name:
                continue
            
            # Get or create the ingredient
            ingredient, _ = get_or_create_ingredient_ci(ingredient_name)
            if not ingredient:
                continue
            
            qty_val = ingredient_quantities[i].strip() if i < len(ingredient_quantities) else ""
            unit_val = ingredient_units[i].strip() if i < len(ingredient_units) else ""

            # Create RecipeIngredient relationship
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                quantity=qty_val or None,
                unit=unit_val,
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
            "unit": row.unit,
            "raw_quantity": row.quantity,
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
                category, _ = get_or_create_category_ci(value)
                if not category:
                    continue
                recipe.categories.add(category)

        RecipeIngredient.objects.filter(recipe=recipe).delete()
        for i, ingredient_name in enumerate(ingredient_names):
            ingredient_name = ingredient_name.strip()
            if not ingredient_name:
                continue
            ingredient, _ = get_or_create_ingredient_ci(ingredient_name)
            if not ingredient:
                continue
            qty_val = ingredient_quantities[i].strip() if i < len(ingredient_quantities) else ""
            unit_val = ingredient_units[i].strip() if i < len(ingredient_units) else ""

            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                quantity=qty_val or None,
                unit=unit_val,
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
            ingredient, _ = get_or_create_ingredient_ci(ingredient_name)
            if not ingredient:
                return redirect("pantry")

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
    comments = recipe.item_comments.all()

    is_saved = False
    if request.user.is_authenticated and request.user != recipe.user:
        is_saved = SavedRecipe.objects.filter(user=request.user, recipe=recipe).exists()

    rating_summary = recipe.ratings.aggregate(average=Avg("score"), count=Count("id"))
    user_rating = None
    if request.user.is_authenticated:
        user_rating = recipe.ratings.filter(user=request.user).values_list("score", flat=True).first()

    return render(request, 'recipes/recipe.html', {
        'recipe': recipe,
        'ingredients': ingredients,
        'comments': comments,
        'is_saved': is_saved,
        'rating_average': rating_summary['average'],
        'rating_count': rating_summary['count'],
        'user_rating': user_rating,
    })


@login_required
def rate_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if request.method == "POST":
        try:
            score = int(request.POST.get("score", ""))
        except (TypeError, ValueError):
            score = 0

        if 1 <= score <= 5:
            Rating.objects.update_or_create(
                user=request.user,
                recipe=recipe,
                defaults={"score": score},
            )

    return redirect("recipe", recipe_id=recipe.id)


@login_required
def save_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    if request.method == "POST" and recipe.user != request.user:
        saved = SavedRecipe.objects.filter(user=request.user, recipe=recipe).first()
        if saved:
            saved.delete()
        else:
            SavedRecipe.objects.create(user=request.user, recipe=recipe)

    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("recipe", recipe_id=recipe.id)


@login_required
def cookbook(request):
    query = request.GET.get("q", "").strip()
    recipes = (
        Recipe.objects.filter(Q(user=request.user) | Q(saved_by__user=request.user))
        .select_related("user")
        .distinct()
        .order_by("-id")
    )

    if query:
        recipes = recipes.filter(
            Q(title__icontains=query)
            | Q(categories__name__icontains=query)
            | Q(ingredients__name__icontains=query)
        ).distinct()

    paginator = Paginator(recipes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "recipes/cookbook.html", {
        "page_obj": page_obj,
        "query": query,
        "pagination_query": request.GET.copy(),
    })


@login_required
def add_to_shopping_list(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    if request.method == "POST":
        for ri in RecipeIngredient.objects.filter(recipe=recipe).select_related("ingredient"):
            # update_or_create keyed on (user, ingredient, recipe) makes this idempotent:
            # clicking "cook this" again for the same recipe overwrites its own requirement
            # instead of adding another copy of it on top.
            ShoppingNeed.objects.update_or_create(
                user=request.user,
                ingredient=ri.ingredient,
                recipe=recipe,
                defaults={"quantity": ri.quantity, "unit": ri.unit},
            )

        return redirect("shopping")

    return redirect("recipe", recipe_id=recipe.id)


@login_required
def shopping(request):
    needs = ShoppingNeed.objects.filter(user=request.user).select_related("ingredient", "recipe")
    pantry_by_ingredient = {
        item.ingredient_id: item
        for item in PantryItem.objects.filter(user=request.user)
    }

    needs_by_ingredient = {}
    for need in needs:
        needs_by_ingredient.setdefault(need.ingredient_id, []).append(need)

    shopping_list = []
    for ingredient_id, ingredient_needs in needs_by_ingredient.items():
        ingredient = ingredient_needs[0].ingredient
        pantry_item = pantry_by_ingredient.get(ingredient_id)
        recipes = [need.recipe for need in ingredient_needs]
        specified_needs = [need for need in ingredient_needs if need.quantity is not None]

        if not specified_needs:
            # No recipe gave an amount for this ingredient - can't do math, just remind to buy it.
            if pantry_item:
                continue  # Already have some - assume that's covered.
            shopping_list.append({
                "ingredient": ingredient,
                "quantity": None,
                "unit": ingredient_needs[0].unit,
                "have_quantity": None,
                "total_needed": None,
                "recipes": recipes,
            })
            continue

        # Group needs by unit family (e.g. mass) so "500 g" and "0.5 kg" add up
        # correctly instead of being treated as unrelated amounts.
        families = {}
        for need in specified_needs:
            family, factor = unit_family_and_factor(need.unit)
            group = families.setdefault(family, {"base_total": Decimal("0"), "display_unit": need.unit, "recipes": []})
            group["base_total"] += need.quantity * factor
            group["recipes"].append(need.recipe)

        for family, group in families.items():
            display_unit = group["display_unit"]
            _, display_factor = unit_family_and_factor(display_unit)
            total_needed_base = group["base_total"]

            have_base = Decimal("0")
            if pantry_item:
                have_family, have_factor = unit_family_and_factor(pantry_item.unit)
                if have_family == family:
                    have_base = pantry_item.quantity * have_factor

            buy_base = total_needed_base - have_base
            if buy_base <= 0:
                continue  # Fully covered by what's already in the pantry

            shopping_list.append({
                "ingredient": ingredient,
                "quantity": buy_base / display_factor,
                "unit": display_unit,
                "have_quantity": have_base / display_factor,
                "total_needed": total_needed_base / display_factor,
                "recipes": group["recipes"],
            })

    shopping_list.sort(key=lambda row: row["ingredient"].name)

    return render(request, "recipes/shopping.html", {
        "shopping_list": shopping_list,
    })


@login_required
def shopping_delete(request, ingredient_id):
    if request.method == "POST":
        ShoppingNeed.objects.filter(user=request.user, ingredient_id=ingredient_id).delete()

    return redirect("shopping")


@login_required
def delete_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if recipe.user != request.user:
        return redirect("recipe", recipe_id=recipe.id)

    if request.method == "POST":
        recipe.delete()
        return redirect("index")

    return redirect("recipe", recipe_id=recipe.id)


@login_required
def add_comment(request, recipe_id):
    if request.method == "POST":
        
        comment = request.POST.get('comment')
        item = Recipe.objects.get(id=recipe_id)
        
        Comment.objects.create(
            user=request.user,
            item=item,
            comment=comment
        )    
    
        return redirect('recipe', recipe_id=recipe_id)
    else:
        return redirect('index')
