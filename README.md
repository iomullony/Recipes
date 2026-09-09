# WoNiNi: Recipe and Meal Preparation Manager

## Overview

WoNiNi is a recipe and meal-preparation management application built with Django, SQLite, HTML, CSS, and JavaScript. It helps users collect recipes, organize the ingredients they have at home, and calculate what they still need before cooking. The application combines a public recipe catalogue with private cooking-planning tools so that a recipe is connected to the practical steps that follow: saving it, checking the pantry, and creating a shopping list.

Users can register for an account, browse recipes, search by title, category, or ingredient, and open a detailed recipe page containing ingredients, quantities, preparation instructions, notes, images, ratings, and comments. Authenticated users can create and edit their own recipes, save recipes created by other users to a personal cookbook, rate recipes from one to five stars, and add comments. The personal pantry stores ingredient quantities and units. When a user chooses "I want to cook this" on a recipe, WoNiNi compares that recipe's requirements with the pantry and creates or updates a shopping list for the missing ingredients.

The project is designed around a cooking workflow rather than a feed, a marketplace, or a generic messaging system. Its main purpose is helping a person decide what to cook and prepare the ingredients needed to do it.

## Distinctiveness and Complexity

WoNiNi satisfies the distinctiveness and complexity requirements because it is a recipe and meal-preparation tool with several connected workflows that are not present in the earlier course projects. The central data model is not a collection of posts or products. It represents recipes, ingredients, recipe-specific quantities and units, categories, pantry inventory, saved recipes, ratings, comments, and shopping needs. These relationships allow a user's pantry and shopping list to respond to the recipes they choose to cook.

The application is distinct from the old CS50W Pizza project. It does not sell menu items, accept orders, calculate prices, or process checkout. A recipe's ingredients are structured data used for cooking and inventory calculations, not purchasable products. The shopping page is a private preparation aid: it tells the user which ingredients and amounts are still needed for selected recipes. There are no products, prices, payments, orders, delivery details, or cart checkout.

The application also is not a social-network application. Profiles, following, comments, and ratings are supporting features attached to recipes. They let users identify recipe authors, provide feedback, and discover recipes, but the primary workflow remains creating a recipe, saving it, checking pantry quantities, and preparing a shopping list. There is no general-purpose status posting, messaging, timeline, or social feed. The home page is a recipe catalogue, and the cookbook is a personal collection of recipes to cook.

The project is more complex than a simple CRUD application because it combines several related workflows. Recipe creation accepts a title, preparation text, notes, image, categories, ingredients, quantities, and units. Ingredients and categories are reused case-insensitively. Pantry quantities can be updated and are considered when shopping needs are calculated. Shopping needs are stored per user, ingredient, and recipe so that cooking the same recipe again updates its contribution instead of creating duplicate requirements. Saved recipes and ratings also use database constraints to prevent duplicate records for the same user and recipe. Search works across recipe titles, categories, and ingredients, including within a user's private cookbook.

## Main Features

- Account registration, authentication, login, and logout.
- Public recipe browsing with pagination.
- Search across recipe titles, categories, and ingredients.
- Recipe creation with image upload, categories, ingredients, quantities, units, preparation instructions, and notes.
- Recipe editing and deletion restricted to the recipe owner.
- Recipe detail pages with ingredients, preparation, notes, comments, ratings, and image display.
- One-to-five-star ratings with one rating per user per recipe; users can update their rating.
- Personal cookbook containing recipes written by the user and recipes saved from other users.
- Pantry inventory with ingredient quantities and units.
- Shopping-list generation based on selected recipes and pantry quantities.
- User profiles, recipe authorship, following, and recipe comments.
- Responsive styling using Bootstrap and project-specific CSS/SCSS.
- Client-side image cropping support for recipe photos.

## File Structure

The root `manage.py` file is Django's command-line entry point. `requirements.txt` lists the Python packages needed to run the project. `package.json` and `package-lock.json` describe the frontend packages: Bootstrap and Sass. `db.sqlite3` is the local development database, while `media/recipes/` stores uploaded recipe images during local development.

The `project/` directory contains Django's project configuration. `settings.py` defines installed applications, middleware, the custom user model, the SQLite database, static files, and media files. `urls.py` connects the admin site and the recipes application. `asgi.py` and `wsgi.py` provide ASGI and WSGI entry points for compatible servers.

The `recipes/` directory contains the application itself. `models.py` defines users, recipes, categories, ingredients, recipe-ingredient quantities, comments, follows, saved recipes, ratings, pantry items, and shopping needs. `views.py` implements authentication, recipe CRUD operations, searching, cookbook behavior, pantry updates, shopping-list calculations, comments, saved recipes, and ratings. `urls.py` maps browser URLs to those views. `admin.py` registers the application's models with Django admin, and `apps.py` contains the application configuration. `units.py` contains unit conversion and unit-family logic used when comparing pantry quantities with recipe requirements. `tests.py` is the application test module.

The `recipes/migrations/` directory contains the database migration history. The migrations create the application's tables and record later changes, including images, pantry items, saved recipes, structured shopping quantities, and ratings. The migration named `0011_rating.py` creates the rating table and its unique user-recipe constraint.

The templates in `recipes/templates/recipes/` define the user interface. `layout.html` provides the shared navigation and page structure. `index.html` and `recipes.html` display the public recipe catalogue. `recipe.html` displays a complete recipe and its rating and comment controls. `new_recipe.html` and `edit_recipe.html` provide recipe forms. `cookbook.html`, `pantry.html`, and `shopping.html` implement the private cooking workflow. `profile.html` displays user information and recipes. `login.html` and `register.html` provide authentication forms. `pagination.html` is shared by paginated pages.

The static files are in `recipes/static/recipes/`. `scss/styles.scss` is the source stylesheet, `css/styles.css` contains the compiled Bootstrap/project styles, and `css/override.css` contains project-specific layout and component adjustments. `js/recipe-image-crop.js` provides the image-cropping interaction used when adding or editing recipe photos. The `imgs/` directory contains interface images such as the default profile image.

## How to Run the Application

1. Make sure Python 3.11 or newer is installed, then create and activate a virtual environment:

   ```text
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install the Python dependencies:

   ```text
   pip install -r requirements.txt
   ```

3. Install the frontend dependencies if you need to compile the stylesheets:

   ```text
   npm install
   ```

4. Apply the database migrations:

   ```text
   python manage.py migrate
   ```

5. Start the development server:

   ```text
   python manage.py runserver
   ```

6. Open `http://127.0.0.1:8000/` in a browser. To create an administrator account for `/admin/`, run `python manage.py createsuperuser`.

The SCSS source can be compiled with:

```text
npx sass recipes/static/recipes/scss/styles.scss recipes/static/recipes/css/styles.css
```

## Additional Information for Staff

The application uses SQLite for local development and stores uploaded images in the local `media/` directory. In a production deployment, the Django secret key, debug setting, allowed hosts, database, and media storage should be configured through environment-specific settings rather than the development defaults in `project/settings.py`.

Most recipe actions that change data require authentication and use Django CSRF protection. Recipe editing and deletion are restricted to the recipe owner. Saving, rating, commenting, pantry updates, shopping-list actions, and cookbook access require a logged-in user. The rating and saved-recipe models enforce one record per user and recipe at the database level.

The project's intended demonstration path is: register an account, create or browse a recipe, save a recipe to the cookbook, add ingredients to the pantry, choose "I want to cook this", and review the generated shopping list. The public search and cookbook search are separate: the home page searches all recipes, while the cookbook search only searches recipes owned by or saved by the current user.

