from rest_framework.response import Response
from rest_framework.decorators import api_view
from game.models import Room
from .serializers import RoomSerializer

@api_view(['GET'])
def getRoom(request, room_id):
    room = Room.objects.get(id = room_id)
    serializer = RoomSerializer(room, many=False)
    return Response(serializer.data)

@api_view(['POST'])
def createRoom(request):
    serializer = RoomSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response()