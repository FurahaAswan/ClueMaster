import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Room, Guess

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = 'chat%s' % self.room_id
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name, 
            {
                'type': 'tester_message', 
                'tester': 'data'
            }
        )

    async def receive(self, text_data):
        # Receive message from WebSocket (front end)
        text_data_json = json.loads(text_data)
        type = text_data_json['type']
        message = text_data_json['content']

        if type == 'guess':
                new_message = await self.create_message(sender, message)

                # Send message to group / ticket
                await self.channel_layer.group_send(
                        self.room_group_name, {
                            'type': 'guess',
                            'content': message,
                            'sender': {'id': str(sender.id), 'name': sender.name},
                        }
                    )
    
    async def tester_message(self, event):
        tester = event['tester']
        await self.send(text_data=json.dumps({
            'tester':tester,
        }))

    async def guess(self, event):

        await self.send(text_data=json.dumps({
            'type': event['type'],
            'content': event['content'],
            'sender': event['sender'],
        }))
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    @sync_to_async
    def get_room(self):
        self.room = Room.objects.get(id=self.room_id)

    @sync_to_async
    def create_guess(self, sender, guess):
        guess = Guess.objects.create(text=guess, player=sender, room = self.room)
        
        self.ticket.guesss.add(guess)

        return guess