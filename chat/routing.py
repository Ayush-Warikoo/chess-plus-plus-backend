# chat/routing.py
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # w+ will match any string made of alphanumeric or _ characters
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
