import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Room, Player, Clue, Round
import asyncio

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"room_{self.room_id}"

        if not await self.get_room():
            await self.accept()
            await self.close()
            return

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

        print(data)

        if message_type == 'guess':
            await self.handle_guess(data['text'])
        elif message_type == 'chat_message':
            await self.handle_chat_message(data['text'])
        elif message_type == "start_timer":
            await self.handle_timer()
        elif message_type == 'join_room':
            self.player_id = data['id']
            await self.handle_join_room()

    # Handle player guess
    async def handle_guess(self, guess_text):
        room = await self.get_room()
        player = await self.get_player()

        if room and player:
            # Check if the guess is correct
            current_round = await self.get_current_round(room)
            current_word = current_round.word

            if guess_text.lower() == current_word.lower():
                is_correct = True
                player.score += 1
            else:
                is_correct = False

            # Broadcast the guess to the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'guess',
                    'text': guess_text,
                    'player_name': player.name,
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
                    'player_name': player.user.username,
                }
            )

    # Handle timer
    async def handle_timer(self):
        room = await self.get_room()
        player = await self.get_player()

        if room and player:
            # Broadcast the initial timer value to the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'timer_update',
                    'value': room.guess_time,
                }
            )

            # Use a separate coroutine to update the timer
            await self.update_timer(room.guess_time)

    # Send guess to room group
    async def guess(self, event):
        await self.send(text_data=json.dumps({
            'type': 'guess',
            'text': event['text'],
            'player_name': event['player_name'],
            'is_correct': event['is_correct'],
        }))

    # Send chat message to room group
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'text': event['text'],
            'player_name': event['player_name'],
        }))
    
    # Separate coroutine to update the timer
    async def update_timer(self, time_remaining):
        while time_remaining > 0:
            # Broadcast the timer updates to the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'timer_update',
                    'value': time_remaining,
                }
            )

        # Sleep for 1 second before the next update
        await asyncio.sleep(1)

        # Decrement the time remaining
        time_remaining -= 1
    
    async def handle_join_room(self):
        
        player = await self.get_player()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_join',
                'name': player.name,
                'id': player.id,
            }
        )
    
    async def player_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_join',
            'name': event['name'],
            'id': event['id'],
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
        try:
            return Player.objects.get(id = self.player_id)
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
