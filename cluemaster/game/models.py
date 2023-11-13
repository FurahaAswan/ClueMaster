from django.db import models
from django.contrib.auth.models import User
from shortuuid.django_fields import ShortUUIDField

class Room(models.Model):
    id = ShortUUIDField(
        length=8,
        max_length=40,
        primary_key=True,
    )
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    rounds = models.PositiveIntegerField()
    guess_time = models.PositiveIntegerField()
    max_players = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

class Player(models.Model):
    name = models.CharField(max_length=50)
    score = models.PositiveIntegerField(default=0)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    is_host = models.BooleanField(default=False)

class Round(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    clue_master = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='rounds_as_cluemaster')
    word = models.CharField(max_length=255)
    time_left = models.IntegerField()

    def __str__(self):
        return f"Round in {self.room.name} with Cluemaster {self.clue_master.name}"

class Clue(models.Model):
    text = models.CharField(max_length=255)
    specificity_level = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=False)
    game_round = models.ForeignKey(Round, on_delete=models.CASCADE)

