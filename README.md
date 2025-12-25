# MacroPad Firmware

CircuitPython firmware for Adafruit MacroPad RP2040 with powerful macro system, profiles, and visual feedback.

## ✨ Features

- **12 programmable keys** with full RGB backlight
- **Profile switching** via encoder
- **Macro types**: Once (single press), Hold (press and hold), Toggle (on/off)
- **Loops and repetitions** with conditional exits
- **Emergency stop all macros** (encoder button press)
- **Custom colors** for each key
- **Keyboard and mouse actions**: key presses, clicks, movements, scrolling
- **OLED display** showing current profile

## 📦 Installation

1. Install CircuitPython 8.x on MacroPad
2. Copy all `.py` files to `CIRCUITPY` drive
3. Create `data/` folder structure or use [MacroPad Configurator](https://github.com/AlexanderPotashko/macropad-configurator)
4. Reset device (Ctrl+D or Ctrl+Shift+R in Serial console)

## 🎮 Usage

- **Keys 0-11**: Execute assigned macros
- **Encoder rotation**: Switch between profiles
- **Encoder press**: Emergency stop all active macros

## 📚 Documentation

Detailed documentation on creating macros and configuring profiles is available in [MACRO_DOCUMENTATION.md](MACRO_DOCUMENTATION.md).

## 🛠️ Tools

For visual editing of profiles and macros, use:

**[MacroPad Configurator](https://github.com/AlexanderPotashko/macropad-configurator)** - web application for convenient profile configuration, macro creation, and key color management.

## 📁 Project Structure

```
macropad-firmware/
├── code.py                 # Main program file
├── macro_engine.py         # Macro execution engine
├── macro_parser.py         # JSON configuration parser
├── profile_manager.py      # Profile management
├── display_manager.py      # OLED display management
├── color_manager.py        # RGB backlight management
├── key_mapping.py          # Key and action mapping
├── data/
│   ├── button_colors.json      # Color configuration
│   ├── current_profile.json    # Current active profile
│   └── profiles/               # Profiles folder
│       ├── default.json
│       └── ...
└── MACRO_DOCUMENTATION.md  # Complete documentation
```

## 🔧 Requirements

- Adafruit MacroPad RP2040
- CircuitPython 8.x
- Adafruit libraries (included in CircuitPython bundle)

## 📄 License

MIT

**Version:** 1.0.0
