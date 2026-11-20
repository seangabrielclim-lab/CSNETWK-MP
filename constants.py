#general constants
LOBBY_PORT = 7777
BLANK = "0.0.0.0"
MIN_PLAYERS = 3
MAX_PLAYERS = 7
SENTINEL = 0xFFFF

#constants for message types
LOBBY_PRESENCE = 0x01
LOBBY_LEAVE = 0x02
LOBBY_START_VOTE = 0x03
LOBBY_START_ACK = 0x04
HELLO = 0x05
HELLO_ACK = 0x06

#constants for disconnection
RETRY_MAX = 6

#constants for timers
T_ACK_DELAY = 0.05
RTO_INIT = 0.2
T_LOBBY_ANNOUNCE_INTERVAL = 2
T_LOBBY_STALE = 6
T_LOBBY_QUIET = 3
T_LOBBY_TIMEOUT = 120