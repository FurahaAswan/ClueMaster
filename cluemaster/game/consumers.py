import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from .models import Room, Player, Clue, Round
import asyncio

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.player_id = self.scope['url_route']['kwargs']['player_id']
        self.room_group_name = f"room_{self.room_id}"

        room = await self.get_room()
        player = await self.get_player()

        if not (player and room):
            await self.accept()
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.handle_join_room()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        #Delete player from db
        player = await self.get_player()
        if player:
            await database_sync_to_async(player.delete)()
            print("delete player")


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
            

    # Handle player guess
    async def handle_guess(self, guess_text):
        room = await self.get_room()
        player = await self.get_player()
        current_round = await self.get_current_round(room)

        if room and player and current_round:
            # Check if the guess is correct
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
                    'id': player.id
                }
            )

    # Send guess to room group
    async def guess(self, event):
        print('sending guess')
        await self.send(text_data=json.dumps({
            'type': 'guess',
            'text': event['text'],
            'player_name': event['player_name'],
            'is_correct': event['is_correct'],
            'id': event['id'],
        }))

    # Handle timer
    async def handle_timer(self):
        room = await self.get_room()
        player = await self.get_player()
        current_round = await self.get_current_round(room)

        if room and player:
            # Broadcast the initial timer value to the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'update_timer',
                    'time': current_round.time_left,
                    'start_timer': True,  # Add a flag to indicate starting the timer
                }
            )
    
    async def update_timer(self,event):
       asyncio.ensure_future(self.update_timer_helper(event))

    # Separate coroutine to update the timer
    async def update_timer_helper(self, event):
        room = await self.get_room()
        current_round = await self.get_current_round(room)

        time_remaining = current_round.time_left

        start_timer = event.get('start_timer', False)

        if start_timer:
            # If the timer is starting, send the initial timer value to the player
            await self.send(text_data=json.dumps(
                {
                    'type': 'timer_update',
                    'value': time_remaining,
                }
            ))

        while time_remaining > 0:
            # Broadcast the timer updates to the room, including the new player
            await self.send(text_data=json.dumps(
                {
                    'type': 'timer_update',
                    'value': time_remaining,
                }
            ))

            # Sleep for 1 second before the next update
            await asyncio.sleep(1)

            # Decrement the time remaining
            current_round.time_left -= 1
            await database_sync_to_async(current_round.save)()
            time_remaining -= 1
        
    
    async def handle_join_room(self):
        room = await self.get_room()
        current_round = await self.get_current_round(room)
        player = await self.get_player()
        clues = await self.get_clues(current_round)

        if current_round:
            word_to_guess = ''
            for letter in current_round.word:
                if letter != ' ':
                    word_to_guess += '_ '
                else:
                    word_to_guess += '  '

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_join',
                    'name': player.name,
                    'id': player.id,
                    'clues': clues,
                    'word_to_guess': word_to_guess
                }
            )

            if current_round.time_left < room.guess_time and current_round.time_left > 0:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'update_timer',
                        'time': current_round.time_left,
                    }
                )
        
        # Broadcast the list of all players to the room
        await self.broadcast_players()
            
    
    async def player_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_join',
            'name': event['name'],
            'id': event['id'],
            'clues': event['clues'],
            'word_to_guess': event['word_to_guess']
        }))
    
    async def broadcast_players(self):
        room = await self.get_room()

        if room:
            player_list = await self.get_all_players(room)

            # Notify all clients in the room about the updated player list
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_list',
                    'players': player_list,
                }
            )

    # Add the player_list method to send the updated player list to clients
    async def player_list(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_list',
            'players': event['players'],
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
    def get_clues(self, current_round):
        if current_round:
            clues = Clue.objects.filter(game_round=current_round.id)
            clues = [clue.text for clue in clues]
            return clues
        return None
    
    @sync_to_async
    def get_all_players(self, room):
        players =  Player.objects.filter(room=room)
        player_list = []

        for player in players:
            player_list.append({'id': player.id, 'player_name': player.name, 'score': player.score})

        return player_list
                     

        