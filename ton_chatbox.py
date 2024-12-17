import json
import logging
import sys
import threading
import time
from datetime import timedelta
from enum import Enum
from typing import Any
import ctypes

import rel
import requests
import websocket
from pythonosc import udp_client

# Is automatically bumped by release action
_VERSION = "1.1.1"

log = logging.getLogger("ToNChatbox")

# Should never be commited
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s]: %(message)s",
    datefmt="%m-%d-%Y %I:%M:%S",
)

# This code is all horribly made and really unprofessional but in my defense
# I was never intending to release it publicly but here we are.
# If enough interest in this script exists I promise to make it all nice and tidy.
#
# For now it "just works" and that's it.

# CONFIGURABLE VARIABLES
OSC_IP = "127.0.0.1"
OSC_PORT = 9000
# ------------------

# GLOBAL VARIABLES
connection_error_count = 0
ready_to_exit = threading.Event()
# -------------------------------


class ToNRoundType(Enum):
    UNKNOWN = 0
    CLASSIC = 1
    FOG = 2
    PUNISHED = 3
    SABOTAGE = 4
    CRACKED = 5
    BLOODBATH = 6
    DOUBLE_TROUBLE = 7
    EX = 8
    GHOST = 9
    UNBOUND = 10

    MIDNIGHT = 50
    ALTERNATE = 51
    FOG_ALTERNATE = 52
    GHOST_ALTERNATE = 53

    MYSTIC_MOON = 100
    BLOOD_MOON = 101
    TWILIGHT = 102
    SOLSTICE = 103

    RUN = 104
    PAGES = 105
    COLD_NIGHT = 107

    def prettify(self) -> str:
        if self is ToNRoundType.PAGES:
            return "8 Pages"
        if self is ToNRoundType.FOG_ALTERNATE:
            return "Fog (Alternate)"
        if self is ToNRoundType.GHOST_ALTERNATE:
            return "Ghost (Alternate)"

        out = self.name.replace("_", " ")
        return out.title()


# Bit of an awkward solution but works for now
#
# Lisa has ID 18 but I don't currently use IDs.
# Would probably be the smarter move in the future.
#
# Sonics name is just an enrage "variant"
NAME_OVERRIDES: dict[str, str] = {"Sonic?": "Faker", " ": "Lisa"}


class ToNWebsocket:
    def __init__(self):
        # event variables
        self.instance_start: float = time.time()
        self.alive: bool = True
        self.round_active: bool = False
        self.opted_in: bool = False
        self.is_saboteur: bool = False
        self.round_type: ToNRoundType = ToNRoundType.UNKNOWN
        self.location: str = ""
        self.terrors_name: str = ""
        self.terrors_command: int = 255

        # STATS variables
        self.players_online: int = 0
        self.lobby_rounds: int = 0
        self.round_stun_all: int = 0

        # extra variables
        self.players_left: int = 0
        self.terror_history: list = []
        self.enrage_guess: str = ""
        self.last_round: ToNRoundType = ToNRoundType.UNKNOWN

        # count variables
        self.CLASSIC: int = 0
        self.FOG: int = 0
        self.PUNISHED: int = 0
        self.SABOTAGE: int = 0
        self.CRACKED: int = 0
        self.BLOODBATH: int = 0
        self.DOUBLE_TROUBLE: int = 0
        self.EX: int = 0
        self.GHOST: int = 0
        self.UNBOUND: int = 0
        self.MIDNIGHT: int = 0
        self.ALTERNATE: int = 0
        self.MYSTIC_MOON: int = 0
        self.BLOOD_MOON: int = 0
        self.TWILIGHT: int = 0
        self.SOLSTICE: int = 0
        self.RUN: int = 0
        self.PAGES: int = 0

    def get_time_string(self) -> str:
        time_string = str(timedelta(seconds=int(time.time() - self.instance_start)))

        return time_string[2:] if time_string.startswith("0:") else time_string

    def add_terror(self) -> None:
        self.terror_history.insert(0, self.terrors_name)
        if len(self.terror_history) > 5:
            self.terror_history.pop(-1)


