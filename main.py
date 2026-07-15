import os
import sys
import time
import shutil
import subprocess
from pathlib import Path

SHORTCUT_FILE = "shortcuts.txt"

# Fast settings
EXPAND_DELAY = 0.025
EXPAND_COOLDOWN = 0.12
KEY_DELAY = 0.0015
PASTE_DELAY = 0.025

enabled = True
word_buffer = ""
shift_pressed = False

is_expanding = False
last_expand_time = 0

# Platform Detection
IS_LINUX = sys.platform.startswith("linux")

LOWER_KEYMAP = {}
SHIFT_KEYMAP = {}
CHAR_TO_KEY = {}

if IS_LINUX:
    try:
        from evdev import InputDevice, UInput, ecodes, list_devices
    except ImportError:
        print("Please install evdev: pip install evdev")
        sys.exit(1)

    LOWER_KEYMAP = {
        ecodes.KEY_A: "a", ecodes.KEY_B: "b", ecodes.KEY_C: "c",
        ecodes.KEY_D: "d", ecodes.KEY_E: "e", ecodes.KEY_F: "f",
        ecodes.KEY_G: "g", ecodes.KEY_H: "h", ecodes.KEY_I: "i",
        ecodes.KEY_J: "j", ecodes.KEY_K: "k", ecodes.KEY_L: "l",
        ecodes.KEY_M: "m", ecodes.KEY_N: "n", ecodes.KEY_O: "o",
        ecodes.KEY_P: "p", ecodes.KEY_Q: "q", ecodes.KEY_R: "r",
        ecodes.KEY_S: "s", ecodes.KEY_T: "t", ecodes.KEY_U: "u",
        ecodes.KEY_V: "v", ecodes.KEY_W: "w", ecodes.KEY_X: "x",
        ecodes.KEY_Y: "y", ecodes.KEY_Z: "z",

        ecodes.KEY_1: "1", ecodes.KEY_2: "2", ecodes.KEY_3: "3",
        ecodes.KEY_4: "4", ecodes.KEY_5: "5", ecodes.KEY_6: "6",
        ecodes.KEY_7: "7", ecodes.KEY_8: "8", ecodes.KEY_9: "9",
        ecodes.KEY_0: "0",

        ecodes.KEY_MINUS: "-", ecodes.KEY_EQUAL: "=",
        ecodes.KEY_DOT: ".", ecodes.KEY_COMMA: ",",
        ecodes.KEY_SLASH: "/", ecodes.KEY_SEMICOLON: ";",
        ecodes.KEY_APOSTROPHE: "'", ecodes.KEY_LEFTBRACE: "[",
        ecodes.KEY_RIGHTBRACE: "]", ecodes.KEY_BACKSLASH: "\\",
        ecodes.KEY_GRAVE: "`",
    }

    SHIFT_KEYMAP = {
        ecodes.KEY_A: "A", ecodes.KEY_B: "B", ecodes.KEY_C: "C",
        ecodes.KEY_D: "D", ecodes.KEY_E: "E", ecodes.KEY_F: "F",
        ecodes.KEY_G: "G", ecodes.KEY_H: "H", ecodes.KEY_I: "I",
        ecodes.KEY_J: "J", ecodes.KEY_K: "K", ecodes.KEY_L: "L",
        ecodes.KEY_M: "M", ecodes.KEY_N: "N", ecodes.KEY_O: "O",
        ecodes.KEY_P: "P", ecodes.KEY_Q: "Q", ecodes.KEY_R: "R",
        ecodes.KEY_S: "S", ecodes.KEY_T: "T", ecodes.KEY_U: "U",
        ecodes.KEY_V: "V", ecodes.KEY_W: "W", ecodes.KEY_X: "X",
        ecodes.KEY_Y: "Y", ecodes.KEY_Z: "Z",

        ecodes.KEY_1: "!", ecodes.KEY_2: "@", ecodes.KEY_3: "#",
        ecodes.KEY_4: "$", ecodes.KEY_5: "%", ecodes.KEY_6: "^",
        ecodes.KEY_7: "&", ecodes.KEY_8: "*", ecodes.KEY_9: "(",
        ecodes.KEY_0: ")",

        ecodes.KEY_MINUS: "_", ecodes.KEY_EQUAL: "+",
        ecodes.KEY_DOT: ">", ecodes.KEY_COMMA: "<",
        ecodes.KEY_SLASH: "?", ecodes.KEY_SEMICOLON: ":",
        ecodes.KEY_APOSTROPHE: '"', ecodes.KEY_LEFTBRACE: "{",
        ecodes.KEY_RIGHTBRACE: "}", ecodes.KEY_BACKSLASH: "|",
        ecodes.KEY_GRAVE: "~",
    }
