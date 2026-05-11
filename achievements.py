"""
Achievement system untuk Discord Bot Sambung Kata
"""
from database import GameDatabase

class Achievement:
    """Base achievement class"""
    def __init__(self, achievement_type, name, description):
        self.achievement_type = achievement_type
        self.name = name
        self.description = description

class RisingStarAchievement(Achievement):
    """Rising Star Achievement - Last player alive"""
    def __init__(self):
        super().__init__(
            achievement_type="RISING_STAR",
            name="🌟 Rising Star",
            description="Jadilah pemain terakhir yang hidup dalam permainan"
        )
    
    def check_and_award(self, user_id, survivors):
        """Check if player earned this achievement"""
        if len(survivors) == 1 and user_id == survivors[0]:
            db = GameDatabase()
            db.add_achievement(user_id, self.achievement_type, self.name)
            db.add_rising_star(user_id)
            return True
        return False

class AchievementManager:
    """Manage all achievements"""
    def __init__(self):
        self.achievements = {
            "RISING_STAR": RisingStarAchievement()
        }
        self.db = GameDatabase()
    
    def check_rising_star(self, user_id, survivors):
        """Check for rising star achievement"""
        achievement = self.achievements["RISING_STAR"]
        return achievement.check_and_award(user_id, survivors)
    
    def get_player_achievements(self, user_id):
        """Get all achievements for a player"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT achievement_name FROM achievements
            WHERE user_id = ?
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        return results
