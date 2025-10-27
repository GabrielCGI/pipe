
import os
import sys
import pprint
import asyncio
import platform
import logging
import datetime
import traceback
from pathlib import Path

from . import loggingsetup

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

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

DISCORD_MAX_FILL_SIZE = 10240000
DISCORD_MAX_TEXT_SIZE = 1023
DISCORD_MAX_EMBED_TILE = 3

DISCORD_SERVER_PUBLISH = "Deadline"
# TODO REMOVE BREAK WHEN IN PROD
DISCORD_CHANNEL_PUBLISH = "daily_report"

_PACKAGE_DIRECTORY = os.path.dirname(__file__)
LOG_DIRECTORY = "R:/logs/daily_reports_logs"
LOG_CONFIG = os.path.join(_PACKAGE_DIRECTORY, "config", "logconfig.json")
logger = None

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)


def setupLog(logname: str):
    """Setup LOG basic config.

    Args:
        logname (str): Log name.
    """
    global logger
    
    logger = logging.getLogger(__name__)
    loggingsetup.setup_log(
        logName=logname,
        logConfigPath=LOG_CONFIG,
        logDirectory=LOG_DIRECTORY
    )

def format_array(array: list[str], width=4) -> str:
    formatted_str = ""
    for i, text in enumerate(array):
        formatted_str += text
        not_last_element = i+1 < len(array)
        if (i+1)%width == 0 and not_last_element:
            formatted_str += "\n"
        elif not_last_element:
            formatted_str += " - "
    formatted_str.rstrip("\n")
    if len(formatted_str) > DISCORD_MAX_TEXT_SIZE:
        formatted_str = formatted_str[:DISCORD_MAX_TEXT_SIZE-10]
        formatted_str += "\n ..."
    return formatted_str


def parseHTMLReport(html_report: str) -> list:
    logger.info(f"HTML Report: {html_report}")
    logger.info("Start parsing...")
    file = open(html_report)
    soup = bs4.BeautifulSoup(file, "html.parser")
    file.close()
    stat_divs: list = soup.find_all("div", {"class": "stat-card"})
    stats = []
    for div in stat_divs:
        stats.append(div.getText().strip().split("\n"))
    logger.info(f"Parse ended\n{pprint.pformat(stats)}")
    return stats


@client.event
async def on_ready():
    try:
        setupLog("daily_report")
        
        # need to import after logger setup to propagate
        from . import deadline_stats_parser

        result = deadline_stats_parser.main()
        if result is None:
            logger.error("Deadline parse failed")
            
        html_report, parser = result
        if not os.path.exists(str(html_report)):
            logger.error(f"Daily Report do not exists\n - {html_report}")
            return

        stats = parseHTMLReport(html_report)
        total_wasted_time = parser.convertIntToTime(
            parser.get_total_wasted_time()
        ).replace("&nbsp;", " ")
        total_jobs = len(parser.jobs)
        total_jobs_with_error = parser.get_total_job_with_error()


        for guild in client.guilds:
            if guild.name != DISCORD_SERVER_PUBLISH:
                continue
            logger.info(f"Found guild {guild.name}")
            for channel in guild.channels:
                if (not isinstance(channel, discord.TextChannel)
                    or channel.name != DISCORD_CHANNEL_PUBLISH):
                    continue
                logger.info(f"Found channel {channel.name}")
                
                logger.debug(f"Send {html_report} to discord")
                await channel.send(file=discord.File(html_report))
                await channel.send(
                    os.path.join("http://serveur:8080",
                    os.path.basename(html_report))
                )

                logger.debug("Start building embed")
                embed = discord.Embed(color=discord.Color.from_rgb(80,80,255))
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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
                    name="Total jobs",
                    value=total_jobs,
                    inline=True
                )
                embed.add_field(
                    name="Total jobs with errors",
                    value=(
                        f"{total_jobs_with_error} \t\t"
                        f"({total_jobs_with_error/total_jobs*100:.02f}%)"
                    ),
                    inline=True
                )
                embed.add_field(
                    name="Total Wasted Time",
                    value=f"**{total_wasted_time}**",
                    inline=False
                )
                embed.add_field(
                    name="Full report here",
                    value=f"`{Path(html_report).as_posix()}`",
                    inline=False)

                # Send the embed
                logger.debug("Send embed")
                await channel.send(embed=embed)
                logger.info("Message sent")
    except Exception as e:
        setupLog("DISCORD_BOT_DIDNTLAUCH")
        logger.warning(f"Could not launch discord bot:\n{e}")
        logger.warning(str(traceback.format_exc()))
        await client.close()
    await client.close()


def publish():
    client.run(TOKEN)
    
if __name__ == "__main__":
    publish()