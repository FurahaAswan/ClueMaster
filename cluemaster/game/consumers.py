import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from .models import Room, Player, Clue, Round
import asyncio
import random

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
        room = await self.get_room()
        players = await self.get_all_players(room)

        #Delete player from db
        player = await self.get_player()
        if player:
            await database_sync_to_async(player.delete)()
            if player.is_host and len(players) > 1:
                await self.select_host()

        if len(players) == 1:
            await database_sync_to_async(room.delete)()
            await self.close()
        elif len(players) > 1:
            await self.update_game_state()
        
        
        
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
        elif message_type == "start_round":
            await self.handle_round()
            #await self.handle_timer()
    
    async def handle_round(self):
        room = await self.get_room()
        player = await self.get_player()
        current_round = await self.get_current_round(room)
        
        # Mark the current active round as inactive
        if current_round:
            current_round.is_active = False
            await database_sync_to_async(current_round.save)()

        # Create a new round
        await database_sync_to_async(Round.objects.create)(
            word='Word', 
            time_left=room.guess_time, 
            clue_master=player, 
            room=room
        )
        
        await self.update_game_state()

        await self.handle_timer()

        

    # Handle player guess
    async def handle_guess(self, guess_text):
        room = await self.get_room()
        player = await self.get_player()
        current_round = await self.get_current_round(room)

        if room and player:
            # Check if the guess is correct
            is_correct = False

            if current_round:
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

        if room and player and current_round:
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

        while time_remaining >= 0:
            # Broadcast the timer updates to the room, including the new player
            await self.send(text_data=json.dumps(
                {
                    'type': 'timer_update',
                    'value': time_remaining,
                }
            ))

            if time_remaining == 0:
                break

            # Sleep for 1 second before the next update
            await asyncio.sleep(1)

            # Decrement the time remaining
            current_round.time_left -= 1
            await database_sync_to_async(current_round.save)()
            time_remaining -= 1
        
    
    async def handle_join_room(self):
        player = await self.get_player()
        print(player)

        await self.update_game_state()
        
        await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_join',
                    'id': player.id,
                    'name': player.name
                }
            )   

        await self.handle_timer()
            
    async def player_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_join',
            'name': event['name'],
            'id': event['id'],
        }))

    async def select_host(self):
        print('Selecting new host')
        room = await self.get_room()
        players = await self.get_all_players(room)
        player = await self.get_player()
        host = await self.get_host()
        
        if not host:
            player.is_host = True
            await database_sync_to_async(player.save)()
        else: 
            new_host = random.choice(players)
            new_host = await database_sync_to_async(Player.objects.get)(id = new_host['id'])
            new_host.is_host = True
            await database_sync_to_async(new_host.save)()

        await self.update_game_state()
    
    async def update_game_state(self):
        room = await self.get_room()
        player = await self.get_player()
        current_round = await self.get_current_round(room)
        clues = await self.get_clues(current_round)
        host = await self.get_host()

        word_to_guess = ''
        if current_round:
            for letter in current_round.word:
                if letter != ' ':
                    word_to_guess += '_ '
                else:
                    word_to_guess += '  '

        # Send the game state to the player
        await self.channel_layer.group_send(
                self.room_group_name,
        {
            'type': 'game_state',
            'player_name': player.name if player else None,
            'player_id': player.id if player else None,
            'is_host': player.is_host if player else False,
            'round_active': current_round.is_active if current_round else False,
            'word_to_guess': word_to_guess,
            'clues': clues,
            'players': await self.get_all_players(room),
            'host': {'id': host.id, 'name': host.name} if host else None,
            'timer': current_round.time_left if current_round else 0,
        })
    
    async def game_state(self, event):
        # Send game state to the connected clients
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'player_name': event['player_name'],
            'player_id': event['player_id'],
            'is_host': event['is_host'],
            'round_active': event['round_active'],
            'word_to_guess': event['word_to_guess'],
            'clues': event['clues'],
            'players': event['players'],
            'host': event['host'],
            'timer': event['timer'],
        }))


    # Helper functions to get room, player, current round, and current clue
    @database_sync_to_async
    def get_room(self):
        try:
            return Room.objects.get(id=self.room_id)
        except Room.DoesNotExist:
            return None

    @database_sync_to_async
    def get_player(self):
        try:
            return Player.objects.get(id = self.player_id)
        except Player.DoesNotExist:
            return None

    @database_sync_to_async
    def get_current_round(self, room):
        try:
            return Round.objects.get(room=room, is_active=True)
        except Round.DoesNotExist:
            return None

    @database_sync_to_async
    def get_clues(self, current_round):
        if current_round:
            clues = Clue.objects.filter(game_round=current_round.id)
            clues = [clue.text for clue in clues]
            return clues
        return []
    
    @database_sync_to_async
    def get_all_players(self, room):
        try:
            players =  Player.objects.filter(room=room)
            player_list = []

            for player in players:
                player_list.append({'id': player.id, 'player_name': player.name, 'score': player.score})

            return player_list
        except Player.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_host(self):
        try:
            room = self.get_room()
            return Player.objects.get(room=room, is_host=True)
        except Player.DoesNotExist:
            return None
                     

        