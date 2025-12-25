# Key mapping and constants for MacroPad
from adafruit_hid.keycode import Keycode

# Physical key number to logical key number mapping
# Physical layout on MacroPad (3x4 matrix, USB at top):
#   0   1   2
#   3   4   5
#   6   7   8
#   9  10  11
#
# Logical layout (1:1 mapping, no rotation):
#   0   1   2
#   3   4   5
#   6   7   8
#   9  10  11

KEY_MAP = {
    0: 0,  1: 1,  2: 2,     # Top row
    3: 3,  4: 4,  5: 5,     # Second row
    6: 6,  7: 7,  8: 8,     # Third row
    9: 9, 10: 10, 11: 11    # Bottom row
}

# Reverse mapping (logical to physical) - for RGB LED control
REVERSE_KEY_MAP = {v: k for k, v in KEY_MAP.items()}

# String to Keycode mapping for parsing key combinations
KEY_NAMES = {
    # Letters
    'A': Keycode.A, 'B': Keycode.B, 'C': Keycode.C, 'D': Keycode.D,
    'E': Keycode.E, 'F': Keycode.F, 'G': Keycode.G, 'H': Keycode.H,
    'I': Keycode.I, 'J': Keycode.J, 'K': Keycode.K, 'L': Keycode.L,
    'M': Keycode.M, 'N': Keycode.N, 'O': Keycode.O, 'P': Keycode.P,
    'Q': Keycode.Q, 'R': Keycode.R, 'S': Keycode.S, 'T': Keycode.T,
    'U': Keycode.U, 'V': Keycode.V, 'W': Keycode.W, 'X': Keycode.X,
    'Y': Keycode.Y, 'Z': Keycode.Z,
    
    # Numbers
    '0': Keycode.ZERO, '1': Keycode.ONE, '2': Keycode.TWO,
    '3': Keycode.THREE, '4': Keycode.FOUR, '5': Keycode.FIVE,
    '6': Keycode.SIX, '7': Keycode.SEVEN, '8': Keycode.EIGHT,
    '9': Keycode.NINE,
    
    # Function keys
    'F1': Keycode.F1, 'F2': Keycode.F2, 'F3': Keycode.F3, 'F4': Keycode.F4,
    'F5': Keycode.F5, 'F6': Keycode.F6, 'F7': Keycode.F7, 'F8': Keycode.F8,
    'F9': Keycode.F9, 'F10': Keycode.F10, 'F11': Keycode.F11, 'F12': Keycode.F12,
    
    # Special keys
    'ENTER': Keycode.ENTER, 'RETURN': Keycode.RETURN,
    'ESCAPE': Keycode.ESCAPE, 'ESC': Keycode.ESCAPE,
    'BACKSPACE': Keycode.BACKSPACE,
    'TAB': Keycode.TAB,
    'SPACE': Keycode.SPACE, 'SPACEBAR': Keycode.SPACE,
    'MINUS': Keycode.MINUS, 'EQUALS': Keycode.EQUALS,
    'LEFT_BRACKET': Keycode.LEFT_BRACKET, 'RIGHT_BRACKET': Keycode.RIGHT_BRACKET,
    'BACKSLASH': Keycode.BACKSLASH, 'POUND': Keycode.POUND,
    'SEMICOLON': Keycode.SEMICOLON, 'QUOTE': Keycode.QUOTE,
    'GRAVE_ACCENT': Keycode.GRAVE_ACCENT,
    'COMMA': Keycode.COMMA, 'PERIOD': Keycode.PERIOD,
    'FORWARD_SLASH': Keycode.FORWARD_SLASH,
    
    # Arrow keys
    'UP': Keycode.UP_ARROW, 'DOWN': Keycode.DOWN_ARROW,
    'LEFT': Keycode.LEFT_ARROW, 'RIGHT': Keycode.RIGHT_ARROW,
    'UP_ARROW': Keycode.UP_ARROW, 'DOWN_ARROW': Keycode.DOWN_ARROW,
    'LEFT_ARROW': Keycode.LEFT_ARROW, 'RIGHT_ARROW': Keycode.RIGHT_ARROW,
    
    # Other keys
    'INSERT': Keycode.INSERT, 'DELETE': Keycode.DELETE,
    'HOME': Keycode.HOME, 'END': Keycode.END,
    'PAGE_UP': Keycode.PAGE_UP, 'PAGEUP': Keycode.PAGE_UP,
    'PAGE_DOWN': Keycode.PAGE_DOWN, 'PAGEDOWN': Keycode.PAGE_DOWN,
    'CAPS_LOCK': Keycode.CAPS_LOCK,
    'PRINT_SCREEN': Keycode.PRINT_SCREEN,
    'SCROLL_LOCK': Keycode.SCROLL_LOCK,
    'PAUSE': Keycode.PAUSE,
    
    # Modifiers
    'CTRL': Keycode.CONTROL, 'CONTROL': Keycode.CONTROL,
    'SHIFT': Keycode.SHIFT,
    'ALT': Keycode.ALT, 'OPTION': Keycode.ALT,
    'GUI': Keycode.GUI, 'WIN': Keycode.GUI, 'WINDOWS': Keycode.GUI,
    'CMD': Keycode.GUI, 'COMMAND': Keycode.GUI,
    'LEFT_CTRL': Keycode.LEFT_CONTROL, 'LEFT_CONTROL': Keycode.LEFT_CONTROL,
    'LEFT_SHIFT': Keycode.LEFT_SHIFT,
    'LEFT_ALT': Keycode.LEFT_ALT,
    'LEFT_GUI': Keycode.LEFT_GUI,
    'RIGHT_CTRL': Keycode.RIGHT_CONTROL, 'RIGHT_CONTROL': Keycode.RIGHT_CONTROL,
    'RIGHT_SHIFT': Keycode.RIGHT_SHIFT,
    'RIGHT_ALT': Keycode.RIGHT_ALT,
    'RIGHT_GUI': Keycode.RIGHT_GUI,
}

# Modifier keys for combination parsing
MODIFIERS = {
    'CTRL', 'CONTROL',
    'SHIFT',
    'ALT', 'OPTION',
    'GUI', 'WIN', 'WINDOWS', 'CMD', 'COMMAND'
}
