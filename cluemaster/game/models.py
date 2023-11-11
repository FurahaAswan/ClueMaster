from django.db import models
from django.contrib.auth.models import User
import shortuuid

class Room(models.Model):
    id = models.CharField(primary_key=True, default=shortuuid.uuid, editable=False, max_length=22)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    rounds = models.PositiveIntegerField()
    guess_time = models.PositiveIntegerField()
    max_players = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)

class Clue(models.Model):
    text = models.CharField(max_length=255)
    specificity_level = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

class Guess(models.Model):
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    clue = models.ForeignKey(Clue, on_delete=models.CASCADE)

class Round(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    cluemaster = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='rounds_as_cluemaster')
    current_clue = models.OneToOneField(Clue, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Round in {self.room.name} with Cluemaster {self.cluemaster.user.username}"

