from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, "game/index.html")

def room(request, room_id):
    return render(request, "game/room.html", {
       'room_id': room_id         
    })
