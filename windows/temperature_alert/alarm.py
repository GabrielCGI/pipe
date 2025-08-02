import sys

packages_path = "R:/pipeline/pipe/windows/temperature_alert/.venv/Lib/site-packages"

if not packages_path in sys.path:
    sys.path.append(packages_path)

from xsense import XSense
from xsense import House
from xsense import Device

USERNAME = r"hello@illogicstudios.com"
PASSWORD = r"tempWithIllogic2025!"
WEBHOOK_URL = "https://discordapp.com/api/webhooks/1399665319437406299/YoZVuUiBAb0K7QKiBj0IUDn96FDCHNAZTagCd09KBUWmsLU_3--Xc3zp_7Mfg1Ub-pEd"
MAGICIEN_ID = "1209436104231489608"
SORCIER_ID = "1234813073882222592"

try:
    from discord_webhook import DiscordWebhook
    DISCORD_ENABLE = True
except:
    DISCORD_ENABLE = False


def send_message(msg):
    if DISCORD_ENABLE:
        webhook = DiscordWebhook(url=WEBHOOK_URL, content=msg)
        webhook.execute()
    else:
        print(msg)


def getRoomData(house: House, device: Device):
    rooms: list[dict] = house.rooms
    room_id = device.room_id
    for room in rooms:
        id = room.get('roomId')
        if id == room_id:
            return room
    return {}
        

def check_temperature(api: XSense):
    for _, house in api.houses.items():
        for _, station in house.stations.items():
            api.get_station_state(station)
            api.get_state(station)

    for _, h in api.houses.items():
        for _, station in h.stations.items():
            for _, device in station.devices.items():
                temperature = device.data.get('temperature', None)
                threshold = device.data.get('temperatureRange', None)
                if temperature is None or threshold is None:
                    continue
                if temperature >= threshold[1]:
                    room_data = getRoomData(house, device)
                    room_name = room_data.get('roomName')
                    msg = ""
                    msg += f"Alerte :fire: : <@&{MAGICIEN_ID}> <@&{SORCIER_ID}> "
                    if room_name is not None:
                        msg += f"La température dans la pièce **{room_name.title()}**"
                    else:
                        msg += f"La température de **{device.name}** (pièce introuvable)"
                    msg += f" est de **{temperature:.1f}°C** "
                    msg += f"et dépasse le seuil **{threshold[1]}°C**"
                    send_message(msg)
                

if __name__ == '__main__':
    api = XSense()
    api.init()
    api.login(USERNAME, PASSWORD)
    api.load_all()

    check_temperature(api)