IGNORED_STATS = [
    "DisplayName",
    "InstanceURL",
    "DiscordName",
    "Rounds",
    "Deaths",
    "Survivals",
    "DamageTaken",
    "TopStuns",
    "TopStunsAll",
    "Stuns",
    "StunsAll",
    "IsOptedIn",
    "LobbyDeaths",
    "LobbySurvivals",
    "LobbyDamageTaken",
    "LobbyStuns",
    "LobbyStunsAll",
    "LobbyTopStuns",
    "LobbyTopStunsAll",
    "TerrorName",
    "RoundType",
    "MapName",
    "MapCreator",
    "MapOrigin",
    "ItemName",
    "IsAlive",
    "IsReborn",
    "IsKiller",
    "IsStarted",
    "RoundInt",
    "MapInt",
    "PageCount",
    "RoundStuns",
]
STATS_NAMES = IGNORED_STATS + ["PlayersOnline", "LobbyRounds", "RoundStunsAll"]

ToNData = ToNWebsocket()


def event_instance(data: Any) -> None:
    ToNData.instance_start = time.time()
    ToNData.alive = True
    ToNData.round_active = False
    ToNData.is_saboteur = False
    ToNData.players_online = 0
    ToNData.lobby_rounds = 0
    ToNData.round_stun_all = 0
    ToNData.players_left = 0
    ToNData.round_type = ToNRoundType.UNKNOWN
    ToNData.location = ""
    ToNData.terrors_name = ""
    ToNData.terrors_command = 255
    ToNData.terror_history = []
    ToNData.enrage_guess = ""
    ToNData.last_round = ToNRoundType.UNKNOWN

    ToNData.CLASSIC = 0
    ToNData.FOG = 0
    ToNData.PUNISHED = 0
    ToNData.SABOTAGE = 0
    ToNData.CRACKED = 0
    ToNData.BLOODBATH = 0
    ToNData.DOUBLE_TROUBLE = 0
    ToNData.EX = 0
    ToNData.GHOST = 0
    ToNData.UNBOUND = 0
    ToNData.MIDNIGHT = 0
    ToNData.ALTERNATE = 0
    ToNData.MYSTIC_MOON = 0
    ToNData.BLOOD_MOON = 0
    ToNData.TWILIGHT = 0
    ToNData.SOLSTICE = 0
    ToNData.RUN = 0
    ToNData.PAGES = 0


def event_alive(data: Any) -> None:
    ToNData.alive = data["Value"]


def event_round_active(data: Any) -> None:
    ToNData.round_active = data["Value"]

    if ToNData.round_active:
        ToNData.enrage_guess = ""
        ToNData.lobby_rounds += 1
        ToNData.players_left = ToNData.players_online
    else:
        ToNData.is_saboteur = False
        ToNData.add_terror()


def event_opted_in(data: Any) -> None:
    ToNData.opted_in = data["Value"]


def event_is_saboteur(data: Any) -> None:
    ToNData.is_saboteur = data["Value"]


def event_death(data: Any) -> None:
    ToNData.players_left -= 1


def event_round_type(data: Any) -> None:
    try:
        ToNData.round_type = ToNRoundType(data["Value"])

        if ToNData.round_type != ToNRoundType.UNKNOWN:
            ToNData.last_round = ToNData.round_type

        if ToNData.round_type is ToNRoundType.FOG_ALTERNATE:
            ToNData.FOG += 1
            ToNData.ALTERNATE += 1
        elif ToNData.round_type is ToNRoundType.GHOST_ALTERNATE:
            ToNData.GHOST += 1
            ToNData.ALTERNATE += 1
        else:
            try:
                item = getattr(ToNData, ToNData.round_type.name)
                setattr(ToNData, ToNData.round_type.name, item + 1)
            except AttributeError:
                pass
    except ValueError:
        log.debug("Unhandled round type: %s", data)
        ToNData.round_type = ToNRoundType.UNKNOWN


def event_location(data: Any) -> None:
    ToNData.location = data["Name"]


def event_terrors(data: Any) -> None:
    ToNData.terrors_command = data["Command"]
    if ToNData.terrors_command != 255:
        if data["Names"] is None:
            ToNData.terrors_name = "???"
            return

        if not isinstance(data["Names"], list):
            return

        ToNData.terrors_name = " | ".join(
            NAME_OVERRIDES.get(x, x) for x in data["Names"]
        )


