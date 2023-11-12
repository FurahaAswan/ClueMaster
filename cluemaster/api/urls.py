from django.urls import path
from . import views


urlpatterns = [
    path('room/create/', views.createRoom),
    path('<str:room_id>', views.joinRoom),
]