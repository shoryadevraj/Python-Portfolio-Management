import discord
from discord.ext import commands, tasks
import asyncio
import re
from datetime import datetime
import pytz
from database import client
from utils import open_account, pvc_coin
import traceback

# ================== LEADERBOARD CONFIG ==================
LB_CHANNEL_ID = 1320424654493450343
LB_COMMAND = "||$lb"

LOG_CHANNEL_ID = 1319342922218340373
CASINO_ANNOUNCE_CHANNEL_ID = 1319174028677615616

CASINO_BOT_ID = 356950275044671499  # <-- PUT CASINO BOT ID HERE

ROLE_FIRST_EXTRA = 1371117898357280788
ROLE_TEAM_LEADER = 1344363582288035963
ROLE_TEAM_A = 1371117119244075069
ROLE_TEAM_B = 1371117166795161650
ROLE_TEAM_C = 1468518291915149470

ROLES_TO_CLEAR = [
    1371117898357280788, # ROLE_FIRST_EXTRA Supreme
    1371117119244075069, # ROLE_TEAM_A
    1371117166795161650, # ROLE_TEAM_B
    1468518291915149470, # ROLE_TEAM_C
    1347599882264907847, # Maverick
    1344363582288035963, # Team Leader
    1347599610138464258, # Tycoon
]

LB_RETRY_DELAY = 4  # seconds
LB_MAX_RETRIES = 3

IST = pytz.timezone("Asia/Kolkata")


