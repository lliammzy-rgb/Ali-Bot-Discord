"""
Configuration untuk Discord Bot Sambung Kata
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Discord Bot Token
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

# Game Configuration
MAX_PLAYERS = 10
PLAYER_LIVES = 3
NORMAL_MODE_TIME = 20  # seconds
EXPERT_MODE_TIME = 18  # seconds
NORMAL_MODE_WIN_POINTS = 100
EXPERT_MODE_WIN_POINTS = 200
EXPERT_MODE_BONUS = 5  # points

# Database
DATABASE_FILE = "game_data.db"

# KBBI Dictionary (will be loaded from external source or built-in list)
VALID_WORDS_FILE = "kbbi_words.txt"
