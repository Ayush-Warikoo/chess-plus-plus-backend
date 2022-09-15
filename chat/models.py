from django.db import models
from django.contrib.auth.models import User

class ChessGame(models.Model):
    GAME_STATUSES = (
        ('O', 'Open'),
        ('A', 'Active'),
        ('D', 'Draw'),
        ('W', 'White Won'),
        ('B', 'Black Won'),
    )
    
    game_key = models.CharField(max_length=36, primary_key=True)
    # can do current_user.white_player_games.all() to get all games where current_user white white
    white_player = models.ForeignKey(User, related_name='white_player_games', on_delete=models.SET_NULL, null=True)
    white_rating = models.IntegerField(default=1200)
    white_time_left = models.IntegerField(null=True)
    black_player = models.ForeignKey(User, related_name='black_player_games', on_delete=models.SET_NULL, null=True)
    black_rating = models.IntegerField(default=1200)
    black_time_left = models.IntegerField(null=True)
    fen = models.CharField(max_length=87)
    start_time = models.DateTimeField(auto_now_add=True)
    move_number = models.IntegerField(default=0)
    game_status = models.CharField(max_length=1, choices=GAME_STATUSES)
    
    
    def __str__(self):
        return self.game_key
    