class CasinoAuto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.leaderboard_pending = False
        self.leaderboard_retries = 0
        self.leaderboard_task = None
        self.last_lb_run_date = None


    async def log_event(self, msg: str):
        print(msg)
        try:
            ch = self.bot.get_channel(LOG_CHANNEL_ID)
            if not ch:
                ch = await self.bot.fetch_channel(LOG_CHANNEL_ID)
            if ch:
                await ch.send(msg)
        except Exception:
            pass

    async def request_leaderboard(self):
        if self.leaderboard_pending:
            return

        channel = self.bot.get_channel(LB_CHANNEL_ID)
        if not channel:
            return

        self.leaderboard_pending = True
        self.leaderboard_retries = 0

        await self.log_event("📊 Leaderboard triggered")
        await channel.send(LB_COMMAND)

        self.leaderboard_task = asyncio.create_task(self.wait_for_leaderboard())

    async def wait_for_leaderboard(self):
        await asyncio.sleep(LB_RETRY_DELAY)

        if self.leaderboard_pending:
            self.leaderboard_pending = False
            await self.log_event("❌ Leaderboard timeout (no casino embed)")

    async def process_leaderboard(self, message: discord.Message, is_special_reset: bool = False):
        if not self.leaderboard_pending:
            return

        self.leaderboard_pending = False

        if self.leaderboard_task:
            self.leaderboard_task.cancel()
            self.leaderboard_task = None

        await self.log_event("✅ Leaderboard received")

        guild = message.guild
        embed = message.embeds[0]
        print(embed)

        text = ""

        if embed.description:
            text += embed.description

        for field in embed.fields:
            text += f"\n{field.value}"

        user_ids = re.findall(r'https://unb\.gg/lb/\d+/(\d+)', text)

        print(f"Extracted User IDs: {user_ids}")
        

        if len(user_ids) < 3:
            await self.log_event("⚠️ Not enough users in leaderboard")
            return
        top3 = []
        for i in user_ids:
            if len(top3)<3:
                if guild.get_member(int(i)):
                    
                    top3.append(i)
                else:
                    try:
                        fetched_member = await guild.fetch_member(int(i))
                        if fetched_member:
                            top3.append(i)
                    except Exception as e:
                        pass
            else:
                break
        print(f"Top 3 User IDs: {top3}")

        first = guild.get_member(int(top3[0]))
        second = guild.get_member(int(top3[1]))
        third = guild.get_member(int(top3[2]))

        if not all([first, second, third]):
            await self.log_event("⚠️ Failed to resolve members")
            return

        # ===== CLEAR OLD ROLES =====
        for member in guild.members:
            remove_roles = [
                guild.get_role(r)
                for r in ROLES_TO_CLEAR
                if guild.get_role(r) and guild.get_role(r) in member.roles
            ]
            if remove_roles:
                await member.remove_roles(*remove_roles, reason="Sunday leaderboard reset")
    
        # ===== ASSIGN NEW ROLES TO WINNERS =====
        if is_special_reset:
            # For !start_creset2
            await first.add_roles(
                guild.get_role(ROLE_FIRST_EXTRA),
                guild.get_role(ROLE_TEAM_LEADER),
                reason="Special Reset - 1st Place",
            )
            # 2nd and 3rd get no roles
        else:
            # Original behavior for !start_casinoreset
            await first.add_roles(
                guild.get_role(ROLE_FIRST_EXTRA),
                guild.get_role(ROLE_TEAM_A),
                guild.get_role(ROLE_TEAM_LEADER),
                reason="Sunday Winner",
            )

            await second.add_roles(
                guild.get_role(ROLE_TEAM_B),
                guild.get_role(ROLE_TEAM_LEADER),
                reason="Sunday 2nd Place",
            )

            await third.add_roles(
                guild.get_role(ROLE_TEAM_C),
                guild.get_role(ROLE_TEAM_LEADER),
                reason="Sunday 3rd Place",
            )

        # ===== RENAME TEAM ROLES =====
        bot_top_role = guild.me.top_role

        role_names = {
            ROLE_TEAM_A: "Team A",
            ROLE_TEAM_B: "Team B",
            ROLE_TEAM_C: "Team C",
        }

        for role_id, new_name in role_names.items():
            role = guild.get_role(role_id)

            if not role:
                continue

            if role.managed or role >= bot_top_role:
                await self.log_event(f"⚠️ Skipped rename: {role.name}")
                continue

            if role.name != new_name:
                await role.edit(name=new_name, reason="Sunday leaderboard rename")
                await self.log_event(f"✏️ Renamed role → {new_name}")

        # ===== AWARD AUI PAWS TO TEAM LEADER ROLE =====
        try:
            if is_special_reset:
                add_amt = 100000
            else:
                add_amt = 60000

            tl_role = guild.get_role(ROLE_TEAM_LEADER)
            added_count = 0
            if tl_role:
                for member in tl_role.members:
                    if member.bot:
                        continue
                    try:
                        await self.log_event(f"ℹ️ Awarding {add_amt} PVC to {member} ({member.id})")
                        bal = await client.db.fetchrow('SELECT * FROM users WHERE id = $1 AND guild_id = $2', member.id, guild.id)
                        if bal is None:
                            await open_account(guild.id, member.id)
                        await client.db.execute('UPDATE users SET pvc = pvc + $1 WHERE id = $2 AND guild_id = $3', add_amt, member.id, guild.id)
                        added_count += 1
                    except Exception as e:
                        tb = traceback.format_exc()
                        await self.log_event(f"⚠️ Failed to add PVC to {member} ({member.id}): {e}\n{tb}")

            try:
                lb_ch = self.bot.get_channel(LB_CHANNEL_ID)
                if not lb_ch:
                    lb_ch = await self.bot.fetch_channel(LB_CHANNEL_ID)
                icon = pvc_coin(guild.id)[0]
                if lb_ch:
                    await lb_ch.send(f"{icon} Added {add_amt} AUI PAWS to Team Leader role ({added_count} members).")

                # Announcement
                try:
                    ann_ch = self.bot.get_channel(CASINO_ANNOUNCE_CHANNEL_ID)
                    if not ann_ch:
                        ann_ch = await self.bot.fetch_channel(CASINO_ANNOUNCE_CHANNEL_ID)
                    if ann_ch and tl_role:
                        gambler_role_id = 1319190561793642496
                        role_mention = f"<@&{gambler_role_id}>"

                        top1 = first.mention if first else "Unknown"
                        top2 = second.mention if second else "Unknown"
                        top3 = third.mention if third else "Unknown"

                        if is_special_reset:
                            announce_msg = (
                                f"What is up {role_mention}\n"
                                "NEW WEEKLY LEADERS \n"
                                "Congratulations to our top performers on the casino leaderboard!\n\n"
                                f"{top1} - Securing the top spot! You've won the exclusive <@&{ROLE_FIRST_EXTRA}> role, **₹500**, and 100K AUI Paws!\n"
                                f"{top2} - **₹300** + 100K AUI Paws!\n"
                                f"{top3} - **₹200** + 100K AUI Paws!\n"
                                "ㅤ\n"
                                "Team AUI"
                            )
                        else:
                            # Modified announcement as per your request - no "Additionally"
                            announce_msg = (
                                f"What is up {role_mention}\n"
                                "NEW WEEKLY LEADERS \n"
                                "Congratulations to our top performers on the casino leaderboard!\n\n"
                                f"{top1} - Securing the top spot, you've won the exclusive <@&{ROLE_FIRST_EXTRA}> role and 60K AUI Paws + ₹500!\n"
                                f"{top2} - 60K AUI Paws + ₹300!\n"
                                f"{top3} - 60K AUI Paws + ₹200!\n"
                                "ㅤ\n"
                                "Team AUI"
                            )
                        await ann_ch.send(announce_msg)
                except Exception:
                    pass
            except Exception:
                pass

            await self.log_event(f"💰 Added {add_amt} AUI PAWS to Team Leader role ({added_count} members).")
        except Exception as e:
            tb = traceback.format_exc()
            await self.log_event(f"⚠️ Error while awarding AUI PAWS: {e}\n{tb}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bots (except casino bot)
        if message.author.bot and message.author.id != CASINO_BOT_ID:
            return

        # ================= MANUAL RESET TRIGGER =================
        if (
            message.author.id == 1085648138808852551
            and message.channel.id == 1319342922218340373
        ):
            content = message.content.strip().lower()

            if content == "!start_casinoreset":
                if self.leaderboard_pending:
                    await message.channel.send("⚠️ Casino reset already in progress.")
                    return

                await self.log_event("🚀 Casino reset manually triggered")
                await self.request_leaderboard()
                return

            elif content == "!start_creset2":
                if self.leaderboard_pending:
                    await message.channel.send("⚠️ Casino reset already in progress.")
                    return

                await self.log_event("🚀 Special Casino reset (creset2) manually triggered")
                self.special_reset_pending = True
                await self.request_leaderboard()
                return

        # ================= LEADERBOARD RESPONSE =================
        if message.author.id != CASINO_BOT_ID:
            return

        if message.channel.id != LB_CHANNEL_ID:
            return

        if not self.leaderboard_pending:
            return

        if not message.embeds:
            return

        # Check if this was triggered by !start_creset2
        is_special = getattr(self, 'special_reset_pending', False)
        if is_special:
            self.special_reset_pending = False

        await self.process_leaderboard(message, is_special_reset=is_special)


async def setup(bot: commands.Bot):
    cog = CasinoAuto(bot)
    cog.special_reset_pending = False  # Initialize the flag
    await bot.add_cog(cog)
