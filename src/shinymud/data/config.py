from shinymud.lib.ansi_codes import *
import os

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

HOST = ''
PORT = 4111
LOG_FILE = ROOT_DIR + '/logs/shinymud.log'
LOG_LEVEL = 10 # 10 is the equivalent of "DEBUG"
DB_NAME = ROOT_DIR + '/shinymud.db'
AREAS_IMPORT_DIR = ROOT_DIR + '/areas'
AREAS_EXPORT_DIR = ROOT_DIR + '/areas'
RESET_INTERVAL = 120 # Amount of time (in seconds) that should pass before an area resets

# Color constants:
clear_fcolor = COLOR_FG_RESET # DON'T CHANGE THIS ONE!
clear_bcolor = COLOR_BG_RESET # DON'T CHANGE THIS ONE EITHER!

# Communication colors
chat_color = COLOR_FG_CYAN
say_color = COLOR_FG_YELLOW
wecho_color = COLOR_FG_BLUE

# Object colors
npc_color = COLOR_FG_YELLOW
user_color = COLOR_FG_YELLOW
room_title_color = COLOR_FG_GREEN
room_body_color = COLOR_FG_GREEN
room_exit_color = COLOR_FG_CYAN
room_id_color = COLOR_FG_RED
item_color = COLOR_FG_RED
