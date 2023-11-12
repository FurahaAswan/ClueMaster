from rest_framework.response import Response
from rest_framework.decorators import api_view
from game.models import Room
from .serializers import RoomSerializer, PlayerSerializer

@api_view(['POST'])
def createRoom(request):
    serializer = RoomSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    print(serializer.errors)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def joinRoom(request, room_id):
    room = Room.objects.get(id=room_id)
    request.data['room'] = room.id
    player_serializer = PlayerSerializer(data=request.data)
    
    if player_serializer.is_valid():
        player_serializer.save()

        return Response(player_serializer.data)

    return Response(player_serializer.errors, status=400)