# Generated by Django 5.1.5 on 2025-01-31 15:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("polls", "0007_remove_vote_weight_gamevote_weight"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="gamevote",
            name="weight",
        ),
    ]