def event_stats(data: Any) -> None:
    if data["Name"] not in STATS_NAMES:
        log.debug("Unhandled STATS event: %s", data)

    if data["Name"] == "PlayersOnline":
        ToNData.players_online = data["Value"]
    elif data["Name"] == "LobbyRounds":
        pass  # This is currently buggy and inaccurate
        # ToNData.lobby_rounds = data["Value"]
    elif data["Name"] == "RoundStunsAll":
        ToNData.round_stun_all = 0 if data["Value"] is None else data["Value"]


def event_connected(data: Any) -> None:
    for event in data["Args"]:
        ev = EVENTS.get(event["Type"], None)
        if ev is None:
            if event["Type"] in IGNORED_EVENTS:
                continue

            unknown_event(event)
            continue

        ev(event)


def event_tracker(data: Any) -> None:
    if data["event"] == "enemy_enraged":
        ToNData.enrage_guess = data["args"][0]


IGNORED_EVENTS = [
    "SAVED",
    "PLAYER_JOIN",
    "ITEM",
    "DAMAGED",
    "PLAYER_LEAVE",
    "PAGE_COUNT",
    "REBORN",
]
EVENTS = {
    "CONNECTED": event_connected,
    "STATS": event_stats,
    "INSTANCE": event_instance,
    "ALIVE": event_alive,
    "ROUND_ACTIVE": event_round_active,
    "OPTED_IN": event_opted_in,
    "IS_SABOTEUR": event_is_saboteur,
    "DEATH": event_death,
    "ROUND_TYPE": event_round_type,
    "LOCATION": event_location,
    "TERRORS": event_terrors,
    "TRACKER": event_tracker,
}


def to_json(message: str) -> dict | None:
    try:
        return json.loads(message)
    except json.JSONDecodeError as e:
        log.error("Unable to decode JSON %s", e.msg)
        return


def unknown_event(data: Any) -> None:
    log.debug("Received unhandled event: %s", data["Type"])
    log.debug(data)


def on_error(ws, error):
    if isinstance(error, ConnectionRefusedError):
        global connection_error_count
        if connection_error_count >= 5:
            log.warning("Unable to establish websocket connection")
            rel.abort()
        else:
            connection_error_count += 1
    else:
        log.error("%s %s", type(error), error)


def on_close(ws=None, close_status_code=None, close_msg=None):
    log.info("Websocket connection closed")
    if close_status_code is not None:
        log.warning("Status Code: %s", close_status_code)
    if close_msg is not None:
        log.warning("Message: %s", close_msg)


def on_open(ws):
    global connection_error_count
    connection_error_count = 0
    log.info("Successfully connected to websocket")


def on_message(ws, message):
    data = to_json(message)

    if data is None:
        return

    func = EVENTS.get(data["Type"], None)

    if func is None:
        if data["Type"] in IGNORED_EVENTS:
            return

        return unknown_event(data)

    if data["Type"] != "TRACKER":
        log.debug(data)
    func(data)


def run_websocket():
    global ready_to_exit
    log.info("Trying to connect to websocket")
    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        "ws://localhost:11398",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    ws.run_forever(
        dispatcher=rel, reconnect=5
    )  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    try:
        rel.dispatch()
    except ConnectionResetError:
        on_close()

    ready_to_exit.set()
    sys.exit()


def render_page(page: int = 0) -> str:
    if page == 0:
        out = "\n".join(
            [
                "",
                f"Last {len(ToNData.terror_history)} Terrors",
                "================",
                "\n".join(ToNData.terror_history),
            ]
        )
        return out
    elif page == 1:
        out = "\n".join(
            [
                "",
                "Round Count",
                "Page 1/2",
                f"Classic: {ToNData.CLASSIC} | Fog: {ToNData.FOG}",
                f"Punished: {ToNData.PUNISHED} | Sabotage: {ToNData.SABOTAGE}",
                f"Ghost: {ToNData.GHOST} | Cracked: {ToNData.CRACKED}",
            ]
        )
        return out
    elif page == 2:
        out = "\n".join(
            [
                "",
                "Round Count",
                "Page 2/2",
                f"Bloodbath: {ToNData.BLOODBATH} | Double Trouble: {ToNData.DOUBLE_TROUBLE}",
                f"EX: {ToNData.EX} | Unbound: {ToNData.UNBOUND}",
                f"Midnight: {ToNData.MIDNIGHT} | Alternate: {ToNData.ALTERNATE}",
            ]
        )
        return out
    elif page == 3:
        out = "\n".join(
            [
                "",
                "Moon Count",
                "================",
                f"Mystic: {ToNData.MYSTIC_MOON}",
                f"Blood: {ToNData.BLOOD_MOON}",
                f"Twilight: {ToNData.TWILIGHT}",
                f"Solstice: {ToNData.SOLSTICE}",
            ]
        )
        return out
    else:
        return "[ERROR] Failed to render page"


