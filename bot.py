import discord, os
from discord.ext import commands, tasks
from collections import defaultdict

token = os.getenv("token")

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# Dictionary to store invite counts
invite_tracker = defaultdict(int)
last_top_5_message_id = None
thread_id = 1328120709762908221  # Replace with your thread ID

@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")
    await fetch_invite_counts()
    update_top_5.start()

async def fetch_invite_counts():
    """Fetch all invites in the server and update the tracker."""
    for guild in bot.guilds:
        invites = await guild.invites()
        for invite in invites:
            invite_tracker[invite.inviter.id] += invite.uses

@bot.event
async def on_invite_create(invite):
    """Track new invites created."""
    invite_tracker[invite.inviter.id] += invite.uses

@bot.event
async def on_member_join(member):
    """Track member joins to update invite counts."""
    guild = member.guild
    invites = await guild.invites()
    for invite in invites:
        if invite.uses > invite_tracker[invite.inviter.id]:
            invite_tracker[invite.inviter.id] = invite.uses
            break

def get_top_5():
    """Retrieve the top 5 inviters sorted by invite count."""
    sorted_invites = sorted(invite_tracker.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_invites[:5]
    return [(bot.get_user(user_id), count) for user_id, count in top_5]

@tasks.loop(seconds=30)
async def update_top_5():
    """Update the top 5 inviters leaderboard."""
    global last_top_5_message_id
    top_5 = get_top_5()
    thread = bot.get_channel(thread_id)
    if not thread:
        print(f"Thread with ID {thread_id} not found.")
        return

    leaderboard = "**🏆 Top 5 Inviters 🏆**\n\n"
    for i, (user, count) in enumerate(top_5, start=1):
        leaderboard += f"{i}. {user.mention if user else 'Unknown User'} - **{count} invites**\n"

    if last_top_5_message_id:
        try:
            # Update the existing message
            message = await thread.fetch_message(last_top_5_message_id)
            await message.edit(content=leaderboard)
        except discord.NotFound:
            last_top_5_message_id = None  # If the message is deleted, reset it
    if not last_top_5_message_id:
        # Send a new message if no existing message found
        message = await thread.send(leaderboard)
        last_top_5_message_id = message.id

bot.run(token)
