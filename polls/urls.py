from django.urls import include, path

from . import views
from . import admin_views

game_patterns = [
    path("", admin_views.game_list, name="game_list"),
    path("add", admin_views.game_add, name="game_add"),
    path("edit/<int:game_id>", admin_views.game_edit, name="game_edit"),
    path("import", admin_views.game_import, name="game_import"),
]

poll_patterns = [
    path("list", views.poll_list, name="poll_list"),
    path("add", admin_views.poll_add, name="poll_add"),
    path(
        "toggle_lock/<int:poll_id>",
        admin_views.poll_toggle_lock,
        name="poll_toggle_lock",
    ),
    path("stats/<int:poll_id>", views.poll_stats, name="poll_stats"),
    path("details/<int:poll_id>", admin_views.poll_detailed_stats, name="poll_details"),
]


urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_redirect),
    path("logout/", views.logout, name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/profile/", views.profile, name="profile"),
    path("game/", include(game_patterns)),
    path("poll/", include(poll_patterns)),
    path("vote/<int:poll_id>", views.poll_vote, name="vote_add"),
    path("vote/ok", views.poll_vote_ok, name="vote_ok"),
]
