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
        self.timer = 0
        self.is_correct = False

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

        await self.handle_join()

        if not self.host:
            await self.select_host()
    
    async def handle_join(self):
        await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_join',
                    'id': self.player.id,
                    'name': self.player.name
                }
            )
        await self.update_game_state()   
            
    async def player_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_join',
            'name': event['name'],
            'id': event['id'],
        }))

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
        asyncio.ensure_future(self.game_loop())
        
    
    async def game_loop(self):
        # Ensure only the host can start the game
        if not self.host or self.host.id != self.player.id:
            return
        
        #words = ["exampleword", "Lebron James", "Fish"]
        words = await bot.get_words(self.room.category,self.room.rounds, self.room.difficulty)
        words = json.loads(words)
        print('Words: ', words)
        words = words['words']
        #clues = ['Clue 1', 'Clue 2', 'Clue 3']

        for i in range(self.room.rounds):
            clues = await bot.get_clues(words[i], self.room.category, self.room.difficulty)
            clues = json.loads(clues)
            clues = clues['clues']
            print(f'Clues for {words[i]}: ', clues)
            # Generate a random word or retrieve it from an external source
            word_to_guess = words[i]  # Replace this with your word generation logic

            # Create a new round
            await self.handle_round(word_to_guess)
            self.clues = [clues[0]]

            # Send timer information to the client based on self.room.guess_time
            for time_left in range(self.room.guess_time, 0, -1):
                self.timer = time_left
                time_elapsed = self.room.guess_time - time_left

                if time_elapsed > 0 and time_elapsed%15 == 0 and time_elapsed/15 < len(clues):
                    self.clues.append(clues[time_elapsed//15])

                if all(player.is_correct == True for player in self.players):
                    print("All players are correct!")
                    break
                
                await self.update_game_state()
                await asyncio.sleep(1)  # Wait for 1 second

            #Wait for 10 seconds in between rounds
            await asyncio.sleep(10)
                
        # Game over or any other logic after the rounds
        print("Game Over")


    async def handle_round(self, word_to_guess):
        #set all players to False
        for player in self.players:
            player.is_correct = False
            await database_sync_to_async(player.save)()

        if self.current_round:
            # Mark the current active round as inactive
            await database_sync_to_async(self.current_round.delete)()
        # Create a new round
        self.current_round = await database_sync_to_async(Round.objects.create)(
            word=word_to_guess, 
            time_left=self.room.guess_time, 
            room=self.room,
        )

        await self.update_game_state()

        

    # Handle player guess
    async def handle_guess(self, guess_text):
        if self.room and self.player:
            if self.current_round:
                current_word = self.current_round.word

                if guess_text.lower() == current_word.lower():
                    self.player.is_correct = True
                    self.player.score += 1
                    await database_sync_to_async(self.player.save)()

            # Broadcast the guess to the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'guess',
                    'text': guess_text,
                    'player_name': self.player.name,
                    'is_correct': self.player.is_correct,
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

    async def select_host(self):
        print('Selecting new host')   
        new_host = random.choice(self.players)
        new_host = await database_sync_to_async(Player.objects.get)(id = new_host.id)
        new_host.is_host = True
        await database_sync_to_async(new_host.save)()

        await self.update_game_state()
    
    async def update_game_state(self):
        self.host = await self.get_host()

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
            'word_to_guess': word_to_guess,
            'host': {'id': self.host.id, 'name': self.host.name} if self.host else None,
            'timer': self.timer,
            'clues': self.clues,
        })
    
    async def game_state(self, event):
        #update game state
        self.players = await self.get_all_players()
        self.current_round = await self.get_current_round()

        # Send game state to the connected clients
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'player_name': self.player.name if self.player else None,
            'player_id': self.player.id if self.player else None,
            'word_to_guess': event['word_to_guess'],
            'clues': event['clues'],
            'players': [{'id': player.id, 'player_name': player.name, 'score': player.score} for player in self.players],
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
            return Round.objects.get(room=self.room)
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
            return list(players)
        except Player.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_host(self):
        try:
            return Player.objects.get(room=self.room, is_host=True)
        except Player.DoesNotExist:
            return None
                     

        