# chat/consumers.py
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import ChessGame

# import users
from django.contrib.auth.models import User
from channels.auth import login

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        print(self.scope['user'])

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)

        # Send message to handlers
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            text_data_json
        )
    
    # Handlers for different types of messages
    def join_game(self, event):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        
        username = event['username']
        
        # add elegant handling if user is not logged in
        user = User.objects.get(username=username)
        print(user)
        
        # If game does not exist, create it and add the player to the white side
        if not ChessGame.objects.filter(game_key=self.room_name).exists():
            game = ChessGame(game_key=self.room_name,
                             fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                             game_status='O',
                             white_player=user)
            game.save()
        # If game exists, add player to black side
        elif ChessGame.objects.get(game_key=self.room_name).black_player is None:
            game = ChessGame.objects.get(game_key=self.room_name)
            game.black_player = user
            game.game_status = 'A'
            game.save()
        
        game = ChessGame.objects.get(game_key=self.room_name)
        role = 'spectator'
        if game.black_player and user == game.black_player:
            print('b')
            role = 'b'
        elif game.white_player and user == game.white_player:
            print('w')
            role = 'w'
        
        print(role, game.fen)
        # send current position to player
        self.send(text_data=json.dumps({
            'type': 'join_game',
            'role': role,
            'message': game.fen,
            'username': username
        }))
        print(event)
        # Send message to WebSocket
        # self.send(text_data=json.dumps(event))

    def chess_move(self, event):
        # save new fen to database
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        game = ChessGame.objects.get(game_key=self.room_name)
        game.fen = event['fen']
        game.save()
        
        # Send message to WebSocket
        print('move sent')
        self.send(text_data=json.dumps(event))
        
    def chess_undo(self, event):
        # save new fen to database
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        game = ChessGame.objects.get(game_key=self.room_name)
        game.fen = event['fen']
        game.save()
    
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))
        
    def game_over(self, event):
        # set game to over in database
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        game = ChessGame.objects.get(game_key=self.room_name)
        game.game_status = event['message']
        game.save()
    
        # Send message to WebSocket
        # self.send(text_data=json.dumps(event))