else:
    try:
        from pynput import keyboard
        from pynput.keyboard import Key, Controller, Listener
    except ImportError:
        print("To run on Windows/macOS, please install pynput: pip install pynput")
        sys.exit(1)


shortcuts = {}
shortcuts_last_mtime = 0


def load_shortcuts():
    global shortcuts_last_mtime
    loaded = {}
    path = Path(SHORTCUT_FILE)

    if not path.exists():
        print(f"Missing {SHORTCUT_FILE}")
        return loaded

    try:
        shortcuts_last_mtime = path.stat().st_mtime
    except Exception:
        pass

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            if not line.strip():
                continue

            # Ignore espanso-style header line if present
            if line.startswith(":espanso:"):
                continue

            if ":" not in line:
                continue

            trigger, replacement = line.split(":", 1)

            trigger = trigger.strip()

            # Normalize invisible spaces from your shortcut file
            replacement = replacement.replace("\u200a", " ")
            replacement = replacement.replace("\u2009", " ")
            replacement = replacement.replace("\u200b", "")
            replacement = replacement.replace("\xa0", " ")

            if trigger:
                loaded[trigger] = replacement

    return loaded


if IS_LINUX:
    # Reverse mapping of character to keycode + shift status
    for keycode, char in LOWER_KEYMAP.items():
        CHAR_TO_KEY[char] = (keycode, False)
    for keycode, char in SHIFT_KEYMAP.items():
        CHAR_TO_KEY[char] = (keycode, True)

    # Special characters
    CHAR_TO_KEY[" "] = (ecodes.KEY_SPACE, False)
    CHAR_TO_KEY["\n"] = (ecodes.KEY_ENTER, False)
    CHAR_TO_KEY["\t"] = (ecodes.KEY_TAB, False)


def can_type_directly(text):
    if len(text) > 50:
        return False
    if "\\n" in text or "\n" in text:
        return False
    return all(char in CHAR_TO_KEY for char in text)


def type_text(ui, text):
    for char in text:
        if char not in CHAR_TO_KEY:
            continue
        keycode, shift = CHAR_TO_KEY[char]
        if shift:
            ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
            ui.syn()
            time.sleep(KEY_DELAY)

        ui.write(ecodes.EV_KEY, keycode, 1)
        ui.syn()
        time.sleep(KEY_DELAY)
        ui.write(ecodes.EV_KEY, keycode, 0)
        ui.syn()
        time.sleep(KEY_DELAY)

        if shift:
            ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
            ui.syn()
            time.sleep(KEY_DELAY)


def check_reload_shortcuts():
    global shortcuts, shortcuts_last_mtime
    path = Path(SHORTCUT_FILE)
    if not path.exists():
        return
    try:
        mtime = path.stat().st_mtime
        if mtime > shortcuts_last_mtime:
            print("Reloading shortcuts...")
            shortcuts = load_shortcuts()
            shortcuts_last_mtime = mtime
    except Exception as e:
        print(f"Error checking/reloading shortcuts: {e}")


def choose_keyboard():
    devices = [InputDevice(path) for path in list_devices()]
    keyboards = []

    for dev in devices:
        caps = dev.capabilities()
        keys = caps.get(ecodes.EV_KEY, [])

        if ecodes.KEY_A in keys and ecodes.KEY_SPACE in keys:
            # Avoid selecting our own virtual device
            name = dev.name.lower()
            if "uinput" in name or "py-evdev" in name:
                continue

            keyboards.append(dev)

    if not keyboards:
        raise RuntimeError("No real keyboard device found.")

    print("Available keyboards:")

    for index, dev in enumerate(keyboards):
        print(f"{index}: {dev.path} | {dev.name}")

    choice = int(input("Select keyboard number: "))
    return keyboards[choice]


def emit_key(ui, key_code):
    ui.write(ecodes.EV_KEY, key_code, 1)
    ui.syn()
    time.sleep(KEY_DELAY)

    ui.write(ecodes.EV_KEY, key_code, 0)
    ui.syn()
    time.sleep(KEY_DELAY)


