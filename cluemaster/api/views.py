from rest_framework.response import Response
from rest_framework.decorators import api_view
from game.models import Room
from .serializers import RoomSerializer

@api_view(['GET'])
def getData(request):
    rooms = rooms.objects.all()
    serializer = RoomSerializer(rooms, many=True)
    return Response(serializer.data)