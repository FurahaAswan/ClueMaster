import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Player, Clue, Round
import asyncio
import random
import bot.bot as bot
from datetime import timedelta


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.player_id = self.scope['url_route']['kwargs']['player_id']
        self.room_group_name = f"room_{self.room_id}"
        self.game = None
        self.loading = False

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.initialize_game()

        if not self.host:
            await self.select_host()

        await self.handle_join()

        
    async def initialize_game(self):
        self.room = await self.get_room()
        self.player = await self.get_player()
        self.host = await self.get_host()
        self.players = await self.get_all_players()
        self.current_round = await self.get_current_round()
        self.timer = self.current_round.time_left if self.current_round else self.room.guess_time
        self.is_correct = False
        self.clues = await self.get_clues()
        

        if not (self.player and self.room):
            await self.close()
            return
    
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
        self.players = await self.get_all_players()
        #Delete player from db
        if self.player:
            await database_sync_to_async(self.player.delete)()
            if self.player.is_host and len(self.players) > 1:
                await self.select_host()

        if len(self.players) == 1:
            await database_sync_to_async(self.room.delete)()
            if self.game:
                self.game.cancel()
                print('Game Cancelled')
            await self.close()
        elif len(self.players) > 1:
            await self.channel_layer.group_send(
            self.room_group_name, {
                'type': 'player_leave',
                'name': self.player.name
            })
            await self.update_game_state()
        
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

        print('RECIEVED', data)

        if message_type == 'guess':
            await self.handle_guess(data['text'], data['time'])
        elif message_type == 'chat_message':
            await self.handle_chat_message(data['text'])
        elif message_type == "start_game":
            self.game = asyncio.ensure_future(self.game_loop())
        
    
    async def game_loop(self):
        self.loading = True
        await self.send_loading_state()
        self.room = await self.get_room()
        # Ensure only the host can start the game
        if not self.host or self.host.id != self.player.id:
            self.loading = False
            await self.send_loading_state()
            return
        
        trivia_data = await bot.get_words(self.room.category,self.room.rounds, self.room.difficulty)
        print('Words: ', trivia_data)
        trivia_data = json.loads(trivia_data)
        trivia_data = trivia_data['trivia_answers']

        answers = []
        for i in range(self.room.rounds):
            random_word = random.choice(trivia_data)
            if random_word not in answers:
                answers.append(random_word)


        print(f'{self.room.rounds} Words: ', answers)
        for answer in answers:
            # Create a new round
            await self.handle_round(answer)

            #Wait for 10 seconds in between rounds
            await asyncio.sleep(2)
                
        # Game over or any other logic after the rounds
        self.game = None
        
        #set all players to False and reset scoreboard
        for player in self.players:
            player.is_correct = False
            player.score = 0
            await database_sync_to_async(player.save)()
        
        await self.update_game_state()
        print("Game Over")


    async def handle_round(self, word_to_guess):
        self.loading = True
        await self.send_loading_state()
        # Create a new round
        self.current_round = await database_sync_to_async(Round.objects.create)(
            word=word_to_guess, 
            time_left=self.room.guess_time, 
            room=self.room,
        )

        await database_sync_to_async(self.current_round.save)()

        clues = await bot.get_clues(word_to_guess, self.room.category, self.room.difficulty)
        clues = json.loads(clues)
        clues = clues['clues']

        checked_clues = []
        for clue in clues:
            checked_clues.append(clue.replace(word_to_guess, self.build_word_to_guess()))

        clues = checked_clues
        
        print(f'Clues for {word_to_guess}: ', clues)
        #clues = ['Clue 1', 'Clue 2 ', 'Clue 3']
        await database_sync_to_async(Clue.objects.create)(text = clues[0], game_round = self.current_round)

        # Send timer information to the client based on self.room.guess_time
        await self.update_game_state()

        self.loading =  False
        await self.send_loading_state()
        
        for time_left in range(self.current_round.time_left, 0, -1):
            self.current_round.time_left = time_left
            await database_sync_to_async(self.current_round.save)()
            
            time_elapsed = self.room.guess_time - time_left

            #Give a clue every 15 seconds
            if time_elapsed > 0 and time_elapsed%15 == 0 and time_elapsed/15 < len(clues):
                await database_sync_to_async(Clue.objects.create)(text = clues[time_elapsed//15], game_round = self.current_round)
                await self.update_game_state()

            if all(player.is_correct == True for player in self.players):
                self.current_round.is_active = False
                await database_sync_to_async(self.current_round.save)()
                await self.update_game_state()
                break
                
            await asyncio.sleep(1)  # Wait for 1 second
        
        #Set all players to incorrect for next round
        for player in self.players:
            player.is_correct = False
            await database_sync_to_async(player.save)()
        
        self.current_round.is_active = False
        await database_sync_to_async(self.current_round.save)()
        await self.update_game_state()
 

    # Handle player guess
    async def handle_guess(self, guess_text, time):
        if self.room and self.player:
            if self.current_round:
                current_word = self.current_round.word

                if guess_text.lower() == current_word.lower():

                    time_taken = self.room.guess_time - int(self.calculate_expiration_timestamp() - time)
                    time_weight = 0.8
                    order_weight = 0.2

                    max_time = self.room.guess_time  # Maximum time allowed for a guess in seconds
                    normalized_time = max(0, min(1, time_taken / max_time))  # Normalize time between 0 and 1

                    # Calculate the time_bonus as a weighted sum of time and creativity
                    time_bonus = 150 * (time_weight * (1 - normalized_time))

                    total_correct_answers = 1

                    for player in self.players:
                        if player.is_correct:
                            total_correct_answers += 1

                    # Calculate the order_bonus based on the order of correct answers
                    order_bonus = 150 * order_weight * (1 / total_correct_answers)  # Assuming total_correct_answers is the count of correct answers

                    # Add the time_bonus and order_bonus to the player's score
                    player_score = time_bonus + order_bonus


                    self.player.is_correct = True
                    self.player.score += player_score
                    await database_sync_to_async(self.player.save)()
                    await self.update_game_state()
                    await self.send(text_data=json.dumps({
                        'type': 'guess',
                        'text': guess_text,
                        'player_name': self.player.name,
                        'is_correct': True,
                        'id': self.player.id,
                    })) 
                    return

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
        new_host = random.choice(self.players)
        new_host = await database_sync_to_async(Player.objects.get)(id = new_host.id)
        new_host.is_host = True
        await database_sync_to_async(new_host.save)()

        await self.update_game_state()
    
    async def update_game_state(self):
        expiration_timestamp = self.calculate_expiration_timestamp()
        word_to_guess = self.build_word_to_guess()

        # Send the game state to the player
        await self.channel_layer.group_send(
                self.room_group_name,
        {
            'type': 'game_state',
            'word_to_guess': word_to_guess,
            'expiration_timestamp': expiration_timestamp,
        })
    
    def build_word_to_guess(self):
        word_to_guess = ''
        if self.current_round:
            if self.current_round.is_active:
                for letter in self.current_round.word:
                    if letter != ' ':
                        word_to_guess += '_ '
                    else:
                        word_to_guess += '  '
            else:
                word_to_guess = self.current_round.word
        return word_to_guess

    def calculate_expiration_timestamp(self):
        if self.current_round and self.current_round.is_active:
            return int((self.current_round.created_at + timedelta(seconds=self.room.guess_time)).timestamp())
        return None
    
    async def game_state(self, event):
        old_room = self.room
        old_player = self.player
        old_host = self.host
        old_players = self.players
        old_current_round = self.current_round
        old_timer = self.current_round.time_left if self.current_round else self.room.guess_time
        old_is_correct = False
        old_clues = self.clues
        old_game = self.game


        #update game state
        await self.initialize_game()

        if (
            old_room != self.room
            or old_player != self.player
            or old_host == self.host
            or old_players != self.players
            or old_current_round != self.current_round
            or old_timer != self.timer
            or old_is_correct != self.is_correct
            or old_clues != self.clues
            or event['expiration_timestamp'] != self.calculate_expiration_timestamp() 
            or event['word_to_guess'] != self.build_word_to_guess()
            or old_game != self.game
            or self.calculate_expiration_timestamp()
        ):

            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'player_name': self.player.name if self.player else None,
                'player_id': self.player.id if self.player else None,
                'word_to_guess': event['word_to_guess'],
                'clues': self.clues,
                'players': [{'id': player.id, 'player_name': player.name, 'score': player.score} for player in self.players],
                'host': {'id': self.host.id, 'name': self.host.name} if self.host else None,
                'expiration_timestamp': event['expiration_timestamp'],
                'game_active': True if self.game else False,
                'loading_state': self.loading
            }))
        
        return
    
    async def send_loading_state(self):
        await self.channel_layer.group_send(
                self.room_group_name,
        {
            'type': 'loading_state',
            'loading_state': self.loading
        })
    
    async def loading_state(self, event):
        await self.send(text_data=json.dumps({
            'type': 'loading_state',
            'loading_state': event['loading_state']
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
                clues = Clue.objects.filter(game_round=self.current_round)
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
                     

        