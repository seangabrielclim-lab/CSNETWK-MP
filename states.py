from enum import Enum

class State(Enum):
    IDLE = 1
    LOBBY_SEARCHING = 2
    INIT = 3
    DISCOVERING = 4
    SEEDING = 5
    DEALT = 6
    AGE_END = 7
    SCORING = 8
    DONE = 9
    ABORT = 10