def emit_combo_ctrl_v(ui):
    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
    ui.syn()
    time.sleep(KEY_DELAY)

    ui.write(ecodes.EV_KEY, ecodes.KEY_V, 1)
    ui.syn()
    time.sleep(KEY_DELAY)

    ui.write(ecodes.EV_KEY, ecodes.KEY_V, 0)
    ui.syn()
    time.sleep(KEY_DELAY)

    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
    ui.syn()
    time.sleep(KEY_DELAY)


def backspace(ui, count):
    for _ in range(count):
        emit_key(ui, ecodes.KEY_BACKSPACE)


def get_clipboard_env():
    env = os.environ.copy()

    # When running with sudo, make Wayland clipboard work better.
    sudo_uid = env.get("SUDO_UID")

    if sudo_uid:
        env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{sudo_uid}")

    env.setdefault("WAYLAND_DISPLAY", "wayland-0")

    return env


def copy_to_clipboard(text):
    env = get_clipboard_env()
    session_type = env.get("XDG_SESSION_TYPE", "").lower()

    wl_copy = shutil.which("wl-copy")
    xclip = shutil.which("xclip")

    # Prefer wl-copy on Wayland
    if session_type == "wayland" and wl_copy:
        subprocess.run(
            [wl_copy],
            input=text,
            text=True,
            env=env,
            check=True
        )
        return

    # Prefer xclip on X11
    if xclip:
        subprocess.run(
            [xclip, "-selection", "clipboard"],
            input=text,
            text=True,
            env=env,
            check=True
        )
        return

    # Fallback to wl-copy if available
    if wl_copy:
        subprocess.run(
            [wl_copy],
            input=text,
            text=True,
            env=env,
            check=True
        )
        return

    raise RuntimeError("No clipboard tool found. Install wl-clipboard or xclip.")


def paste_text(ui, text):
    if not text:
        return

    copy_to_clipboard(text)
    time.sleep(PASTE_DELAY)
    emit_combo_ctrl_v(ui)
    time.sleep(PASTE_DELAY)


def paste_text_with_virtual_enter(ui, text):
    """
    Literal \\n in shortcuts.txt means:
    paste text before it, then press Enter.
    Example:
    bs:<@716390085896962058> c bisasam\\n
    """
    parts = text.split("\\n")

    for index, part in enumerate(parts):
        if part:
            paste_text(ui, part)

        if index < len(parts) - 1:
            time.sleep(0.02)
            emit_key(ui, ecodes.KEY_ENTER)
            time.sleep(0.02)


def expand(ui, trigger, replacement):
    global is_expanding, last_expand_time

    if is_expanding:
        return

    is_expanding = True

    try:
        # Let the target app receive the original trigger + space first
        time.sleep(EXPAND_DELAY)

        # Delete trigger + typed space
        backspace(ui, len(trigger) + 1)

        time.sleep(0.02)

        # Choose between direct typing and clipboard pasting
        if can_type_directly(replacement):
            type_text(ui, replacement)
        else:
            paste_text_with_virtual_enter(ui, replacement)

        last_expand_time = time.monotonic()

    except subprocess.CalledProcessError as e:
        print(f"Clipboard command failed: {e}")
    except Exception as e:
        print(f"Expansion failed: {e}")

    finally:
        time.sleep(EXPAND_COOLDOWN)
        is_expanding = False


