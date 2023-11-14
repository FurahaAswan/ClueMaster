import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from .models import Room, Player, Clue, Round
import asyncio
import random
import bot.bot as bot


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.player_id = self.scope['url_route']['kwargs']['player_id']
        self.room_group_name = f"room_{self.room_id}"

        self.room = await self.get_room()
        self.player = await self.get_player()
        self.host = await self.get_host()
        self.players = await self.get_all_players()
        self.current_round = await self.get_current_round()
        self.clues = await self.get_clues()

        if not (self.player and self.room):
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

        if not self.host:
            await self.select_host()

    async def disconnect(self, close_code):
        #Delete player from db
        if self.player:
            await database_sync_to_async(self.player.delete)()
            if self.player.is_host and len(self.players) > 1:
                await self.select_host()

        if len(self.players) == 1:
            await database_sync_to_async(self.room.delete)()
            await self.close()
        elif len(self.players) > 1:
            await self.update_game_state()
            await self.channel_layer.group_send(
            self.room_group_name, {
                'type': 'player_leave',
                'name': self.player.name
            })
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
    async def player_leave(self, event):
        # Send game state to the connected clients
        await self.send(text_data=json.dumps({
            'type': 'player_leave',
            'name': event['name']
        }))


    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']

        print(data)

        if message_type == 'guess':
            await self.handle_guess(data['text'])
        elif message_type == 'chat_message':
            await self.handle_chat_message(data['text'])
        elif message_type == "start_game":
            await self.start_game()
    
    async def start_game(self):
        #self.words = await bot.get_words(self.room.category, self.room.rounds)
        self.words = ['worxd' for round in range(self.room.rounds)]
        #self.words = json.loads(self.words)

        print(self.words)
        i = 1

        for word in self.words:
            print('Iteration', i)
            await self.handle_round(word)
            i += 1

    async def handle_round(self, word_to_guess):
        # Mark the current active round as inactive
        if self.current_round:
            self.current_round.is_active = False
            await database_sync_to_async(self.current_round.save)()

        # Create a new round
        await database_sync_to_async(Round.objects.create)(
            word=word_to_guess, 
            time_left=self.room.guess_time, 
            room=self.room,
        )
        
        self.current_round = await self.get_current_round()
        print('Current round', self.current_round)

        await self.update_game_state()
        await self.handle_timer()

    # Handle timer
    async def handle_timer(self):
        print('handle_timer')
        if self.room and self.player and self.current_round:
            # Broadcast the initial timer value to the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'update_timer',
                    'time': self.current_round.time_left,
                }
            )
    
    async def update_timer(self,event):
       print('update_timer')
       asyncio.ensure_future(self.update_timer_helper(event))

    # Separate coroutine to update the timer
    async def update_timer_helper(self, event):
        time_remaining = self.current_round.time_left

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
            self.current_round.time_left -= 1
            await database_sync_to_async(self.current_round.save)()
            time_remaining -= 1      

    # Handle player guess
    async def handle_guess(self, guess_text):
        if self.room and self.player:
            # Check if the guess is correct
            is_correct = False

            if self.current_round:
                current_word = self.current_round.word

                if guess_text.lower() == current_word.lower():
                    is_correct = True
                    self.player.score += 1
                else:
                    is_correct = False

            # Broadcast the guess to the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'guess',
                    'text': guess_text,
                    'player_name': self.player.name,
                    'is_correct': is_correct,
                    'id': self.player.id
                }
            )

    # Send guess to room group
    async def guess(self, event):
        await self.send(text_data=json.dumps({
            'type': 'guess',
            'text': event['text'],
            'player_name': event['player_name'],
            'is_correct': event['is_correct'],
            'id': event['id'],
        }))  
    
    async def handle_join_room(self):
        player = await self.get_player()

        await self.update_game_state()
        
        await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_join',
                    'id': self.player.id,
                    'name': self.player.name
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
        new_host = random.choice(self.players)
        new_host = await database_sync_to_async(Player.objects.get)(id = new_host['id'])
        new_host.is_host = True
        await database_sync_to_async(new_host.save)()

        await self.update_game_state()
    
    async def update_game_state(self):
        self.host = await self.get_host()
        self.players = await self.get_all_players()
        self.current_round = await self.get_current_round()

        word_to_guess = ''
        if self.current_round:
            for letter in self.current_round.word:
                if letter != ' ':
                    word_to_guess += '_ '
                else:
                    word_to_guess += '  '

        # Send the game state to the player
        await self.channel_layer.group_send(
                self.room_group_name,
        {
            'type': 'game_state',
            'player_name': self.player.name if self.player else None,
            'player_id': self.player.id if self.player else None,
            'is_host': self.player.is_host if self.player else False,
            'round_active': self.current_round.is_active if self.current_round else False,
            'word_to_guess': word_to_guess,
            'clues': self.clues,
            'players': await self.get_all_players(),
            'host': {'id': self.host.id, 'name': self.host.name} if self.host else None,
            'timer': self.current_round.time_left if self.current_round else 0,
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
    def get_current_round(self):
        try:
            return Round.objects.get(room=self.room, is_active=True)
        except Round.DoesNotExist:
            return None

    @database_sync_to_async
    def get_clues(self):
        try:
            if self.current_round:
                clues = Clue.objects.filter(game_round=self.current_round.id)
                clues = [clue.text for clue in clues]
                return clues
            return []
        except Clue.DoesNotExist:
            return []
    
    @database_sync_to_async
    def get_all_players(self):
        try:
            players =  Player.objects.filter(room=self.room)
            player_list = []

            for player in players:
                player_list.append({'id': player.id, 'player_name': player.name, 'score': player.score})

            return player_list
        except Player.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_host(self):
        try:
            room = Room.objects.get(id=self.room_id)
            return Player.objects.get(room=room, is_host=True)
        except Player.DoesNotExist:
            return None
                     

        