def run_osc():
    global ready_to_exit
    client = udp_client.SimpleUDPClient(OSC_IP, OSC_PORT)

    page = 0
    time_page = time.time() + 15
    while not ready_to_exit.is_set():
        if (time_page - time.time()) <= 0:
            time_page = time.time() + 15
            if page < 3:
                page += 1
            else:
                page = 0

        header = f"Time: {ToNData.get_time_string()} | Rounds: {ToNData.lobby_rounds}"
        default_round = (
            f"Type: {ToNData.round_type.prettify()} | Map: {ToNData.location}"
        )
        default_terrors = ToNData.terrors_name
        footer = ""
        if ToNData.round_type is not ToNRoundType.PAGES:
            footer += f"Survivors: {ToNData.players_left} | "
        footer += f"Round Stuns: {ToNData.round_stun_all}"
        if (
            ToNData.is_saboteur
            and ToNData.round_active
            and ToNData.terrors_command == 4
        ):
            msg = "\n".join(
                [
                    "===============",
                    "GET AWAY FROM ME",
                    "",
                    "I AM MURDERER",
                    "===============",
                ]
            )
        elif ToNData.is_saboteur and ToNData.round_active and ToNData.alive:
            msg = "\n".join(
                [
                    default_round,
                    "",
                    default_terrors,
                    "",
                    "I AM PACIFIST MURDERER",
                    footer,
                ]
            )
        elif (
            ToNData.round_active
            and ToNData.alive
            and ToNData.terrors_command == 2
            and ToNData.enrage_guess
        ):
            msg = "\n".join(
                [
                    default_round,
                    "",
                    f"Actual Terror: {default_terrors}",
                    "",
                    f"Enrage Guess: {ToNData.enrage_guess}",
                    "",
                    footer,
                ]
            )
        elif ToNData.round_active and ToNData.alive:
            msg = "\n".join(
                [
                    default_round,
                    "",
                    default_terrors,
                    "",
                    footer,
                ]
            )
        elif ToNData.round_active:
            msg = "\n".join(
                [
                    header,
                    default_round,
                    "",
                    default_terrors,
                    "",
                    footer,
                ]
            )
        elif (
            ToNData.last_round is ToNRoundType.PUNISHED
            or ToNData.last_round is ToNRoundType.PAGES
        ):
            msg = "\n".join(
                [header, "===============", "GET", "YOUR", "ITEMS", "==============="]
            )
        elif ToNData.round_active is False and len(ToNData.terror_history) > 0:
            msg = "\n".join([header, render_page(page)])
        else:
            msg = header

        if ToNData.opted_in:
            client.send_message("/chatbox/input", [msg, True, False])
        ready_to_exit.wait(2)


def check_for_update() -> None:
    with requests.Session() as session:
        session.headers = {
            "User-Agent": f"ToNChatbox/{_VERSION}",
            "Accept": "application/vnd.github+json",
        }
        r = session.get(
            "https://api.github.com/repos/ItsMestro/ToNChatbox/releases/latest"
        )

    if not r.ok:
        log.warning("Unable to check for new version of the app")

    data: dict = json.loads(r.content)

    new_version: str = data.get("tag_name", "")
    if new_version != _VERSION:
        log.info(
            "\n".join(
                [
                    f"There's a new version of ToNChatbox available! Current: {_VERSION} > Latest: {new_version}",
                    "Grab the latest one here: https://github.com/ItsMestro/ToNChatbox/releases/latest",
                ]
            )
        )


if __name__ == "__main__":
    ctypes.windll.kernel32.SetConsoleTitleW(f"ToNChatbox {_VERSION}")

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        check_for_update()

    thread = threading.Thread(target=run_osc)
    thread.start()

    run_websocket()
