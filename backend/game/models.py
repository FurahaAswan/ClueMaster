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
    name = models.CharField(max_length=50, default='Unnamed Room')
    created_at = models.DateTimeField(auto_now_add=True)
    rounds = models.PositiveIntegerField(default=2)
    guess_time = models.PositiveIntegerField(default=60)
    max_players = models.PositiveIntegerField(default=2)
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=50, default='General Knowledge (Math, Science, Art, Sports, etc.)')

    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'
    PAIN = 'pain'
    EXPERT = 'expert'

    DIFFICULTY_CHOICES = (
        (EASY, 'Easy'),
        (MEDIUM, 'Medium'),
        (HARD, 'Hard'),
        (EXPERT, 'Expert'),
        (PAIN, 'Pain'), 
    )

    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES, default="medium")

    def __str__(self):
        return f"{self.name}(s) Room"


class Player(models.Model):
    name = models.CharField(max_length=50)
    score = models.PositiveIntegerField(default=0)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    is_host = models.BooleanField(default=False)
    is_correct = models.BooleanField(default=False)

class Round(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    word = models.CharField(max_length=255)
    time_left = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    async def get_room_guess_time(self):
        return await database_sync_to_async(lambda: self.room.guess_time)()

    def save(self, *args, **kwargs):
        if not self.time_left:
            # Set the default value for time_left based on the room's guess_time
            self.time_left = self.get_room_guess_time()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Round in {self.room}"

class Clue(models.Model):
    text = models.CharField(max_length=255)
    specificity_level = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=False)
    game_round = models.ForeignKey(Round, on_delete=models.CASCADE)

