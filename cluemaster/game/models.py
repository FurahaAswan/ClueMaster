from django.db import models
from django.contrib.auth.models import User
from shortuuid.django_fields import ShortUUIDField
from channels.db import database_sync_to_async

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
    category = models.CharField(max_length=50)

    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'

    DIFFICULTY_CHOICES = (
        (EASY, 'Easy'),
        (MEDIUM, 'Medium'),
        (HARD, 'Hard'), 
    )

    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES, default="easy")

class Player(models.Model):
    name = models.CharField(max_length=50)
    score = models.PositiveIntegerField(default=0)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    is_host = models.BooleanField(default=False)

class Round(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    word = models.CharField(max_length=255)
    time_left = models.IntegerField()

    async def get_room(self):
        return await database_sync_to_async(lambda: self.room.id)()

    def __str__(self):
        return f"Round in {self.get_room()}"

class Clue(models.Model):
    text = models.CharField(max_length=255)
    specificity_level = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=False)
    game_round = models.ForeignKey(Round, on_delete=models.CASCADE)

