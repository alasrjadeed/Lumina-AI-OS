"""ADB Keyboard — send keystrokes and text to Android devices via ADB."""

from __future__ import annotations

import time
from dataclasses import dataclass

from core.android.device import AndroidDevice
from core.log import log


# Android KeyEvent constants
class Key:
    HOME = 3
    BACK = 4
    CALL = 5
    ENDCALL = 6
    KEY_0 = 7
    KEY_1 = 8
    KEY_2 = 9
    KEY_3 = 10
    KEY_4 = 11
    KEY_5 = 12
    KEY_6 = 13
    KEY_7 = 14
    KEY_8 = 15
    KEY_9 = 16
    STAR = 17
    POUND = 18
    DPAD_UP = 19
    DPAD_DOWN = 20
    DPAD_LEFT = 21
    DPAD_RIGHT = 22
    DPAD_CENTER = 23
    VOLUME_UP = 24
    VOLUME_DOWN = 25
    POWER = 26
    CAMERA = 27
    CLEAR = 28
    A = 29
    B = 30
    C = 31
    D = 32
    E = 33
    F = 34
    G = 35
    H = 36
    KEY_I = 37
    J = 38
    K = 39
    L = 40
    M = 41
    N = 42
    KEY_O = 43
    P = 44
    Q = 45
    R = 46
    S = 47
    T = 48
    U = 49
    V = 50
    W = 51
    X = 52
    Y = 53
    Z = 54
    COMMA = 55
    PERIOD = 56
    ALT_LEFT = 57
    ALT_RIGHT = 58
    SHIFT_LEFT = 59
    SHIFT_RIGHT = 60
    TAB = 61
    SPACE = 62
    ENTER = 66
    DEL = 67
    FOCUS = 80
    MENU = 82
    NOTIFICATION = 83
    SEARCH = 84
    ESC = 111
    CAPS_LOCK = 115
    SCROLL_LOCK = 116
    CTRL_LEFT = 113
    CTRL_RIGHT = 114

    MEDIA_PLAY_PAUSE = 85
    MEDIA_STOP = 86
    MEDIA_NEXT = 87
    MEDIA_PREVIOUS = 88
    MEDIA_REWIND = 89
    MEDIA_FAST_FORWARD = 90
    MUTE = 91

    NUMPAD_0 = 144
    NUMPAD_1 = 145
    NUMPAD_2 = 146
    NUMPAD_3 = 147
    NUMPAD_4 = 148
    NUMPAD_5 = 149
    NUMPAD_6 = 150
    NUMPAD_7 = 151
    NUMPAD_8 = 152
    NUMPAD_9 = 153

    SEMICOLON = 154
    PLUS = 155
    MINUS = 156
    EQUALS = 157
    SLASH = 158
    BACKSLASH = 159
    LEFT_BRACKET = 160
    RIGHT_BRACKET = 161
    APOSTROPHE = 162
    GRAVE = 163
    AT = 164
    COLON = 165
    PIPE = 166
    TILDE = 167

    # Meta keys
    META_ALT_ON = 2
    META_SHIFT_ON = 1
    META_CTRL_ON = 4096

    @staticmethod
    def name_to_code(name: str) -> int | None:
        """Convert a key name to its keycode."""
        mapping = {
            "home": Key.HOME,
            "back": Key.BACK,
            "menu": Key.MENU,
            "enter": Key.ENTER,
            "space": Key.SPACE,
            "tab": Key.TAB,
            "del": Key.DEL,
            "delete": Key.DEL,
            "clear": Key.CLEAR,
            "search": Key.SEARCH,
            "power": Key.POWER,
            "volume_up": Key.VOLUME_UP,
            "volume_down": Key.VOLUME_DOWN,
            "camera": Key.CAMERA,
            "call": Key.CALL,
            "endcall": Key.ENDCALL,
            "up": Key.DPAD_UP,
            "down": Key.DPAD_DOWN,
            "left": Key.DPAD_LEFT,
            "right": Key.DPAD_RIGHT,
            "center": Key.DPAD_CENTER,
            "ok": Key.DPAD_CENTER,
            "escape": Key.ESC,
            "esc": Key.ESC,
            "caps": Key.CAPS_LOCK,
            "caps_lock": Key.CAPS_LOCK,
            "scroll": Key.SCROLL_LOCK,
            "num": Key.NUMPAD_0,
            "play": Key.MEDIA_PLAY_PAUSE,
            "pause": Key.MEDIA_PLAY_PAUSE,
            "stop": Key.MEDIA_STOP,
            "next": Key.MEDIA_NEXT,
            "prev": Key.MEDIA_PREVIOUS,
            "mute": Key.MUTE,
            "notification": Key.NOTIFICATION,
        }
        return mapping.get(name.lower().strip())

    @staticmethod
    def char_to_keycode(char: str) -> tuple[int, bool]:
        """Convert a character to (keycode, shift_needed)."""
        code_map = {
            "a": (Key.A, False),
            "b": (Key.B, False),
            "c": (Key.C, False),
            "d": (Key.D, False),
            "e": (Key.E, False),
            "f": (Key.F, False),
            "g": (Key.G, False),
            "h": (Key.H, False),
            "i": (Key.KEY_I, False),
            "j": (Key.J, False),
            "k": (Key.K, False),
            "l": (Key.L, False),
            "m": (Key.M, False),
            "n": (Key.N, False),
            "o": (Key.KEY_O, False),
            "p": (Key.P, False),
            "q": (Key.Q, False),
            "r": (Key.R, False),
            "s": (Key.S, False),
            "t": (Key.T, False),
            "u": (Key.U, False),
            "v": (Key.V, False),
            "w": (Key.W, False),
            "x": (Key.X, False),
            "y": (Key.Y, False),
            "z": (Key.Z, False),
            "A": (Key.A, True),
            "B": (Key.B, True),
            "C": (Key.C, True),
            "D": (Key.D, True),
            "E": (Key.E, True),
            "F": (Key.F, True),
            "G": (Key.G, True),
            "H": (Key.H, True),
            "I": (Key.KEY_I, True),
            "J": (Key.J, True),
            "K": (Key.K, True),
            "L": (Key.L, True),
            "M": (Key.M, True),
            "N": (Key.N, True),
            "O": (Key.KEY_O, True),
            "P": (Key.P, True),
            "Q": (Key.Q, True),
            "R": (Key.R, True),
            "S": (Key.S, True),
            "T": (Key.T, True),
            "U": (Key.U, True),
            "V": (Key.V, True),
            "W": (Key.W, True),
            "X": (Key.X, True),
            "Y": (Key.Y, True),
            "Z": (Key.Z, True),
            "0": (Key.KEY_0, False),
            "1": (Key.KEY_1, False),
            "2": (Key.KEY_2, False),
            "3": (Key.KEY_3, False),
            "4": (Key.KEY_4, False),
            "5": (Key.KEY_5, False),
            "6": (Key.KEY_6, False),
            "7": (Key.KEY_7, False),
            "8": (Key.KEY_8, False),
            "9": (Key.KEY_9, False),
            " ": (Key.SPACE, False),
            ".": (Key.PERIOD, False),
            ",": (Key.COMMA, False),
            "\t": (Key.TAB, False),
            "\n": (Key.ENTER, False),
            "!": (Key.KEY_1, True),
            "@": (Key.AT, False),
            "#": (Key.POUND, False),
            "$": (Key.KEY_4, True),
            "%": (Key.KEY_5, True),
            "^": (Key.KEY_6, True),
            "&": (Key.KEY_7, True),
            "*": (Key.STAR, False),
            "(": (Key.KEY_9, True),
            ")": (Key.KEY_0, True),
            "-": (Key.MINUS, False),
            "_": (Key.MINUS, True),
            "=": (Key.EQUALS, False),
            "+": (Key.PLUS, False),
            "[": (Key.LEFT_BRACKET, False),
            "{": (Key.LEFT_BRACKET, True),
            "]": (Key.RIGHT_BRACKET, False),
            "}": (Key.RIGHT_BRACKET, True),
            "\\": (Key.BACKSLASH, False),
            "|": (Key.PIPE, False),
            ";": (Key.SEMICOLON, False),
            ":": (Key.COLON, False),
            "'": (Key.APOSTROPHE, False),
            '"': (Key.APOSTROPHE, True),
            "/": (Key.SLASH, False),
            "?": (Key.SLASH, True),
            "`": (Key.GRAVE, False),
            "~": (Key.TILDE, False),
            "<": (Key.COMMA, True),
            ">": (Key.PERIOD, True),
        }
        return code_map.get(char, (Key.SPACE, False))


