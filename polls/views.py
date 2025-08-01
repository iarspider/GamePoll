import copy
import json
import re
from collections import defaultdict
from itertools import combinations
from operator import itemgetter

from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, redirect

from GamePoll import settings
from polls.models import TwitchUser, Poll, Vote, GameVote, Game, PollBlock


# Special views


def index(request):
    return redirect("login" if not settings.DEBUG else "dev_login")


@login_required
def poll_list(request):
    if request.user.is_superuser:
        paginator = Paginator(
            Poll.objects.order_by("-id").all(), 10, allow_empty_first_page=True
        )
    else:
        paginator = Paginator(
            Poll.objects.exclude(status="finished", pollblock__person=request.user)
            .order_by("-id")
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


def dev_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/accounts/profile")  # Redirect to home or dashboard
        else:
            return HttpResponse("Invalid credentials", status=401)

    return render(request, "polls/dev_login.html")


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

    if poll.status != "active":
        return render(request, "polls/poll_locked.html")

    if PollBlock.objects.filter(person=request.user, poll=poll).count() > 0:
        return render(
            request, "polls/second_vote_attempt.html", context={"id": poll_id}
        )

    try:
        twitch_user = TwitchUser.objects.get(user=request.user)
    except TwitchUser.DoesNotExist:
        twitch_user = None

    if request.method == "POST":
        data = json.loads(request.body)
        try:
            poll = Poll.objects.get(id=poll_id)
        except Poll.DoesNotExist:
            return HttpResponse(f"Poll with id {poll_id} not found", status=400)

        if poll.status != "active":
            return HttpResponse(f"Poll with id {poll_id} is closed", status=400)

        # Validation
        s1 = set(data["game_order"])
        s2 = set(int(x) for x in data["game_states"].keys())
        s3 = set(x.id for x in poll.games.all())

        if not (s1 == s2 and s2 == s3):
            return HttpResponse(
                f"Mismatch between game_order, game_states and poll_games", status=400
            )

        vote = Vote()
        vote.poll = poll
        if poll.anonymous:
            vote.person = None
        else:
            vote.person = request.user
        vote.owl = data["owl_checkbox"]
        vote.bee = data["bee_checkbox"]
        vote.cheese = data["cheese_checkbox"]
        vote.sub_vote = twitch_user.subscribed

        vote.save()

        lock = PollBlock()
        lock.person = request.user
        lock.poll = poll
        lock.save()

        for i, game_id in enumerate(reversed(data["game_order"])):
            game_vote = GameVote()
            game_vote.vote = vote
            game_vote.game = Game.objects.get(id=game_id)
            game_vote.rating = (i + 1) if data["game_states"][str(game_id)] else -1

            game_vote.save()

        return redirect("vote_ok")

    return render(
        request,
        "polls/vote_add.html",
        context={
            "poll": poll,
            "is_sub": False,  # (twitch_user and twitch_user.subscribed) or settings.DEBUG,
        },
    )


@login_required
def poll_vote_ok(request):
    return render(request, "polls/vote_ok.html")


def login_redirect(request):
    return redirect("login", permanent=True)


@login_required()
def poll_stats(request, poll_id):
    def schulze(data) -> tuple[list[int], bool]:
        d: dict[tuple[int, int], float] = defaultdict(float)
        p: dict[tuple[int, int], float] = defaultdict(float)
        games_set: set[int] = set()

        for ranking in data:
            for (A, a_score, a_weight), (B, b_score, b_weight) in combinations(
                ranking, 2
            ):
                games_set.update([A, B])
                if a_score > b_score:
                    d[(A, B)] += a_weight
                elif a_score < b_score:
                    d[(B, A)] += b_weight

        for A, B in combinations(games_set, 2):
            if d[(A, B)] > d[(B, A)]:
                p[(A, B)] = d[(A, B)]
            elif d[(B, A)] > d[(A, B)]:
                p[(B, A)] = d[(B, A)]

        for A in games_set:
            for B in games_set:
                if A == B:
                    continue
                for C in games_set:
                    if C == A or C == B:
                        continue
                    p[(A, B)] = max(p[(A, B)], min(p[(A, C)], p[(C, B)]))

        wins: dict[int, int] = defaultdict(int)

        for A, B in combinations(games_set, 2):
            if p[(A, B)] > p[(B, A)]:
                wins[A] += 1
            elif p[(B, A)] > p[(A, B)]:
                wins[B] += 1

        for G in games_set.difference(copy.copy(list(wins.keys()))):
            wins[G] = 0

        wins = dict(sorted(wins.items(), key=itemgetter(1), reverse=True))

        res_ = list(wins.keys())
        return res_, len(res_) > 1 and wins[res_[0]] == wins[res_[1]]

    if not request.user.is_superuser:
        tmp = (
            Poll.objects.filter(id=poll_id)
            .exclude(pollblock__person=request.user)
            .count()
        )
        if tmp == 0:
            return redirect("poll_list")

    result = {"🦉": "", "🐝": "", "🧀": "", "🗳️": ""}
    poll = Poll.objects.get(id=poll_id)

    votes = Vote.objects.filter(poll=poll)
    data: list[list[tuple[int, int, float]]] = []

    for vote in votes:
        viewer = TwitchUser.objects.get(user=vote.person)

        result["🦉"] += "🦉" * vote.owl
        result["🐝"] += "🐝" * vote.bee
        result["🧀"] += "🧀" * vote.cheese
        result["🗳️"] += "🗳️"

        game_votes = GameVote.objects.filter(vote=vote)
        data.append(
            sorted(
                [
                    (gv.game.id, gv.rating, 1.5 if viewer.subscribed else 1.0)
                    for gv in game_votes
                ],
                key=itemgetter(1),
            )
        )

    for k in copy.copy(tuple(result.keys())):
        if not result[k]:
            result.pop(k)

    res, tie = schulze(data)
    top3_qs = Game.objects.filter(id__in=res[:3])
    top3 = sorted(top3_qs, key=lambda g: res.index(g.id))

    rest_qs = Game.objects.filter(id__in=res[3:])
    rest = sorted(rest_qs, key=lambda g: res.index(g.id))

    return render(
        request,
        "polls/vote_stats.html",
        context={
            "poll_title": poll.title,
            "top3": top3,
            "rest": rest,
            "result": list(result.values()),
            "top_tie": tie,
            "vote_count": votes.count(),
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

    if poll.status != "active":
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

    if poll.status != "active":
        return render(request, "polls/poll_locked.html")

    return render(request, "polls/retract_vote_ok.html", context={"poll": poll})


@login_required
def vote_error(request):
    return render(request, "polls/vote_error.html")
