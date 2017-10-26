import discord
import asyncio
from threading import Thread
from discord.ext import commands
from senpai import SENPAI
from secret import token, prefix

description = '''Automated 4chan Cup coverage, live to your Discord server. #BringBackGB'''

bot = commands.Bot(command_prefix=prefix, description=description)
extensions = []

class SENPAIReader:
   # events to ignore for Discord
   nonEvents = set(["Clock Started", "Clock Stopped"])
   allowedTypes = set([discord.ChannelType.text, discord.ChannelType.private, discord.ChannelType.group])

   def __init__ (self, bot):
      self.bot = bot
      self.reader = SENPAI()
      self.active_channels = set([])
      self.homeName = None
      self.awayName = None
      self.homeScore = 0
      self.awayScore = 0
      print("reader initialised")
      bot.loop.create_task(self.read_senpai())

   async def read_senpai(self):
      # wait until bot is ready
      await self.bot.wait_until_ready()
      print("ready for SENPAI")
      # build list of permitted channels by iterating over servers
      for server in bot.servers:
         # get user ID for this specific server
         user = server.get_member(bot.user.id)
         # check all channels in this server
         for channel in server.channels:
            # if we can send messages, and if it's a text channel, add it to the active channel list
            if (user.permissions_in(channel).send_messages) and (channel.type in SENPAIReader.allowedTypes):
               self.active_channels.add(channel.id)
      # while connection is active
      while not self.bot.is_closed:
         event = self.reader.readEvent()
         # log event to console
         print(event)
         # skip events not part of gameplay
         if event.event in SENPAIReader.nonEvents:
            continue
         # teams changed announces next match
         elif event.event == "Teams Changed":
            self.homeName = event.home.teamname
            self.awayName = event.away.teamname
            message = "Up Next: {} vs. {}".format(self.homeName, self.awayName)
         # stats found announces kickoff
         elif event.event == "Stats Found":
            self.homeScore = 0
            self.awayScore = 0
            message = "Kickoff: {} vs. {}".format(self.homeName, self.awayName)
         # stats lost announces game end
         elif event.event == "Stats Lost":
            message = "Final Score: {} {} - {} {}".format(self.homeScore, self.homeName, self.awayScore, self.awayName)
         # goal should update score, and has special mesage
         elif event.event == "Goal":
            # mark down score
            if event.team == "Home":
               self.homeScore += 1
               team = self.homeName
            else:
               self.awayScore += 1
               team = self.awayName
            message = "**Goal!** {} scores for {}".format(event.scorer.name, team)
            if event.assister is not None:
               message += ", assisted by {}.".format(event.assister.name)
            else:
               message += "."
            # wait for goals
            await asyncio.sleep(20)
         # otherwise just print the event
         else:
            message = str(event)
            # after making message, wait 20 seconds for stream delay for in-game events
            await asyncio.sleep(20)
         # send message to all channels
         for channel in self.active_channels:
            try:
               await self.bot.send_message(discord.Object(id=channel), message)
            except Exception as e:
               print("Error on channel ID {}, skipping".format(channel))
               print("error was:", e)

@bot.event
async def on_ready():
   print("Connected to Discord.")
   print(bot.user.name)
   print(bot.user.id)
   reader = SENPAIReader(bot)
   print("-- loading extensions --")
   bot.edit_profile(username="GermanBot")
   for extension in extensions:
      try:
         bot.load_extension(extension)
         print("Successfully loaded extension '{}'".format(extension))
      except Exception as e:
         print("Error loading extension '{}'".format(extension))
         print("{}: {}".format(type(e).__name__, e))
   print("-- beginning log --")

def main ():
   #reader = SENPAIReader(bot)
   while True:
      try:
         bot.run(token)
      except KeyboardInterrupt:
         raise
      except Exception as e:
         print(e)
         continue

if __name__ == '__main__':
   main()