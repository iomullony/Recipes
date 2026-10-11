# WoNiNi: Recipe and Meal Preparation Manager

## Overview

WoNiNi is a recipe and meal-preparation application built with Django, SQLite, HTML, CSS, and JavaScript. It helps users collect recipes, organize ingredients they have at home, and work out what they still need before cooking. The application combines a public recipe catalogue with private cooking-planning tools, connecting recipe discovery to saving a recipe, checking pantry stock, and preparing a shopping list.

Users can register, browse and search recipes by title, category, or ingredient, and view recipe details including ingredients, quantities, preparation instructions, notes, images, ratings, and comments. Authenticated users can create and edit their own recipes, save other users' recipes to a personal cookbook, rate recipes from one to five stars, and add comments. Each user's pantry stores ingredient amounts and units. When a user chooses “I want to cook this” for a recipe, WoNiNi compares the recipe's ingredient requirements with the pantry and records the remaining amounts on the user's shopping list.

The application is designed around a cooking workflow rather than a feed, marketplace, or generic messaging system. Its main purpose is helping a person decide what to cook and prepare the ingredients needed to do it.

## Distinctiveness and Complexity

WoNiNi satisfies the distinctiveness and complexity requirements because it is a recipe and meal-preparation tool with connected workflows that differ from the earlier course projects. Its data model represents recipes, ingredients, recipe-specific quantities and units, categories, pantry inventory, saved recipes, ratings, comments, and shopping needs. These relationships allow a user's pantry and shopping list to respond to recipes they choose to cook.

The application is distinct from the CS50W Pizza project. It does not sell menu items, accept orders, calculate prices, or process checkout. A recipe's ingredients are structured data used for cooking and inventory calculations, not purchasable products. The shopping page is a private preparation aid that identifies ingredients and amounts still needed for selected recipes. There are no products, prices, payments, orders, delivery details, or cart checkout.

The application is also not a social-network application. Profiles, following, comments, and ratings support recipe authorship, feedback, and discovery, but the primary workflow remains creating a recipe, saving it, checking pantry quantities, and preparing a shopping list. There is no general-purpose status posting, messaging, or social feed. The home page is a recipe catalogue, and the cookbook is a personal collection of recipes.

The project is more complex than a simple CRUD application because it combines related workflows. Recipe creation accepts a title, preparation text, notes, image, categories, ingredients, quantities, and units. Ingredients and categories are reused case-insensitively. Pantry quantities are considered when shopping needs are calculated. Shopping needs are stored per user, ingredient, and recipe, so selecting the same recipe again updates that recipe's contribution instead of duplicating it. Unit conversion compares quantities only within compatible families (for example, grams and kilograms); it does not assume that weight and volume can be converted without ingredient-specific density. Saved recipes and ratings also use database constraints to prevent duplicate records for the same user and recipe. Search works across recipe titles, categories, and ingredients, including within a user's private cookbook.

## Main Features

- Registration and login, profiles and follows, plus a searchable, paginated recipe catalogue.
- Recipe creation, editing, and owner-restricted deletion, including ingredients, quantities, images, and instructions.
- Recipe details with comments, adjustable one-to-five-star ratings, and recipe-author information.
- A personal cookbook for recipes the user creates or saves.
- Pantry inventory and per-recipe shopping needs calculated from available quantities and compatible units.
- Responsive Bootstrap styling and client-side recipe-photo cropping.

## Project Files

The project uses the conventional Django layout: `manage.py` and the dependency manifests are in the root; `project/` contains site configuration; and `recipes/` contains the application, its templates, static assets, and migrations. There are no other application projects in this repository.

### Root files

- `manage.py` is Django's command-line entry point for running the development server, applying migrations, and using other management commands.
- `requirements.txt` lists the Python packages required by the application: Django and Pillow (used for uploaded images).
- `package.json` and `package-lock.json` define and lock the frontend Node.js packages used to compile SCSS: Bootstrap and Sass. Node.js is only needed when recompiling styles; it is not needed just to run Django.
- `.gitignore` excludes local databases, uploaded media, Python caches, Node dependencies, logs, and generated Sass source maps from version control.
- `README.md` describes the application, its structure, and how to run it.

### Django configuration

- `project/__init__.py` marks the configuration folder as a Python package.
- `project/settings.py` configures installed applications, middleware, the custom user model, SQLite, static files, media uploads, and other Django settings.
- `project/urls.py` connects the Django admin and the recipes application's URL configuration, and serves uploaded media during local development.
- `project/asgi.py` and `project/wsgi.py` expose ASGI and WSGI entry points for compatible servers.

