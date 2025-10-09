
import os
import sys
import pprint
import asyncio
import platform
import logging
import datetime
import traceback
from pathlib import Path


DISCORD_PUBLISH = (
    "R:/pipeline/networkInstall/python_shares/"
    "python311_deadline_discord_pkgs/Lib/site-packages"
)
if not DISCORD_PUBLISH in sys.path:
    sys.path.insert(0, DISCORD_PUBLISH)

import bs4

from dotenv import load_dotenv

import discord
from discord.utils import get

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

DISCORD_MAX_FILL_SIZE = 10240000
DISCORD_MAX_TEXT_SIZE = 1023
DISCORD_MAX_EMBED_TILE = 3

DISCORD_SERVER_PUBLISH = "Deadline"
DISCORD_CHANNEL_PUBLISH = "daily_report"

LOG_DIR = 'R:/logs/daily_reports'
LOG = None

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)


def setupLog(usdfile: str):
    """Setup LOG basic config.

    Args:
        usdfile (str): USD path.
    """
    global LOG
    global LOG_FILE
    
    basename = os.path.basename(usdfile)
    name = os.path.splitext(basename)[0]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    logname = sorted(Path(LOG_DIR).glob(f'log_{name}_*.log'))
    
    if logname:
        LOG_FILE = logname[0]
    else:
        logfilename = f"log_{name}_{timestamp}.log"
        LOG_FILE = os.path.join(LOG_DIR, logfilename)

    os.makedirs(LOG_DIR, exist_ok=True)
    
    LOG = logging.getLogger(__name__)
    LOG.setLevel(logging.INFO)

    LOG.propagate = False

    if LOG.hasHandlers():
        LOG.handlers.clear()

    file_handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    LOG.addHandler(stream_handler)
    LOG.addHandler(file_handler)


def format_array(array: list[str], width=4) -> str:
    formatted_str = ""
    for i, text in enumerate(array):
        formatted_str += text
        not_last_element = i+1 < len(array)
        if (i+1)%width == 0 and not_last_element:
            formatted_str += "\n"
        elif not_last_element:
            formatted_str += ' - '
    formatted_str.rstrip('\n')
    if len(formatted_str) > DISCORD_MAX_TEXT_SIZE:
        formatted_str = formatted_str[:DISCORD_MAX_TEXT_SIZE-10]
        formatted_str += '\n ...'
    return formatted_str


def parseHTMLReport(html_report: str) -> list:
    LOG.info(f"HTML Report: {html_report}")
    LOG.info("Start parsing...")
    file = open(html_report)
    soup = bs4.BeautifulSoup(file, 'html.parser')
    file.close()
    stat_divs: list = soup.find_all("div", {"class": "stat-card"})
    stats = []
    for div in stat_divs:
        stats.append(div.getText().strip().split("\n"))
    LOG.info(f"Parse ended\n{pprint.pformat(stats)}")
    return stats


@client.event
async def on_ready():
    try:
        # Check if the name of the config file is given
        if len(sys.argv) != 2: 
            raise Exception(
                "Bad arguments number. format : "
                "</path/to/publish_daily_report.py> "
                "</path/to/report.html>"
            )
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        setupLog(f'daily_report_{timestamp}')
        
        html_report = sys.argv[1]
        if not os.path.exists(html_report):
            LOG.error(f"Daily Report do not exists\n - {html_report}")
            return

        stats = parseHTMLReport(html_report)

        for guild in client.guilds:
            if guild.name != DISCORD_SERVER_PUBLISH:
                continue
            LOG.info(f'Found guild {guild.name}')
            for channel in guild.channels:
                if (not isinstance(channel, discord.TextChannel)
                    or channel.name != DISCORD_CHANNEL_PUBLISH):
                    continue
                LOG.info(f'Found channel {channel.name}')
                    
                embed = discord.Embed(color=discord.Color.from_rgb(80,80,255))
                embed.add_field(
                    name="Daily Report",
                    value=timestamp,
                    inline=False)
                for stat in stats:
                    embed.add_field(
                        name=stat[0],
                        value=stat[1],
                        inline=True)
                for i in range(len(stats) // DISCORD_MAX_EMBED_TILE):
                    embed.add_field(
                        name="\u200b",
                        value="\u200b",
                        inline=True)
                embed.add_field(
                    name="Full report here",
                    value=f"`{Path(html_report).as_posix()}`",
                    inline=False)

                # Send the embed
                await channel.send(embed=embed)
                LOG.info('Message sent')
    except Exception as e:
        setupLog('DISCORD_BOT_DIDNTLAUCH')
        LOG.warning(f'Could not launch discord bot:\n{e}')
        LOG.warning(str(traceback.format_exc()))
        await client.close()
    await client.close()


if __name__ == "__main__":
    client.run(TOKEN)