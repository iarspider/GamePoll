from django.contrib import admin

# Register your models here.
from .models import Game, Tag, Poll, PollBlock, Vote

# Register your models here.
admin.site.register(Game)
admin.site.register(Tag)
admin.site.register(Poll)
admin.site.register(PollBlock)
admin.site.register(Vote)
