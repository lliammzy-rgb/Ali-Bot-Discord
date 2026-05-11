"""
Game logic untuk Discord Bot Sambung Kata
"""
import random
import asyncio
from typing import List, Dict, Optional
from config import (
    NORMAL_MODE_TIME, EXPERT_MODE_TIME,
    NORMAL_MODE_WIN_POINTS, EXPERT_MODE_WIN_POINTS,
    EXPERT_MODE_BONUS, PLAYER_LIVES, MAX_PLAYERS
)
from achievements import AchievementManager
from database import GameDatabase

class Player:
    """Represents a player in the game"""
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.points = 0
        self.lives = PLAYER_LIVES
        self.is_alive = True
    
    def add_points(self, points):
        self.points += points
    
    def remove_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.is_alive = False
    
    def roll_word(self):
        """Use a life to roll/skip a word"""
        if self.lives > 0:
            self.lives -= 1
            if self.lives <= 0:
                self.is_alive = False
            return True
        return False
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "points": self.points,
            "lives": self.lives,
            "is_alive": self.is_alive
        }

class GameState:
    """Manages the state of a game"""
    def __init__(self, mode: str, guild_id: int):
        self.mode = mode  # "normal" or "expert"
        self.guild_id = guild_id
        self.players: Dict[int, Player] = {}
        self.current_player_index = 0
        self.current_word = ""
        self.previous_words: List[str] = []
        self.is_active = False
        self.time_limit = EXPERT_MODE_TIME if mode == "expert" else NORMAL_MODE_TIME
        self.win_points = EXPERT_MODE_WIN_POINTS if mode == "expert" else NORMAL_MODE_WIN_POINTS
        self.valid_words = self._load_valid_words()
        self.achievement_manager = AchievementManager()
        self.db = GameDatabase()
    
    def _load_valid_words(self) -> set:
        """Load valid words from KBBI"""
        try:
            with open("kbbi_words.txt", "r", encoding="utf-8") as f:
                return set(word.strip().lower() for word in f.readlines())
        except FileNotFoundError:
            # Default words jika file tidak ada
            return set()
    
    def add_player(self, user_id: int, username: str) -> bool:
        """Add player to game"""
        if len(self.players) >= MAX_PLAYERS:
            return False
        
        if user_id not in self.players:
            self.players[user_id] = Player(user_id, username)
            self.db.add_or_update_player(user_id, username)
            return True
        return False
    
    def remove_player(self, user_id: int) -> bool:
        """Remove player from game"""
        if user_id in self.players:
            del self.players[user_id]
            return True
        return False
    
    def get_player(self, user_id: int) -> Optional[Player]:
        """Get player object"""
        return self.players.get(user_id)
    
    def get_alive_players(self) -> List[Player]:
        """Get list of alive players"""
        return [p for p in self.players.values() if p.is_alive]
    
    def get_current_player(self) -> Optional[Player]:
        """Get current player whose turn it is"""
        alive_players = self.get_alive_players()
        if not alive_players:
            return None
        self.current_player_index = self.current_player_index % len(alive_players)
        return alive_players[self.current_player_index]
    
    def next_turn(self):
        """Move to next player's turn"""
        alive_players = self.get_alive_players()
        if alive_players:
            self.current_player_index = (self.current_player_index + 1) % len(alive_players)
    
    def set_current_word(self, word: str) -> bool:
        """Set the current word"""
        word = word.lower().strip()
        
        # Check if word already used
        if word in self.previous_words:
            return False
        
        # Check if word is valid (optional - only if KBBI loaded)
        if self.valid_words and word not in self.valid_words:
            return False
        
        self.current_word = word
        self.previous_words.append(word)
        return True
    
    def check_word_chain(self, new_word: str, last_syllable: str) -> bool:
        """Check if new word starts with last syllable of previous word"""
        new_word = new_word.lower().strip()
        
        if not new_word or not last_syllable:
            return False
        
        return new_word.startswith(last_syllable.lower())
    
    def is_valid_answer(self, new_word: str) -> tuple[bool, str]:
        """Validate player's answer
        Returns: (is_valid, reason)
        """
        new_word = new_word.lower().strip()
        
        # Check if word already used
        if new_word in self.previous_words:
            return False, "❌ Kata sudah pernah digunakan!"
        
        # Check if word is in KBBI
        if self.valid_words and new_word not in self.valid_words:
            return False, "❌ Kata tidak ditemukan di KBBI!"
        
        # Check word chain (last syllable to first syllable)
        if self.current_word:
            last_syllable = self._get_last_syllable(self.current_word)
            if not self._get_first_syllable(new_word).startswith(last_syllable):
                return False, f"❌ Kata harus dimulai dengan '{last_syllable}'"
        
        return True, "✅ Jawaban benar!"
    
    def _get_last_syllable(self, word: str) -> str:
        """Get last syllable of word (simplified)"""
        word = word.lower()
        # Simple implementation: last 2-3 characters
        if len(word) >= 3:
            return word[-2:]
        return word
    
    def _get_first_syllable(self, word: str) -> str:
        """Get first syllable of word (simplified)"""
        word = word.lower()
        if len(word) >= 2:
            return word[:2]
        return word
    
    def add_points_to_player(self, user_id: int, points: int):
        """Add points to player"""
        player = self.get_player(user_id)
        if player:
            player.add_points(points)
            base_points = points
            if self.mode == "expert":
                base_points = points - EXPERT_MODE_BONUS
            self.db.update_player_stats(user_id, points=base_points)
    
    def eliminate_player(self, user_id: int):
        """Eliminate player from game"""
        player = self.get_player(user_id)
        if player:
            player.is_alive = False
    
    def check_game_end(self) -> Optional[Player]:
        """Check if game has ended, return winner if so"""
        alive_players = self.get_alive_players()
        
        # Check if someone reached win points
        for player in self.players.values():
            if player.points >= self.win_points and player.is_alive:
                return player
        
        # Check if only one player alive
        if len(alive_players) == 1:
            return alive_players[0]
        
        # Check if all players eliminated
        if len(alive_players) == 0:
            return None
        
        return None
    
    def end_game(self) -> Optional[Dict]:
        """End the game and return results"""
        winner = self.check_game_end()
        
        if not winner:
            return None
        
        survivors = [p.user_id for p in self.get_alive_players()]
        
        # Award rising star if applicable
        if len(survivors) == 1:
            self.achievement_manager.check_rising_star(winner.user_id, survivors)
        
        # Update database
        self.db.update_player_stats(
            winner.user_id,
            wins=1,
            games=1,
            points=winner.points
        )
        
        self.db.save_game_history(
            self.mode,
            winner.user_id,
            winner.username,
            [p.username for p in self.players.values()],
            winner.points
        )
        
        self.is_active = False
        
        return {
            "winner": winner,
            "mode": self.mode,
            "players": {uid: p.to_dict() for uid, p in self.players.items()}
        }
    
    def get_leaderboard(self) -> List[Dict]:
        """Get leaderboard"""
        results = self.db.get_leaderboard()
        return [dict(row) for row in results]
    
    def get_game_status(self) -> Dict:
        """Get current game status"""
        return {
            "mode": self.mode,
            "is_active": self.is_active,
            "current_word": self.current_word,
            "time_limit": self.time_limit,
            "win_points": self.win_points,
            "players": {uid: p.to_dict() for uid, p in self.players.items()},
            "current_player": self.get_current_player().to_dict() if self.get_current_player() else None,
            "alive_players_count": len(self.get_alive_players())
        }

class GameManager:
    """Manage multiple game sessions"""
    def __init__(self):
        self.active_games: Dict[int, GameState] = {}  # guild_id -> GameState
    
    def create_game(self, guild_id: int, mode: str) -> GameState:
        """Create new game"""
        game = GameState(mode, guild_id)
        self.active_games[guild_id] = game
        return game
    
    def get_game(self, guild_id: int) -> Optional[GameState]:
        """Get active game for guild"""
        return self.active_games.get(guild_id)
    
    def remove_game(self, guild_id: int):
        """Remove game session"""
        if guild_id in self.active_games:
            del self.active_games[guild_id]
    
    def has_active_game(self, guild_id: int) -> bool:
        """Check if guild has active game"""
        return guild_id in self.active_games and self.active_games[guild_id].is_active
