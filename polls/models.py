from django.contrib.auth.models import User
from django.db import models
from django.db.models import OneToOneField


class Game(models.Model):
    name = models.CharField(max_length=255)
    steam_id = models.IntegerField()
    description = models.TextField()
    alt_url = models.URLField(max_length=255)
    logo_url = models.URLField(max_length=255, blank=True, null=True)
    small_logo_url = models.URLField(max_length=255, blank=True, null=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} (#{self.steam_id})"


class Poll(models.Model):
    title = models.CharField(max_length=255, unique=True, default="FILLME")
    games = models.ManyToManyField(Game, related_name="games")
    start_date = models.DateTimeField()
    closed = models.BooleanField(default=False)
    anonymous = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    person = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    owl = models.BooleanField(default=False)
    bee = models.BooleanField(default=False)
    cheese = models.BooleanField(default=False)
    weight = models.IntegerField(default=1)

    def __str__(self):
        return f"Vote of {self.person.username} in poll {self.poll.title}"


class GameVote(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    rating = models.IntegerField()
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)


class PollBlock(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    person = models.ForeignKey(User, on_delete=models.CASCADE)


class TwitchUser(models.Model):
    user = OneToOneField(User, on_delete=models.CASCADE)
    subscribed = models.BooleanField(default=False)
    twitch_user_id = models.IntegerField(default=-1)

    def __str__(self):
        return f"{self.user.username}@{self.twitch_user_id}"


class Tag(models.Model):
    name = models.CharField(max_length=255)


class GameTag(models.Model):
    game = models.ForeignKey(Game, on_delete=models.DO_NOTHING)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
