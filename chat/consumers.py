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
        self.room_group_name = 'chat_%s' % self.room_name # change to chess
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
        print(text_data_json)

        # single
        if (text_data_json['type'] == 'create_game'):
            self.create_game(text_data_json)
        elif (text_data_json['type'] == 'cancel_game'):
            self.cancel_game(text_data_json)
        # TODO: attach lobby client to user and turn join_game to single
        # elif (text_data_json['type'] == 'join_game'):
        #     self.join_game(text_data_json)
        elif (text_data_json['type'] == 'join_lobby'):
            self.join_lobby(text_data_json)
        else:
            # group
            print('group')
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                text_data_json
            )
    
    # Handlers for different types of messages
    def join_lobby(self, event):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        
        games = ChessGame.objects.filter(game_status='O').values_list('game_key', 'white_player', 'white_rating')
        games = [dict(zip(['key', 'whitePlayer', 'whiteRating'], game)) for game in games]
        # convert player id to username
        for game in games:
            game['whitePlayer'] = User.objects.get(id=game['whitePlayer']).username
        
        print(games)
        self.send(text_data=json.dumps({
            'type': 'join_lobby',
            'games': games,
            'username': event['username']
        }))
    
    def add_lobby_game(self, event):
        print('add lobby game')
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))
    
    def remove_lobby_game(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))
    
    # SINGLE
    def create_game(self, event):
        # set game to open in database
        username = event['username']
        gameKey = event['gameKey']
        if (ChessGame.objects.filter(game_key=gameKey).exists()):
            print("UUID collided, buy a lottery ticket")
            return

        # add elegant handling if user is not logged in
        user = User.objects.get(username=username)
        game = ChessGame(game_key=gameKey,
                             fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                             game_status='O',
                             white_player=user)
        game.save()

        # This might not work
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'add_lobby_game',
                'game': {'key': gameKey, 'whitePlayer': username, 'whiteRating': game.white_rating},
            } #** Might be json.dumps(event)
        )
        # Send message to WebSocket
        # self.send(text_data=json.dumps(event))
        
    def cancel_game(self, event):
        gameKey = event['gameKey']
        if (ChessGame.objects.filter(game_key=gameKey).exists()):
            game = ChessGame.objects.get(game_key=gameKey)
            game.delete()
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'remove_lobby_game',
                'gameKey': gameKey,
            })
        
        
    
    def join_game(self, event):
        # add prefix
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        print('join game')
        
        username = event['username']
        
        # add elegant handling if user is not logged in
        if (not User.objects.filter(username=username).exists()):
            self.send(text_data=json.dumps({
                'type': 'unauthorized',
                'message': 'You are not logged in',
            }))
            return
            
        user = User.objects.get(username=username)
        print(user)
        
        # If game exists, add player to black side
        if ChessGame.objects.get(game_key=self.room_name).black_player is None:
            game = ChessGame.objects.get(game_key=self.room_name)
            game.black_player = user
            game.game_status = 'A'
            game.save()
            
            # TODO: remove game from all lobby group channels
            
        
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
            'username': username,
            'whitePlayer': game.white_player.username,
            'blackPlayer': game.black_player.username,
        }))
        print(event)
        # Send message to WebSocket
        # self.send(text_data=json.dumps(event))
        

    # GROUP
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
        self.send(text_data=json.dumps(event))

