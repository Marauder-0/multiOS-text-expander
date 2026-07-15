# Cross-Platform Text Expander

A lightweight, high-performance, cross-platform text expander built with Python. It monitors keyboard inputs and automatically replaces trigger shortcuts with expanded text.

It uses a driver-level `evdev` backend on Linux for low latency, and a platform-agnostic `pynput` backend on Windows and macOS.

## Features

- **Hybrid Typing Engine**: Bypasses the clipboard for short replacements by typing characters directly via virtual keyboard events. This preserves your system clipboard history and eliminates clipboard latency.
- **Clipboard Fallback**: Smoothly falls back to clipboard copy-and-paste for long paragraphs or multi-line macros, preserving high performance.
- **Dynamic Config Reloading**: Automatically watches `shortcuts.txt` for updates. Simply save your edits to the file, and the changes will take effect immediately without needing to restart the script.
- **Toggle State**: Toggle the text expander ON or OFF at any time by pressing the `RIGHT_CTRL` key.

## Requirements & Installation

1. **Python 3** installed on your system.

2. **Dependencies**:
   - **Linux**:
     ```bash
     pip install evdev
     ```
     For long paragraph fallback expansions, install a clipboard utility:
     - **X11**: `xclip` (`sudo apt install xclip`)
     - **Wayland**: `wl-clipboard` (`sudo apt install wl-clipboard`)

   - **Windows / macOS**:
     ```bash
     pip install pynput
     ```
     *(Optional)* For clipboard fallback support on very long expansions:
     ```bash
     pip install pyperclip
     ```

## Getting Started

1. **Create your shortcuts file**:
   Create a `shortcuts.txt` file in the same directory as the script. Define your triggers and replacements separated by a colon (`:`):
   ```text
   btw: by the way
   gm: Good morning!
   shg: ¯\_(ツ)_/¯
   todo: - [ ] \n- [ ] 
   ```
   *Note: Use `\n` to insert a newline followed by an Enter key press.*

2. **Run the Text Expander**:
   - **Linux**:
     Because `evdev` interacts directly with Linux input devices, the script must be run with root privileges. Use the `-E` flag to preserve your user environment variables:
     ```bash
     sudo -E python3 main.py
     ```
     Select your keyboard index from the displayed list.

   - **Windows**:
     Run the script from an administrator PowerShell or Command Prompt:
     ```cmd
     python main.py
     ```

   - **macOS**:
     Run the script in the Terminal:
     ```bash
     python3 main.py
     ```
     *Note: You may need to grant Accessibility permissions to your Terminal application in System Preferences.*

3. **Toggle ON/OFF**:
   Tap the `RIGHT_CTRL` key to enable or disable expansion on the fly.
