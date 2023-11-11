import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Room, Player, Clue, Guess, Round

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"game_{self.room_id}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']

        if message_type == 'guess':
            await self.handle_guess(data['text'])
        elif message_type == 'chat_message':
            await self.handle_chat_message(data['text'])

    # Handle player guess
    async def handle_guess(self, guess_text):
        room = await self.get_room()
        player = await self.get_player()

        if room and player:
            # Check if the guess is correct
            current_round = await self.get_current_round(room)
            current_clue = await self.get_current_clue(current_round)

            if current_clue and guess_text.lower() == current_clue.text.lower():
                is_correct = True
                player.score += 1
            else:
                is_correct = False

            # Save the guess
            guess = Guess.objects.create(text=guess_text, is_correct=is_correct, player=player, clue=current_clue)

            # Broadcast the guess to the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'guess',
                    'text': guess_text,
                    'player_username': player.user.username,
                    'is_correct': is_correct,
                }
            )

    # Handle chat messages
    async def handle_chat_message(self, message_text):
        room = await self.get_room()
        player = await self.get_player()

        if room and player:
            # Broadcast the chat message to the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'text': message_text,
                    'player_username': player.user.username,
                }
            )

    # Send guess to room group
    async def guess(self, event):
        await self.send(text_data=json.dumps({
            'type': 'guess',
            'text': event['text'],
            'player_username': event['player_username'],
            'is_correct': event['is_correct'],
        }))

    # Send chat message to room group
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'text': event['text'],
            'player_username': event['player_username'],
        }))

    # Helper functions to get room, player, current round, and current clue
    @sync_to_async
    def get_room(self):
        try:
            return Room.objects.get(id=self.room_id)
        except Room.DoesNotExist:
            return None

    @sync_to_async
    def get_player(self):
        user = self.scope['user']
        try:
            return Player.objects.get(user=user)
        except Player.DoesNotExist:
            return None

    @sync_to_async
    def get_current_round(self, room):
        try:
            return Round.objects.get(room=room, is_active=True)
        except Round.DoesNotExist:
            return None

    @sync_to_async
    def get_current_clue(self, current_round):
        if current_round:
            return current_round.current_clue
        return None
