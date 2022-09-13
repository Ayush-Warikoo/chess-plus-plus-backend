# chat/consumers.py
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import ChessGame


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        game = None;
        print(self.channel_name)
        
        # If game does not exist, create it and add the player to the white side
        if not ChessGame.objects.filter(game_key=self.room_name).exists():
            game = ChessGame(game_key=self.room_name,
                             fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                             game_status='A',
                             white_player=self.channel_name)
            game.save()
        # If game exists, add player to black side
        elif ChessGame.objects.get(game_key=self.room_name).black_player is None:
            game = ChessGame.objects.get(game_key=self.room_name)
            game.black_player = self.channel_name
            game.save()
            
        # Join room group (white, black, or spectator)
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        
        if game is None:
            game = ChessGame.objects.get(game_key=self.room_name)
        
        role = 'spectator'
        if game.black_player and self.channel_name == game.black_player:
            role = 'b'
        elif game.white_player and self.channel_name == game.white_player:
            role = 'w'
        
        print(role, game.fen)
        # send current position to player
        self.send(text_data=json.dumps({
            'type': 'join_game',
            # 'type': 'game_join',
            'role': role,
            'message': game.fen,
        }))

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
        game.game_status = 'O'
        game.save()
    
        # Send message to WebSocket
        # self.send(text_data=json.dumps(event))
