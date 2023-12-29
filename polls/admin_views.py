import datetime
import json
import re
from abc import ABC
from html.parser import HTMLParser

import requests
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect, reverse, get_object_or_404

from polls.models import Game, Poll, Tag, GameTag


class HTMLFilter(HTMLParser, ABC):
    """
    A simple no dependency HTML -> TEXT converter.
    Usage:
          str_output = HTMLFilter.convert_html_to_text(html_input)
    """

    def __init__(self, *args, **kwargs):
        self.text = ""
        self.in_body = False
        super().__init__(*args, **kwargs)

    def handle_data(self, data):
        self.text += data

    @classmethod
    def convert_html_to_text(cls, html: str) -> str:
        f = cls()
        html = html.replace("<br>", "\n").replace("\t", "")
        f.feed(html)
        return re.sub(r"\s+", " ", f.text.strip())


def is_superuser(user):
    return user.is_superuser


@login_required
def game_add(request):
    if not request.user.is_superuser:
        raise PermissionDenied()

    if request.method == "POST":
        # Get data from the POST request
        name = request.POST.get("name")
        steam_id = request.POST.get("steam_id")
        description = request.POST.get("description")
        alt_url = request.POST.get("alt_url")
        logo_url = request.POST.get("logo_url")

        # Create a new Game object and save it to the database
        game = Game(
            name=name,
            steam_id=steam_id,
            description=description,
            alt_url=alt_url,
            logo_url=logo_url,
        )
        game.save()

        # Redirect to the "games/" page upon successful submission
        return redirect(reverse("game_list"))
    return render(request, "polls/game_add.html")


@login_required
def game_edit(request, game_id):
    if not request.user.is_superuser:
        raise PermissionDenied()

    if request.method == "POST":
        # Get data from the POST request
        # name = request.POST.get("name")
        # steam_id = request.POST.get("steam_id")
        # description = request.POST.get("description")
        # alt_url = request.POST.get("alt_url")
        # logo_url = request.POST.get("logo_url")

        # Create a new Game object and save it to the database
        game = Game.objects.get(id=game_id)
        for _ in ("name", "steam_id", "description", "alt_url", "logo_url"):
            val = request.POST.get(_)
            setattr(game, _, val)

        game.save()

        # Redirect to the "games/" page upon successful submission
        return redirect(reverse("game_list"))
    game = get_object_or_404(Game, game_id)

    return render(request, "polls/game_add.html", {"game": game})


@login_required
def game_list(request):
    if not request.user.is_superuser:
        raise PermissionDenied()

    paginator = Paginator(Game.objects.all(), 10, allow_empty_first_page=True)
    page_no = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_no)

    return render(
        request, "polls/game_list.html", context={"games": page_obj, "can_edit": False}
    )


@login_required
def game_import(request):
    if not request.user.is_superuser:
        raise PermissionDenied()

    if request.method == "POST":
        game_id = int(request.POST.get("steam_id", -1))
        if game_id == -1:
            return HttpResponseRedirect(reverse("game_list"))

        has_game = Game.objects.filter(id=game_id).count() > 0
        if has_game:
            return HttpResponseRedirect(reverse("game_list"))

        game_data = requests.get(
            "https://store.steampowered.com/api/appdetails", params=dict(appids=game_id)
        ).json()

        if not game_data[str(game_id)].get("success", False):
            return HttpResponseRedirect(reverse("game_list"))

        game_data = game_data[str(game_id)]["data"]

        try:
            game = Game.objects.get(steam_id=game_id)
        except Game.DoesNotExist:
            game = Game(
                name=game_data["name"],
                steam_id=game_id,
                description=HTMLFilter.convert_html_to_text(
                    game_data["short_description"]
                ),
                alt_url=f"https://store.steampowered.com/app/{game_id}",
                logo_url=game_data.get("header_image", None),
                small_logo_url=game_data.get(
                    "capsule_imagev5", game_data["capsule_image"]
                ),
            )
            game.save()

        for tag_ in game_data["genres"]:
            try:
                this_tag = Tag.objects.get(id=tag_["id"])
            except Tag.DoesNotExist:
                this_tag = Tag()
                this_tag.id = tag_["id"]
                this_tag.name = tag_["description"]
                this_tag.save()

            game_tag = GameTag()
            game_tag.game = game
            game_tag.tag = this_tag
            game_tag.save()

        return HttpResponseRedirect(reverse("game_list"))

    return render(request, "polls/game_import.html")


@login_required
def poll_add(request):
    if not request.user.is_superuser:
        raise PermissionDenied()

    if request.method == "POST":
        data = json.loads(request.body)
        poll = Poll()
        poll.anonymous = data["anonymous"]
        poll.start_date = datetime.datetime.fromisoformat(data["start_date"])
        poll.end_date = datetime.datetime.fromisoformat(data["end_date"])
        poll.title = data["title"]
        poll.save()

        for game_id in data["selectedIds"]:
            poll.games.add(Game.objects.get(steam_id=game_id))

        poll.save()

        return HttpResponse(reverse("poll_list"))

    return render(request, "polls/poll_add.html", context={"games": Game.objects.all()})


@login_required
def poll_toggle_lock(request, poll_id):
    if not request.user.is_superuser:
        raise PermissionDenied()

    try:
        poll = Poll.objects.get(id=poll_id)
    except Poll.DoesNotExist:
        return HttpResponseRedirect(reverse("poll_list"))

    if request.method == "POST":
        poll.closed = not poll.closed
        poll.save()
        return HttpResponseRedirect(reverse("poll_list"))

    return render(
        request,
        "polls/poll_toggle_lock.html",
        context={
            "poll_title": poll.title,
            "poll_id": poll.id,
            "action": "Unlock" if poll.closed else "Lock",
        },
    )


@login_required
def poll_detailed_stats(request, poll_id):
    if not request.user.is_superuser:
        raise PermissionDenied()

    poll = get_object_or_404(Poll, pk=poll_id)
    keys = ["login", "owl", "bee", "cheese"]
    res = []

    for game in poll.games.all():
        keys.append(game.name)

    for vote in poll.vote_set:
        tmp = {}
        tmp["login"] = vote.person.first_name
        for k in ("owl", "bee", "cheese"):
            tmp[k] = "✅" if getattr(vote, k) else "❌"
        for gamevote in vote.gamevote_set:
            tmp[gamevote.game.name] = gamevote.rating if gamevote.rating > 0 else "👎"

        res.append(tmp)

    return render(
        request, "polls/vote_details.html", {"keys": res[0].keys(), "results": res}
    )
