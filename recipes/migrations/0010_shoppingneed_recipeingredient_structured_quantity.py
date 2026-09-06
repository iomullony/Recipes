import re

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def split_quantity_strings(apps, schema_editor):
    RecipeIngredient = apps.get_model("recipes", "RecipeIngredient")
    pattern = re.compile(r"^\s*([\d.]+)\s*(.*?)\s*$")

    for ri in RecipeIngredient.objects.all():
        raw = (ri.quantity_text or "").strip()
        if not raw:
            continue

        match = pattern.match(raw)
        if match and match.group(1):
            ri.quantity_amount = match.group(1)
            ri.unit = match.group(2)
            ri.save(update_fields=["quantity_amount", "unit"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0009_savedrecipe_delete_liked_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="recipeingredient",
            old_name="quantity",
            new_name="quantity_text",
        ),
        migrations.AddField(
            model_name="recipeingredient",
            name="quantity_amount",
            field=models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True),
        ),
        migrations.AddField(
            model_name="recipeingredient",
            name="unit",
            field=models.CharField(max_length=20, blank=True, default=""),
        ),
        migrations.RunPython(split_quantity_strings, noop_reverse),
        migrations.RemoveField(
            model_name="recipeingredient",
            name="quantity_text",
        ),
        migrations.RenameField(
            model_name="recipeingredient",
            old_name="quantity_amount",
            new_name="quantity",
        ),
        migrations.AlterField(
            model_name="recipeingredient",
            name="unit",
            field=models.CharField(max_length=20, blank=True),
        ),
        migrations.CreateModel(
            name="ShoppingNeed",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)),
                ("unit", models.CharField(max_length=20, blank=True)),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                ("ingredient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shopping_needs", to="recipes.ingredient")),
                ("recipe", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shopping_needs", to="recipes.recipe")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shopping_needs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["ingredient__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="shoppingneed",
            constraint=models.UniqueConstraint(fields=("user", "ingredient", "recipe"), name="unique_user_ingredient_recipe_need"),
        ),
    ]
