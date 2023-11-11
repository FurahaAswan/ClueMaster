from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Room)
admin.site.register(Player)
admin.site.register(Clue)
admin.site.register(Guess)
admin.site.register(Round)