### Recipes application

- `recipes/__init__.py` marks the app as a Python package, and `recipes/apps.py` defines its Django application configuration.
- `recipes/models.py` defines users, recipes, categories, ingredients, recipe-ingredient quantities, comments, follows, saved recipes, ratings, pantry items, and shopping needs, including their database constraints and relationships.
- `recipes/views.py` implements registration and authentication, recipe browsing and editing, search, profiles, following, ratings, comments, saved recipes, pantry updates, and shopping-list calculations.
- `recipes/urls.py` maps browser paths to the application views.
- `recipes/admin.py` registers application models with Django's admin site.
- `recipes/units.py` defines supported mass and volume conversions and unit-family behavior used when comparing pantry quantities with recipe requirements.
- `recipes/tests.py` is the Django test module. It currently contains the generated placeholder and does not yet define automated tests.

### Database migrations

`recipes/migrations/__init__.py` makes the migrations directory a Python package. The numbered migration files record the database schema changes in order: `0001_initial.py` creates the custom user; `0002_category_ingredient_recipe_comment_recipeingredient_and_more.py` adds the core recipe, category, ingredient, and comment models; `0003_recipe_title.py` and `0004_alter_recipe_title.py` add and adjust the recipe title; `0005_recipe_image.py` adds recipe images; `0006_recipe_date_time_follow_liked.py` adds recipe timestamps, following, and the original liked model; `0007_pantryitem.py` adds pantry inventory; `0008_comment_date_time_category_unique_category_name_ci_and_more.py` adds comment timestamps and case-insensitive uniqueness constraints; `0009_savedrecipe_delete_liked_and_more.py` replaces likes with saved recipes; `0010_shoppingneed_recipeingredient_structured_quantity.py` adds structured quantities and per-recipe shopping needs; and `0011_rating.py` adds ratings.

### Templates and static assets

Templates are in `recipes/templates/recipes/`. `layout.html` is the shared page layout and navigation. `index.html` and `recipes.html` show recipe listings; `recipe.html` shows an individual recipe; `new_recipe.html` and `edit_recipe.html` contain recipe forms; `cookbook.html`, `pantry.html`, and `shopping.html` implement the private cooking workflow; `profile.html` shows a user profile; `login.html` and `register.html` contain account forms; and `pagination.html` is shared by paginated listings. `includes/recipe_crop_modal.html` defines the image-cropping dialog used by the recipe forms.

Static assets are in `recipes/static/recipes/`. `scss/styles.scss` is the Sass source stylesheet; `css/styles.css` is its compiled stylesheet; and `css/override.css` contains additional application styles. `js/recipe-image-crop.js` implements the crop interaction, and `imgs/user.svg` is the profile placeholder graphic. The shared template loads Bootstrap and icon/font assets from their public CDNs.

## How to Run the Application

Use Python 3.12 or newer for the pinned Django 6.1.1 dependency, and run these commands from the project root. On Windows, the virtual environment activation command shown below is for PowerShell:

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the Python dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Apply the database migrations:

   ```powershell
   python manage.py migrate
   ```

4. Start the development server:

   ```powershell
   python manage.py runserver
   ```

5. Open `http://127.0.0.1:8000/` in a browser. To create an administrator account for `/admin/`, run `python manage.py createsuperuser` in a second terminal while the virtual environment is active.

Node.js is optional for running the app. To install the frontend dependencies and recompile the stylesheet from its Sass source, run:

```powershell
npm install
npx sass recipes/static/recipes/scss/styles.scss recipes/static/recipes/css/styles.css
```

## Additional Information for Staff

The application uses SQLite and local media storage for development. On a fresh checkout, running migrations creates the local database. User-uploaded photos are stored under `media/recipes/` while developing and are not source files. In production, the Django secret key, debug setting, allowed hosts, database, and media storage must be configured for the deployment environment rather than using development defaults in `project/settings.py`.

Most actions that change data require authentication and use Django's CSRF protection. Recipe editing and deletion are restricted to the recipe owner. Saving, rating, commenting, pantry updates, shopping-list actions, and cookbook access require a logged-in user. The rating and saved-recipe models enforce one record per user and recipe at the database level.

The intended demonstration path is to register an account, create or browse a recipe, save a recipe to the cookbook, add ingredients to the pantry, choose “I want to cook this,” and review the generated shopping list. Public search and cookbook search are separate: the home page searches all recipes, while the cookbook search is limited to recipes owned by or saved by the current user. The project currently has no automated test cases in `recipes/tests.py`; this is disclosed here so that the test status is clear.
