from django.db import models

class ChessGame(models.Model):
    GAME_STATUSES = (
        ('O', 'Over'),
        ('A', 'Active'),
    )
    
    game_key = models.CharField(max_length=36, primary_key=True)
    white_player = models.CharField(max_length=36, null=True)
    black_player = models.CharField(max_length=36, null=True)
    fen = models.CharField(max_length=87)
    start_time = models.DateTimeField(auto_now_add=True)
    move_number = models.IntegerField(default=0)
    game_status = models.CharField(max_length=1, choices=GAME_STATUSES)
    
    def __str__(self):
        return self.game_key
    