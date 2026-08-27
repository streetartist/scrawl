"""Key and mouse button constants used by Scrawl input decorators."""

# Arrow keys
K_LEFT = "left"
K_RIGHT = "right"
K_UP = "up"
K_DOWN = "down"

# Letters
K_a = "a"
K_b = "b"
K_c = "c"
K_d = "d"
K_e = "e"
K_f = "f"
K_g = "g"
K_h = "h"
K_i = "i"
K_j = "j"
K_k = "k"
K_l = "l"
K_m = "m"
K_n = "n"
K_o = "o"
K_p = "p"
K_q = "q"
K_r = "r"
K_s = "s"
K_t = "t"
K_u = "u"
K_v = "v"
K_w = "w"
K_x = "x"
K_y = "y"
K_z = "z"

# Numbers
K_0 = "0"
K_1 = "1"
K_2 = "2"
K_3 = "3"
K_4 = "4"
K_5 = "5"
K_6 = "6"
K_7 = "7"
K_8 = "8"
K_9 = "9"

# Special keys
K_SPACE = "space"
K_RETURN = "return"
K_ESCAPE = "escape"
K_BACKSPACE = "backspace"
K_TAB = "tab"
K_LSHIFT = "lshift"
K_RSHIFT = "rshift"
K_LCTRL = "lctrl"
K_RCTRL = "rctrl"
K_LALT = "lalt"
K_RALT = "ralt"

# Function keys
K_F1 = "f1"
K_F2 = "f2"
K_F3 = "f3"
K_F4 = "f4"
K_F5 = "f5"
K_F6 = "f6"
K_F7 = "f7"
K_F8 = "f8"
K_F9 = "f9"
K_F10 = "f10"
K_F11 = "f11"
K_F12 = "f12"

# Mouse buttons
MOUSE_LEFT = 1
MOUSE_MIDDLE = 2
MOUSE_RIGHT = 3

def resolve_key(key: str) -> str:
    """Normalize a documented string key name."""
    if not isinstance(key, str):
        raise TypeError("Scrawl key identifiers must be strings")
    normalized = key.strip().lower()
    if not normalized:
        raise ValueError("Scrawl key identifiers cannot be empty")
    return normalized
