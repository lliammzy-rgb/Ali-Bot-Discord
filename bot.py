"""
Main Discord Bot file untuk Sambung Kata
"""
import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN, GUILD_ID
from game import GameManager

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
game_manager = GameManager()

@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")

@bot.command(name="start")
async def start_game(ctx, mode: str = "normal"):
    """Mulai game sambung kata. Mode: normal/expert"""
    guild_id = ctx.guild.id
    if game_manager.has_active_game(guild_id):
        await ctx.send("Game sudah berjalan di server ini!")
        return
    if mode not in ["normal", "expert"]:
        await ctx.send("Mode tidak valid! Pilih 'normal' atau 'expert'.")
        return
    game = game_manager.create_game(guild_id, mode)
    game.is_active = True
    await ctx.send(f"Game sambung kata dimulai! Mode: {mode}. Gunakan !join untuk ikut bermain.")

@bot.command(name="join")
async def join_game(ctx):
    """Join game yang sedang berjalan"""
    guild_id = ctx.guild.id
    user = ctx.author
    game = game_manager.get_game(guild_id)
    if not game or not game.is_active:
        await ctx.send("Belum ada game yang berjalan. Gunakan !start untuk memulai.")
        return
    if game.add_player(user.id, user.display_name):
        await ctx.send(f"{user.display_name} berhasil join game!")
    else:
        await ctx.send(f"{user.display_name} sudah join atau slot penuh.")

@bot.command(name="begin")
async def begin_game(ctx):
    """Mulai giliran pertama (setelah semua join)"""
    guild_id = ctx.guild.id
    game = game_manager.get_game(guild_id)
    if not game or not game.is_active:
        await ctx.send("Belum ada game yang berjalan.")
        return
    if len(game.players) < 2:
        await ctx.send("Minimal 2 pemain untuk mulai game.")
        return
    # Pilih kata awal secara acak
    if not game.valid_words:
        await ctx.send("KBBI word list belum tersedia. Tambahkan kbbi_words.txt!")
        return
    first_word = random.choice(list(game.valid_words))
    game.set_current_word(first_word)
    await ctx.send(f"Game dimulai! Kata pertama: **{first_word}**\nGiliran: {game.get_current_player().username}")
    await next_turn(ctx, game)

async def next_turn(ctx, game):
    while game.is_active:
        player = game.get_current_player()
        if not player:
            await ctx.send("Semua pemain telah tereliminasi. Game berakhir.")
            game.is_active = False
            break
        await ctx.send(f"Giliran {player.username}. Jawab dengan !jawab <kata>")
        try:
            def check(m):
                return m.author.id == player.user_id and m.channel == ctx.channel and m.content.startswith("!jawab ")
            msg = await bot.wait_for('message', timeout=game.time_limit, check=check)
            answer = msg.content[7:].strip()
            valid, reason = game.is_valid_answer(answer)
            if valid:
                game.set_current_word(answer)
                points = 10 + (5 if game.mode == "expert" else 0)
                game.add_points_to_player(player.user_id, points)
                await ctx.send(f"✅ {player.username} benar! +{points} poin. Kata berikutnya: {answer}")
                winner = game.check_game_end()
                if winner:
                    result = game.end_game()
                    await ctx.send(f"🏆 Game selesai! Pemenang: {winner.username} dengan {winner.points} poin!")
                    break
                game.next_turn()
            else:
                player.remove_life()
                await ctx.send(f"{reason} {player.username} kehilangan 1 nyawa. Sisa nyawa: {player.lives}")
                if not player.is_alive:
                    await ctx.send(f"{player.username} tereliminasi!")
                game.next_turn()
        except asyncio.TimeoutError:
            player.remove_life()
            await ctx.send(f"⏰ {player.username} tidak menjawab tepat waktu! Kehilangan 1 nyawa. Sisa nyawa: {player.lives}")
            if not player.is_alive:
                await ctx.send(f"{player.username} tereliminasi!")
            game.next_turn()

@bot.command(name="leaderboard")
async def leaderboard(ctx):
    """Tampilkan leaderboard top 10"""
    game = game_manager.get_game(ctx.guild.id)
    if not game:
        await ctx.send("Belum ada data leaderboard.")
        return
    leaderboard = game.get_leaderboard()
    if not leaderboard:
        await ctx.send("Leaderboard kosong.")
        return
    msg = "**Leaderboard Top 10**\n"
    for i, row in enumerate(leaderboard, 1):
        msg += f"{i}. {row['username']} - {row['total_points']} pts, {row['total_wins']} win, Rising Star: {row['rising_star_count']}\n"
    await ctx.send(msg)

@bot.command(name="achievements")
async def achievements(ctx):
    """Tampilkan achievement kamu"""
    from achievements import AchievementManager
    am = AchievementManager()
    user_id = ctx.author.id
    achs = am.get_player_achievements(user_id)
    if not achs:
        await ctx.send("Belum ada achievement yang didapat.")
        return
    msg = "**Achievements kamu:**\n"
    for row in achs:
        msg += f"- {row['achievement_name']}\n"
    await ctx.send(msg)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
