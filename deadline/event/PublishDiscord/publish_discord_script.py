
import os
import re
import sys
import requests
import json
import asyncio
import platform

import discord
from discord.utils import get

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    try:
        # Check if the name of the config file is given
        if len(sys.argv) != 2: raise Exception("Bad arguments number. format : <path_to_this_script> <config_message_file>")
        with open(sys.argv[1], "r") as tmp:
            datas = json.loads(tmp.read())

        # Retrieve datas
        job_name = datas["job_name"]
        frames = datas["frames"]
        comment = datas["comment"]
        error = datas["error_count"]
        submit_time = datas["submit_time"]
        end_time = datas["end_time"]
        avg_time = datas["avg_time"]
        render_time = datas["render_time"]
        video = datas["video"]
        username = datas["user"]
        description = "**\""+datas["description"]+"\"**"
        server_pub = datas["server_pub"]
        channel_pub = datas["channel_pub"]

        user = None
        for guild in client.guilds:
            if guild.name != server_pub: continue
            for member in guild.members:
                if member.name == username:
                    user = member
                    break

            user_none = user is None
            for channel in guild.channels:
                if not isinstance(channel, discord.TextChannel) or channel.name != channel_pub: continue

                # Send the video
                if video is not None:
                    msg = await channel.send(file=discord.File(video))
                    video_url = msg.attachments[0].url
                    description+=f"\n\n[Dowload the MOV here]({video_url})"
                else:
                    description+="\n\n*No preview available*"

                # Create an embed with all the datas
                embed = discord.Embed(color=discord.Color.from_rgb(80,80,255))
                embed.add_field(name="Job Name", value=job_name, inline=False)
                if not user_none:
                    embed.add_field(name="User", value=user.mention, inline=True)
                    embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="Render Time", value=render_time, inline=True)
                embed.add_field(name="Submit Time", value=submit_time, inline=True)
                embed.add_field(name="Average Time", value=avg_time, inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="End Time", value=end_time, inline=True)
                embed.add_field(name="Frames", value=frames, inline=not user_none)
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(name="Error", value=error, inline=True)
                if len(comment)>0:
                    embed.add_field(name="Comment", value=comment, inline=False)

                embed.add_field(name="\u200b", value=description, inline=False)

                # Send the embed
                await channel.send(embed=embed)
    except:
        await client.close()
    await client.close()

client.run('PUT DISCORD BOT TOKEN HERE')