def main_linux():
    global enabled, word_buffer, shift_pressed
    global is_expanding, last_expand_time, shortcuts

    shortcuts = load_shortcuts()

    if not shortcuts:
        print("No shortcuts loaded. Will check shortcuts.txt again if created.")

    keyboard = choose_keyboard()
    ui = UInput()

    print("Text expander running (Linux evdev engine).")
    print("Tap RIGHT_CTRL to toggle ON/OFF.")
    print(f"Loaded {len(shortcuts)} shortcuts.")
    print("Use sudo -E python main.py if clipboard paste fails.")

    for event in keyboard.read_loop():
        if event.type != ecodes.EV_KEY:
            continue

        key = event.code
        value = event.value

        # Ignore key hold/repeat
        if value == 2:
            continue

        if key in (ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT):
            shift_pressed = value == 1
            continue

        # Single RIGHT_CTRL toggle
        if key == ecodes.KEY_RIGHTCTRL and value == 1:
            enabled = not enabled
            state = "ON" if enabled else "OFF"
            print(f"Expander toggled {state}")
            continue

        if not enabled:
            continue

        # Only handle key down
        if value != 1:
            continue

        # Periodically check for config file changes
        check_reload_shortcuts()

        if key == ecodes.KEY_SPACE:
            now = time.monotonic()
            trigger = word_buffer

            if is_expanding or now - last_expand_time < EXPAND_COOLDOWN:
                word_buffer = ""
                continue

            if trigger in shortcuts:
                print(f"Expanding: {trigger}")
                word_buffer = ""
                expand(ui, trigger, shortcuts[trigger])
            else:
                word_buffer = ""

            continue

        if key == ecodes.KEY_BACKSPACE:
            word_buffer = word_buffer[:-1]
            continue

        if key == ecodes.KEY_ENTER:
            word_buffer = ""
            continue

        current_map = SHIFT_KEYMAP if shift_pressed else LOWER_KEYMAP

        if key in current_map:
            word_buffer += current_map[key]

            if len(word_buffer) > 100:
                word_buffer = word_buffer[-100:]

            continue

        # Other keys should break trigger detection
        word_buffer = ""


def paste_text_pynput(text):
    # Support literal \n
    text = text.replace("\\n", "\n")
    try:
        import pyperclip
        pyperclip.copy(text)
        time.sleep(PASTE_DELAY)

        controller = Controller()
        if sys.platform == "darwin":
            controller.press(Key.cmd)
            controller.press('v')
            controller.release('v')
            controller.release(Key.cmd)
        else:
            controller.press(Key.ctrl)
            controller.press('v')
            controller.release('v')
            controller.release(Key.ctrl)
        time.sleep(PASTE_DELAY)
    except ImportError:
        controller = Controller()
        controller.type(text)


def expand_pynput(trigger, replacement):
    global is_expanding, last_expand_time
    is_expanding = True
    try:
        time.sleep(EXPAND_DELAY)

        controller = Controller()
        # Backspace trigger + space
        for _ in range(len(trigger) + 1):
            controller.press(Key.backspace)
            controller.release(Key.backspace)
            time.sleep(0.002)

        time.sleep(0.02)

        if "\n" in replacement or "\\n" in replacement or len(replacement) > 50:
            paste_text_pynput(replacement)
        else:
            controller.type(replacement)

        last_expand_time = time.monotonic()
    except Exception as e:
        print(f"Expansion failed: {e}")
    finally:
        time.sleep(EXPAND_COOLDOWN)
        is_expanding = False


def on_press_pynput(key):
    global word_buffer, enabled, is_expanding, last_expand_time

    # Toggle enabled on RIGHT CTRL press
    if key == Key.ctrl_r:
        enabled = not enabled
        state = "ON" if enabled else "OFF"
        print(f"Expander toggled {state}")
        return

    if not enabled:
        return

    check_reload_shortcuts()

    # Check space trigger
    if key == Key.space:
        now = time.monotonic()
        trigger = word_buffer
        if is_expanding or now - last_expand_time < EXPAND_COOLDOWN:
            word_buffer = ""
            return

        if trigger in shortcuts:
            print(f"Expanding: {trigger}")
            word_buffer = ""
            expand_pynput(trigger, shortcuts[trigger])
        else:
            word_buffer = ""
        return

    if key == Key.backspace:
        word_buffer = word_buffer[:-1]
        return

    if key == Key.enter:
        word_buffer = ""
        return

    try:
        if hasattr(key, 'char') and key.char:
            word_buffer += key.char
            if len(word_buffer) > 100:
                word_buffer = word_buffer[-100:]
        else:
            word_buffer = ""
    except Exception:
        word_buffer = ""


def main_pynput():
    global shortcuts
    shortcuts = load_shortcuts()
    if not shortcuts:
        print("No shortcuts loaded. Will check shortcuts.txt again if created.")

    print("Text expander running (Cross-platform pynput engine).")
    print("Tap RIGHT_CTRL to toggle ON/OFF.")
    print(f"Loaded {len(shortcuts)} shortcuts.")

    with Listener(on_press=on_press_pynput) as listener:
        listener.join()


def main():
    if IS_LINUX:
        main_linux()
    else:
        main_pynput()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped text expander.")