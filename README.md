# MacroPad Firmware v2

Firmware for Adafruit MacroPad RP2040 with advanced macro management system.

## Features

### Hybrid Priority System
- **Press/Hold macros**: Have highest priority, can interrupt active macros
- **Toggle macros**: Execute through queue, don't interrupt each other

### SLOT + QUEUE System
- **12 SLOTS** (one per button): For instant execution
- **Queue up to 1000 macros**: For waiting Toggle macros
- Overflow protection: Check BEFORE adding

### Two-Level Timer System
- `action_wait_until`: Waiting between actions within macro
- `cycle_wait_until`: Waiting before next Toggle macro cycle

### 5 Macro States
1. **OFF** (default)
2. **ACTIVE** (executing action)
3. **WAIT** (waiting between actions)
4. **SLEEPING** (waiting before next cycle)
5. **IN_QUEUE** (waiting in queue)

### LED Indication
- **READY** (dim green): Macro ready to launch
- **ACTIVE** (blue): Macro executing action
- **WAIT** (yellow): Macro waiting between actions
- **SLEEPING** (green): Toggle macro sleeping until next cycle
- **IN_QUEUE** (purple): Toggle macro in queue

### OLED Display
Shows system state in real-time:
```
Test EXEC
/ #3 [T>] Farm
/ QUEUE: 2 [5...]
/ SLEEP: 1
```
- **EXEC**: Executing macros (SLOT)
- **QUEUE**: Count and names of waiting macros
- **SLEEP**: Count of sleeping macros

## File Structure

### Core Modules
- `code.py` - Entry point, main loop
- `macro_engine.py` - Macro execution coordination
- `macro_state.py` - Macro state management
- `queue_manager.py` - SLOT + QUEUE management
- `action_executor.py` - Action execution (keys, mouse)
- `color_manager.py` - LED indication management
- `display_manager.py` - OLED display management

### Helper Modules
- `key_mapping.py` - Button to macro mapping
- `profile_manager.py` - Profile management
- `macro_parser.py` - JSON configuration parsing

### Data
- `data/profiles/*.json` - Profiles with macros
- `data/current_profile.json` - Active profile
- `data/button_colors.json` - Button colors

## Macro Format

### Press (single press)
```json
{
  "name": "Single Press",
  "type": "press",
  "actions": [
    { "type": "press", "keys": "F1" }
  ]
}
```

### Hold (holding)
```json
{
  "name": "Hold Shift",
  "type": "hold",
  "actions": [
    { "type": "press", "keys": "Shift" }
  ]
}
```

### Toggle (cyclic execution)
```json
{
  "name": "Farm Loop",
  "type": "toggle",
  "wait": 15000,
  "actions": [
    { "type": "press", "keys": "8", "wait": 500 },
    { "type": "press", "keys": "Shift+Space" }
  ]
}
```

**Important**: The `wait` parameter at macro level sets the pause before the next cycle. Final `wait` from the last action was removed in v2.

## Deployment

### Clean Installation
1. Copy all `.py` files to CIRCUITPY root
2. Copy `data/` folder with profiles
3. MacroPad will automatically reboot

### Profile Switching
- Rotate encoder to select
- Press encoder to activate
- Current profile is saved to `current_profile.json`

## Troubleshooting

### Macro Won't Start
1. Check JSON syntax in profile
2. Ensure `"type"` is specified correctly
3. For Toggle macros check `"wait"` parameter

### Queue Overflow
- Maximum 1000 macros in queue
- On overflow macro is not added
- Check count via display

### LEDs Not Changing
- Check `color_manager.py`
- Ensure `update_all_leds()` is called in main loop

## Version History

### v2.0 (Current)
- Hybrid priority system
- SLOT + QUEUE architecture
- 5 explicit states
- Two-level timers
- New Toggle macro format (`wait` parameter)
- Improved LED indication
- Enhanced display with SLOT/QUEUE/SLEEP info

### v1.0
- Basic macro system
- Press/Hold/Toggle types
- Simple LED indication
- Profile system
