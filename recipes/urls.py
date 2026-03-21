from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("new_recipe/", views.new_recipe, name="new_recipe"),
    path("profile/<int:user_id>", views.profile, name="profile"),
    path("follow", views.follow, name="follow"),
    path("pantry/", views.pantry, name="pantry"),
    path("pantry/<int:item_id>/update/", views.pantry_update, name="pantry_update"),
    path("pantry/<int:item_id>/delete/", views.pantry_delete, name="pantry_delete"),
    path('recipe/<int:recipe_id>/', views.recipe, name='recipe'),
]
