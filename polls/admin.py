from django.contrib import admin

# Register your models here.
from .models import Game, Tag, Poll, PollBlock, Vote

# Register your models here.
admin.register(Game)
admin.register(Tag)
admin.register(Poll)
admin.register(PollBlock)
admin.register(Vote)
