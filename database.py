"""
Database management untuk leaderboard dan stats pemain
"""
import sqlite3
from datetime import datetime
from config import DATABASE_FILE

class GameDatabase:
    def __init__(self):
        self.db_file = DATABASE_FILE
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table untuk stats pemain
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                total_wins INTEGER DEFAULT 0,
                total_games INTEGER DEFAULT 0,
                total_points INTEGER DEFAULT 0,
                rising_star_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table untuk game history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                winner_id INTEGER,
                winner_name TEXT,
                players TEXT NOT NULL,
                final_points INTEGER,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table untuk achievements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_type TEXT NOT NULL,
                achievement_name TEXT NOT NULL,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_or_update_player(self, user_id, username):
        """Add or update player stats"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO player_stats (user_id, username)
            VALUES (?, ?)
        ''', (user_id, username))
        
        conn.commit()
        conn.close()
    
    def update_player_stats(self, user_id, wins=0, games=0, points=0):
        """Update player statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE player_stats
            SET total_wins = total_wins + ?,
                total_games = total_games + ?,
                total_points = total_points + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (wins, games, points, user_id))
        
        conn.commit()
        conn.close()
    
    def add_achievement(self, user_id, achievement_type, achievement_name):
        """Add achievement to player"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO achievements (user_id, achievement_type, achievement_name)
            VALUES (?, ?, ?)
        ''', (user_id, achievement_type, achievement_name))
        
        conn.commit()
        conn.close()
    
    def save_game_history(self, mode, winner_id, winner_name, players, final_points):
        """Save game history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO game_history (mode, winner_id, winner_name, players, final_points)
            VALUES (?, ?, ?, ?, ?)
        ''', (mode, winner_id, winner_name, ",".join(players), final_points))
        
        conn.commit()
        conn.close()
    
    def get_leaderboard(self, limit=10):
        """Get top players leaderboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, total_wins, total_games, total_points, rising_star_count
            FROM player_stats
            ORDER BY total_points DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_player_stats(self, user_id):
        """Get specific player stats"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM player_stats WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result
    
    def add_rising_star(self, user_id):
        """Add rising star count to player"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE player_stats
            SET rising_star_count = rising_star_count + 1
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
