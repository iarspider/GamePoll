import datetime
import json
import re

from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect

from polls.models import TwitchUser, Poll, Vote, GameVote, Game, PollBlock


# Special views


def index(request):
    return redirect("login")


@login_required
def poll_list(request):
    if request.user.is_superuser:
        paginator = Paginator(Poll.objects.all(), 10, allow_empty_first_page=True)
    else:
        gmtnow = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
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
    if not request.user.is_authenticated:
        return render(
            request,
            "polls/login.html",
        )
    else:
        return redirect("profile")


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
        polls.append(lock.poll)

    return render(
        request,
        "polls/profile.html",
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

        return redirect("vote_ok")

    return render(request, "polls/vote_add.html", context={"poll": poll})


@login_required
def poll_vote_ok(request):
    return render(request, "polls/vote_ok.html")


def login_redirect(request):
    return redirect("login", permanent=True)


@login_required()
def poll_stats(request, poll_id):
    if not request.user.is_superuser:
        tmp = (
            Poll.objects.filter(id=poll_id)
            .exclude(pollblock__person=request.user)
            .count()
        )
        if tmp == 0:
            return redirect("poll_list")

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


@login_required
def logout(request):
    auth_logout(request)
    return redirect("login")


@login_required
def poll_unvote(request, poll_id):
    try:
        poll = Poll.objects.get(pk=poll_id)
    except Poll.DoesNotExist:
        return render(request, "polls/poll_not_found.html")

    if poll.closed:
        return render(request, "polls/poll_locked.html")

    try:
        poll_block = PollBlock.objects.get(person=request.user, poll=poll)
    except PollBlock.DoesNotExist:
        return render(request, "polls/not_voted.html", context={"poll": poll})

    if request.method != "POST":
        return render(request, "polls/retract_vote.html", context={"poll": poll})
    else:
        poll_block.delete()
        Vote.objects.filter(poll=poll, person=request.user).delete()

    return redirect("poll_unvote_ok", poll_id=poll_id)


@login_required
def poll_unvote_ok(request, poll_id):
    try:
        poll = Poll.objects.get(pk=poll_id)
    except Poll.DoesNotExist:
        return render(request, "polls/poll_not_found.html")

    if poll.closed:
        return render(request, "polls/poll_locked.html")

    return render(request, "polls/retract_vote_ok.html", context={"poll": poll})