def soft_keyboard_enable(device: AndroidDevice) -> dict:
    """Enable ADB Keyboard IME on the device."""
    ime = "com.android.adbkeyboard/.AdbIME"
    result = device.shell(f"ime enable {ime} 2>/dev/null && ime set {ime} 2>/dev/null")
    ok = "not found" not in result.lower()
    log.info("ADB Keyboard IME: %s", "enabled" if ok else "not available")
    return {"enabled": ok, "output": result.strip()}


def soft_keyboard_disable(device: AndroidDevice) -> dict:
    """Disable ADB Keyboard IME and revert to default."""
    result = device.shell("ime reset 2>/dev/null")
    return {"result": result.strip()}


@dataclass
class KeyPressResult:
    success: bool
    message: str = ""
    error: str = ""


class LuminaADBKeyboard:
    """Lumina ADB Keyboard — virtual keyboard for Android devices via ADB."""

    def __init__(self, device: AndroidDevice | None = None):
        self.device = device or AndroidDevice()

    def type_text(self, text: str, delay_ms: int = 0) -> KeyPressResult:
        """Type text on the device. Uses ADB input text or keyevent for special chars."""
        if not self.device.is_connected:
            return KeyPressResult(False, error="No device connected")
        try:
            self.device.input_text(text)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
            log.info("ADB Keyboard: typed %d chars", len(text))
            return KeyPressResult(True, message=f"Typed {len(text)} characters")
        except Exception as e:
            return KeyPressResult(False, error=str(e))

    def press_key(self, key_name: str) -> KeyPressResult:
        """Press a named key (home, back, enter, etc.)."""
        code = Key.name_to_code(key_name)
        if code is None:
            return KeyPressResult(False, error=f"Unknown key: {key_name}")
        return self.press_keycode(code)

    def press_keycode(self, code: int) -> KeyPressResult:
        """Press a key by its Android keycode."""
        if not self.device.is_connected:
            return KeyPressResult(False, error="No device connected")
        try:
            self.device.input_keyevent(code)
            log.info("ADB Keyboard: keycode %d", code)
            return KeyPressResult(True, message=f"Keycode {code} pressed")
        except Exception as e:
            return KeyPressResult(False, error=str(e))

    def press_enter(self) -> KeyPressResult:
        return self.press_keycode(Key.ENTER)

    def press_back(self) -> KeyPressResult:
        return self.press_keycode(Key.BACK)

    def press_home(self) -> KeyPressResult:
        return self.press_keycode(Key.HOME)

    def press_menu(self) -> KeyPressResult:
        return self.press_keycode(Key.MENU)

    def press_del(self) -> KeyPressResult:
        return self.press_keycode(Key.DEL)

    def press_tab(self) -> KeyPressResult:
        return self.press_keycode(Key.TAB)

    def press_space(self) -> KeyPressResult:
        return self.press_keycode(Key.SPACE)

    def press_search(self) -> KeyPressResult:
        return self.press_keycode(Key.SEARCH)

    def press_power(self) -> KeyPressResult:
        return self.press_keycode(Key.POWER)

    def press_volume_up(self) -> KeyPressResult:
        return self.press_keycode(Key.VOLUME_UP)

    def press_volume_down(self) -> KeyPressResult:
        return self.press_keycode(Key.VOLUME_DOWN)

    def press_mute(self) -> KeyPressResult:
        return self.press_keycode(Key.MUTE)

    def press_dpad(self, direction: str) -> KeyPressResult:
        dir_map = {
            "up": Key.DPAD_UP,
            "down": Key.DPAD_DOWN,
            "left": Key.DPAD_LEFT,
            "right": Key.DPAD_RIGHT,
            "center": Key.DPAD_CENTER,
            "ok": Key.DPAD_CENTER,
        }
        code = dir_map.get(direction.lower())
        if code is None:
            return KeyPressResult(False, error=f"Unknown direction: {direction}")
        return self.press_keycode(code)

    def press_media(self, action: str) -> KeyPressResult:
        action_map = {
            "play": Key.MEDIA_PLAY_PAUSE,
            "pause": Key.MEDIA_PLAY_PAUSE,
            "stop": Key.MEDIA_STOP,
            "next": Key.MEDIA_NEXT,
            "prev": Key.MEDIA_PREVIOUS,
            "rewind": Key.MEDIA_REWIND,
            "ff": Key.MEDIA_FAST_FORWARD,
        }
        code = action_map.get(action.lower())
        if code is None:
            return KeyPressResult(False, error=f"Unknown media action: {action}")
        return self.press_keycode(code)

    def type_key_by_key(self, text: str, delay_ms: int = 50) -> KeyPressResult:
        """Type text character by character using keycodes (handles special chars better)."""
        if not self.device.is_connected:
            return KeyPressResult(False, error="No device connected")
        count = 0
        for char in text:
            code, shift = Key.char_to_keycode(char)
            try:
                if shift:
                    self.device._adb(
                        "shell", "input", "keyevent", f"--longpress {Key.SHIFT_LEFT} {code}"
                    )
                else:
                    self.device.input_keyevent(code)
                count += 1
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000)
            except Exception:
                pass
        return KeyPressResult(True, message=f"Typed {count} characters via keyevents")

    def clear_text(self) -> KeyPressResult:
        """Clear text by selecting all and deleting."""
        if not self.device.is_connected:
            return KeyPressResult(False, error="No device connected")
        try:
            self.device._adb("shell", "input", "keyevent", f"--longpress {Key.A}")
            self.device.input_keyevent(Key.DEL)
            return KeyPressResult(True, message="Text cleared")
        except Exception as e:
            return KeyPressResult(False, error=str(e))

    def get_ime_list(self) -> list[dict]:
        """List available input methods on the device."""
        if not self.device.is_connected:
            return []
        output = self.device.shell("ime list -s")
        return [
            {"id": line.strip(), "active": "adbkeyboard" in line.lower()}
            for line in output.strip().split("\n")
            if line.strip()
        ]

    def set_ime(self, ime_id: str) -> KeyPressResult:
        """Set the active input method."""
        try:
            self.device.shell(f"ime set {ime_id} 2>/dev/null")
            return KeyPressResult(True, message=f"IME set: {ime_id}")
        except Exception as e:
            return KeyPressResult(False, error=str(e))


adb_keyboard = LuminaADBKeyboard()
