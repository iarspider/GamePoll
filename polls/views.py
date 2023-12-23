import datetime
import json
import re

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import (
    HttpResponse,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.shortcuts import render, redirect, reverse

from polls.models import TwitchUser, Poll, Vote, GameVote, Game, PollBlock
from .forms import LoginForm


# Create your views here.
def index(request):
    return HttpResponse("Hello, world!")


@login_required
def poll_list(request):
    if request.user.is_superuser:
        paginator = Paginator(Poll.objects.all(), 10, allow_empty_first_page=True)
    else:
        gmtnow = datetime.datetime.now(datetime.timezone.utc)
        paginator = Paginator(
            Poll.objects.filter(start_date__lt=gmtnow, closed=False)
            .exclude(pollblock__person=request.user)
            .distinct(),
            10,
            allow_empty_first_page=True,
        )
    page_no = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_no)

    return render(request, "polls/poll_list.html", context={"polls": page_obj})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page.
                return redirect(reverse("poll/list"))
            else:
                # Return an 'invalid login' error message.
                return render(
                    request,
                    "polls/login.html",
                    {"form": form, "error": "Invalid login credentials"},
                )
    else:
        form = LoginForm()

    return render(request, "polls/login.html", {"form": form})


@login_required
def profile(request):
    user = request.user
    user_email = re.sub("[^@.]", "X", user.email)
    try:
        twitch_user = TwitchUser.objects.get(user=user)
    except TwitchUser.DoesNotExist:
        twitch_user = None

    polls = []
    for lock in PollBlock.objects.filter(person=user):
        polls.append(lock.poll.title)

    return render(
        request,
        "polls/index.html",
        context={
            "user": user,
            "twitch_user": twitch_user,
            "email": user_email,
            "polls": polls,
        },
    )


@login_required
def poll_vote(request, poll_id):
    try:
        poll = Poll.objects.get(pk=poll_id)
    except Poll.DoesNotExist:
        return render(request, "polls/poll_not_found.html")

    if PollBlock.objects.filter(person=request.user, poll=poll).count() > 0:
        return render(request, "polls/second_vote_attempt.html")

    if poll.closed:
        return render(request, "polls/poll_locked.html")

    if request.method == "POST":
        data = json.loads(request.body)
        poll = Poll.objects.get(id=poll_id)
        vote = Vote()
        vote.poll = poll
        if poll.anonymous:
            vote.person = None
        else:
            vote.person = request.user
        vote.owl = data["owl_checkbox"]
        vote.bee = data["bee_checkbox"]
        vote.cheese = data["cheese_checkbox"]
        try:
            twitch_user = TwitchUser.objects.get(user=request.user)
        except TwitchUser.DoesNotExist:
            twitch_user = None

        if twitch_user and twitch_user.subscribed:
            vote.weight = 2

        vote.save()

        lock = PollBlock()
        lock.person = request.user
        lock.poll = poll
        lock.save()

        for i, game_id in enumerate(reversed(data["game_order"])):
            game_vote = GameVote()
            game_vote.vote = vote
            game_vote.game = Game.objects.get(steam_id=game_id)
            game_vote.rating = (i + 1) if data["game_states"][str(game_id)] else -1
            game_vote.save()

        return HttpResponseRedirect(reverse("vote_ok"))

    return render(request, "polls/vote_add.html", context={"poll": poll})


@login_required
def poll_vote_ok(request):
    return render(request, "polls/vote_ok.html")


def login_redirect(request):
    return HttpResponsePermanentRedirect(
        reverse("login"),
    )


@login_required()
def poll_stats(request, poll_id):
    if not request.user.is_superuser:
        tmp = (
            Poll.objects.filter(id=poll_id)
            .exclude(pollblock__person=request.user)
            .count()
        )
        if tmp == 0:
            return HttpResponseRedirect(request, reverse("poll_list"))

    result = {}
    result_negative = {}
    poll = Poll.objects.get(id=poll_id)
    for game in poll.games.all():
        result[game.name] = 0
        result_negative[game.name] = 0

    result["🦉"] = 0
    result["🐝"] = 0
    result["🧀"] = 0

    votes = Vote.objects.filter(poll=poll)
    for vote in votes:
        result["🦉"] += vote.owl * vote.weight
        result["🐝"] += vote.bee * vote.weight
        result["🧀"] += vote.cheese * vote.weight
        game_votes = GameVote.objects.filter(vote=vote)
        for game_vote in game_votes:
            if game_vote.rating > 0:
                result[game_vote.game.name] += game_vote.rating + vote.weight
            else:
                result_negative[game_vote.game.name] += vote.weight

    return render(
        request,
        "polls/vote_stats.html",
        context={
            "poll_title": poll.title,
            "result": result.items(),
            "result_negative": result_negative.items(),
        },
    )
