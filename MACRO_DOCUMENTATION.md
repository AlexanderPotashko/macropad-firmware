# MacroPad v2 Macro Documentation (Remaster)

## 🎯 What's New in v2

**Hybrid Priority System:**
- ⚡ **Press** and **Hold** - priority macros (interrupt everything)
- 🔄 **Toggle** - queued macros (wait their turn in QUEUE)

**Key Changes:**
- `type: "once"` renamed to `type: "press"` (more intuitive name)
- `loop: true` no longer needed for Toggle - loops are automatic
- `wait` at macro level now only for Toggle (pause between cycles)
- SLOT + QUEUE system - one executes, others wait

---

## Table of Contents
1. [Profile Structure](#profile-structure)
2. [Macro Types](#macro-types)
3. [Action Types](#action-types)
4. [Pauses and Delays](#pauses-and-delays)
5. [Key Presses](#key-presses)
6. [Mouse Actions](#mouse-actions)
7. [Repeats](#repeats)
8. [Button Colors](#button-colors)
9. [Complete Examples](#complete-examples)

---

## Profile Structure

A profile is a JSON file containing the configuration for 12 MacroPad buttons.

```json
{
  "name": "Profile Name",
  "description": "Profile description (optional)",
  "buttons": [
    { /* Button 0 */ },
    { /* Button 1 */ },
    null,  // Button 2 not configured
    { /* Button 3 */ },
    // ... total 12 elements (0-11)
  ]
}
```

**Important:**
- The `buttons` array must contain exactly 12 elements
- `null` means the button is not used
- Indexes 0-11 correspond to physical buttons on the device

---

## Macro Types

### Macro Structure

```json
{
  "_id": "m_unique_id",
  "name": "Macro Name",
  "type": "press",
  "wait": 1000,
  "actions": [ /* list of actions */ ]
}
```

### Macro Parameters

| Parameter | Type | Required | Description |
|----------|-----|----------|-------------|
| `_id` | string | Yes | Unique macro identifier |
| `name` | string | Yes | Macro name (displayed on screen) |
| `type` | string | Yes | Macro type: `press`, `hold`, `toggle` |
| `wait` | number | No | **Toggle only:** pause between cycles in ms |
| `actions` | array | Yes | Array of actions to execute |
| `colors` | object | No | Button LED color configuration |

---

### 1. 🔵 Press - Priority Single Execution

**Behavior:**
- ⚡ Interrupts any current macro (even Toggle)
- 🚀 Executes immediately (doesn't wait in queue)
- ✅ Executes all actions once and stops

**When to use:** Quick actions that should trigger instantly.

```json
{
  "_id": "quick_save",
  "name": "Quick Save",
  "type": "press",
  "actions": [
    { "type": "press", "keys": "Ctrl+S" }
  ]
}
```

**Example with multiple actions:**
```json
{
  "_id": "screenshot",
  "name": "Screenshot",
  "type": "press",
  "actions": [
    { "type": "press", "keys": "Windows+Shift+S", "wait": 500 },
    { "type": "wait", "ms": 200 },
    { "type": "press", "keys": "Ctrl+V" }
  ]
}
```

---

### 2. 🟠 Hold - Priority Hold Execution

**Behavior:**
- ⚡ Interrupts any current macro
- 🔁 Executes cyclically while button is held
- ⏹️ Stops when button is released

**When to use:** Actions that should repeat while button is pressed.

```json
{
  "_id": "auto_fire",
  "name": "Auto Fire",
  "type": "hold",
  "actions": [
    { "type": "click", "button": 1, "wait": 100 }
  ]
}
```

**Hold Macro Conflict:**
- If two Hold buttons are pressed simultaneously → the last pressed interrupts the previous one
- When releasing one button, the other does NOT resume

**Complex Hold Example:**
```json
{
  "_id": "sprint_jump",
  "name": "Sprint + Jump",
  "type": "hold",
  "actions": [
    { "type": "press", "keys": "Shift", "wait": 50 },
    { "type": "press", "keys": "Space", "wait": 450 }
  ]
}
```

---

### 3. 🟢 Toggle - Queued Cyclic Execution

**Behavior:**
- 📋 If SLOT is busy → enters QUEUE
- 🔁 Executes cyclically until pressed again
- ⏸️ When interrupted by Press/Hold → transitions to SLEEPING
- ✅ Automatically resumes after `wait` time

**When to use:** Background tasks, automation, farming.

```json
{
  "_id": "auto_clicker",
  "name": "Auto Clicker",
  "type": "toggle",
  "wait": 1000,
  "actions": [
    { "type": "click", "button": 1 }
  ]
}
```

**`wait` Parameter:**
- Specified in milliseconds
- This is the pause **between cycles** (after all actions complete)
- If not specified or 0 - cycle repeats without pause

**Toggle Cancellation:**
- Pressing the same button again → macro stops
- Works even if macro is in queue (IN_QUEUE)

**Example with macro.wait:**
```json
{
  "_id": "farm_macro",
  "name": "Farm Resources",
  "type": "toggle",
  "wait": 60000,
  "actions": [
    { "type": "press", "keys": "F1", "wait": 1000 },
    { "type": "press", "keys": "F2", "wait": 500 },
    { "type": "wait", "ms": 5000 }
  ]
}
```

**Toggle Execution Cycle:**
1. Executes action 1 → waits `action.wait` (1000ms)
2. Executes action 2 → waits `action.wait` (500ms)
3. Executes action 3 (wait) → waits 5000ms
4. All actions completed → releases SLOT
5. Transitions to SLEEPING → waits `macro.wait` (60000ms)
6. Wakes up → enters queue (or takes SLOT if free)
7. Repeats from step 1

---

## Priorities and Queue

### Hybrid System

| Type | Priority | Behavior when SLOT is busy |
|-----|----------|---------------------------|
| **Press** | ⚡ High | Interrupts current macro |
| **Hold** | ⚡ High | Interrupts current macro |
| **Toggle** | 📋 Queue | Enters QUEUE |

### Toggle Macro Interruption

When Press/Hold interrupts Toggle:

```
[Before]
Toggle executing → action 2 of 5

[Press triggered]
Toggle → SLEEPING (saves timer)
Press → SLOT (executes immediately)

[Press completed]
SLOT is released
process_queue() → Toggle returns to SLOT

[Toggle resumes]
❌ Does NOT continue from action 2
✅ Starts OVER from action 1
```

**Important:** Toggle always starts from the beginning after interruption (simplicity and predictability).

---

### Queue (QUEUE)

- **Maximum:** 1000 macros
- **Order:** FIFO (First In, First Out)
- **Duplicates:** Forbidden (one macro cannot be in queue twice)
- **Overflow:** When limit is reached → emergency stop of all macros

**Display on screen:**
```
Test         EXEC   ← Profile + status
#3 [T>] Farm       ← SLOT (Toggle active)
QUEUE: 2 [5...]    ← Queue size + first in line
SLEEP: 1 | Enc=STOP ← Sleeping macros
```

---

## Macro States and LED Colors

| State | Color | RGB | Description |
|-------|-------|-----|-------------|
| **READY** | 🟢 Dim green | (0, 40, 0) | Ready to launch |
| **ACTIVE** | 🔵 Blue | (0, 80, 255) | Executing action |
| **WAIT** | 🟡 Yellow | (255, 200, 0) | Waiting between actions |
| **SLEEPING** | 🟢 Bright green | (0, 255, 0) | Toggle waiting macro.wait |
| **IN_QUEUE** | 🟣 Purple | (200, 0, 200) | Waiting in queue |
| **OFF** | ⚫ Black | (0, 0, 0) | Not configured |

---

## Action Types

### 1. Key Press - `press`

Simulates a complete key press cycle (press → release).

```json
{
  "type": "press",
  "keys": "F1",
  "wait": 1000
}
```

**Parameters:**
- `keys` (string, required) - key or key combination
- `wait` (number, optional) - pause after press in milliseconds
- `wait_random` (object, optional) - random pause (see "Pauses" section)

### 1.1. Key Press Down - `press_down`

Presses key(s) without releasing. Used for precise control over key presses.

```json
{
  "type": "press_down",
  "keys": "Shift",
  "wait": 100
}
```

**Parameters:**
- `keys` (string, required) - key or key combination to press down
- `wait` (number, optional) - pause after pressing in milliseconds
- `wait_random` (object, optional) - random pause

**⚠️ Important:** After `press_down` must always follow `press_up` for the same keys, otherwise they will remain pressed. When macro stops, all keys are automatically released.

### 1.2. Key Press Up - `press_up`

Releases previously pressed keys.

```json
{
  "type": "press_up",
  "keys": "Shift",
  "wait": 1000
}
```

**Parameters:**
- `keys` (string, required) - key or key combination to release
- `wait` (number, optional) - pause after release in milliseconds
- `wait_random` (object, optional) - random pause

**Example using `press_down` / `press_up`:**

```json
{
  "actions": [
    { "type": "press_down", "keys": "Shift", "wait": 100 },
    { "type": "press", "keys": "Space", "wait": 50 },
    { "type": "press_up", "keys": "Shift", "wait": 1000 }
  ]
}
```

This provides precise control: Shift is pressed → wait 100ms → press Space (while Shift held) → wait 50ms → release Shift → wait 1000ms.

### 2. Text Input - `type`

Types text as if user is typing on keyboard.

```json
{
  "type": "type",
  "text": "Hello World!",
  "wait": 500
}
```

**Parameters:**
- `text` (string, required) - text to input
- `wait` (number, optional) - pause after input in milliseconds
- `wait_random` (object, optional) - random pause

### 3. Pause - `wait`

Waits for specified number of milliseconds.

```json
{
  "type": "wait",
  "ms": 5000
}
```

**Parameters:**
- `ms` (number, required) - wait time in milliseconds

### 4. Random Pause - `wait_random`

Waits for random time within specified range.

```json
{
  "type": "wait_random",
  "min": 1000,
  "max": 3000
}
```

**Parameters:**
- `min` (number, required) - minimum time in milliseconds
- `max` (number, required) - maximum time in milliseconds

### 5. Mouse Click - `mouse_click`

Simulates mouse button click.

```json
{
  "type": "mouse_click",
  "button": "left",
  "wait": 100
}
```

**Parameters:**
- `button` (string, optional) - mouse button: `"left"`, `"right"`, `"middle"` (default: `"left"`)
- `wait` (number, optional) - pause after click in milliseconds
- `wait_random` (object, optional) - random pause

### 6. Mouse Movement - `mouse_move`

Moves mouse cursor relative to current position.

```json
{
  "type": "mouse_move",
  "x": 10,
  "y": -5,
  "wait": 100
}
```

**Parameters:**
- `x` (number, required) - horizontal offset (+ right, - left)
- `y` (number, required) - vertical offset (+ down, - up)
- `wait` (number, optional) - pause after movement
- `wait_random` (object, optional) - random pause

### 7. Mouse Scroll - `mouse_scroll`

Scrolls mouse wheel.

```json
{
  "type": "mouse_scroll",
  "amount": 5,
  "wait": 200
}
```

**Parameters:**
- `amount` (number, required) - scroll amount (+ up, - down)
- `wait` (number, optional) - pause after scroll
- `wait_random` (object, optional) - random pause

### 8. Repeat - `repeat`

Repeats a group of actions specified number of times.

```json
{
  "type": "repeat",
  "count": 5,
  "actions": [
    { "type": "press", "keys": "Space", "wait": 100 },
    { "type": "wait", "ms": 500 }
  ]
}
```

**Parameters:**
- `count` (number, required) - number of repetitions
- `actions` (array, required) - array of actions to repeat

---

## Паузы и задержки

### Built-in Pause (`wait`)

All actions except `wait` and `wait_random` support the built-in `wait` parameter:

```json
{ "type": "press", "keys": "F1", "wait": 1000 }
```

This is equivalent to:

```json
{ "type": "press", "keys": "F1" },
{ "type": "wait", "ms": 1000 }
```

### Random Pause (`wait_random`)

You can specify a built-in random pause:

```json
{
  "type": "press",
  "keys": "F1",
  "wait_random": {
    "min": 500,
    "max": 1500
  }
}
```

Or as a separate action:

```json
{
  "type": "wait_random",
  "min": 500,
  "max": 1500
}
```

### Pause Usage Examples

**Fixed pause:**
```json
{ "type": "press", "keys": "F1", "wait": 1000 }
```

**Random pause (more natural):**
```json
{
  "type": "press",
  "keys": "F1",
  "wait_random": { "min": 800, "max": 1200 }
}
```

**No pause (next action executes immediately):**
```json
{ "type": "press", "keys": "F1" }
```

---

## Key Presses

### Single Keys

```json
{ "type": "press", "keys": "A" }
{ "type": "press", "keys": "1" }
{ "type": "press", "keys": "F5" }
{ "type": "press", "keys": "Enter" }
{ "type": "press", "keys": "Space" }
```

### Key Combinations

Use `+` for combinations:

```json
{ "type": "press", "keys": "Ctrl+C" }
{ "type": "press", "keys": "Shift+A" }
{ "type": "press", "keys": "Ctrl+Shift+Esc" }
{ "type": "press", "keys": "Alt+F4" }
{ "type": "press", "keys": "Win+1" }
```

### Supported Keys

**Letters:** A-Z

**Numbers:** 0-9

**Function Keys:** F1-F12

**Modifiers:**
- `Ctrl`, `Control` - Control
- `Shift` - Shift
- `Alt`, `Option` - Alt
- `Win`, `GUI`, `Windows`, `Cmd`, `Command` - Windows/Command key

**Special Keys:**
- `Enter`, `Return` - Enter
- `Escape`, `Esc` - Escape
- `Backspace` - Backspace
- `Tab` - Tab
- `Space`, `Spacebar` - Space
- `Delete` - Delete
- `Insert` - Insert
- `Home`, `End` - Home/End
- `PageUp`, `PageDown` - Page Up/Down

**Arrows:**
- `Up`, `Down`, `Left`, `Right`
- `Up_Arrow`, `Down_Arrow`, `Left_Arrow`, `Right_Arrow`

**Punctuation:**
- `Minus` - minus
- `Equals` - equals
- `Left_Bracket`, `Right_Bracket` - brackets [ ]
- `Backslash` - backslash
- `Semicolon` - semicolon
- `Quote` - quote
- `Comma` - comma
- `Period` - period
- `Forward_Slash` - forward slash

**Other:**
- `Caps_Lock` - Caps Lock
- `Print_Screen` - Print Screen
- `Scroll_Lock` - Scroll Lock
- `Pause` - Pause

### Combination Examples

```json
// Save file
{ "type": "press", "keys": "Ctrl+S" }

// Copy
{ "type": "press", "keys": "Ctrl+C" }

// Paste
{ "type": "press", "keys": "Ctrl+V" }

// Switch window
{ "type": "press", "keys": "Alt+Tab" }

// Switch to window 1
{ "type": "press", "keys": "Win+1" }

// Open task manager
{ "type": "press", "keys": "Ctrl+Shift+Esc" }

// Close window
{ "type": "press", "keys": "Alt+F4" }
```

---

## Mouse Actions

### Mouse Click

```json
// Left button (default)
{ "type": "mouse_click", "button": "left" }

// Right button
{ "type": "mouse_click", "button": "right" }

// Middle button (wheel)
{ "type": "mouse_click", "button": "middle" }

// With pause after click
{ "type": "mouse_click", "button": "left", "wait": 500 }

// With random pause
{
  "type": "mouse_click",
  "button": "left",
  "wait_random": { "min": 100, "max": 300 }
}
```

### Mouse Movement

```json
// Move right 10 pixels
{ "type": "mouse_move", "x": 10, "y": 0 }

// Move up 20 pixels
{ "type": "mouse_move", "x": 0, "y": -20 }

// Diagonal movement
{ "type": "mouse_move", "x": 15, "y": 10 }
```

### Mouse Scroll

```json
// Scroll up
{ "type": "mouse_scroll", "amount": 5 }

// Scroll down
{ "type": "mouse_scroll", "amount": -5 }

// Fast scroll
{ "type": "mouse_scroll", "amount": 10 }
```

### Example: Auto Clicker

```json
{
  "_id": "m_autoclicker",
  "name": "Auto Clicker",
  "type": "toggle",
  "loop": true,
  "actions": [
    { "type": "mouse_click", "button": "left", "wait": 100 }
  ]
}
```

### Example: Double Click with Pause

```json
{
  "_id": "m_doubleclick",
  "name": "Double Click",
  "type": "toggle",
  "loop": true,
  "actions": [
    { "type": "mouse_click", "button": "left", "wait": 50 },
    { "type": "mouse_click", "button": "left", "wait": 5000 }
  ]
}
```

---

## Repeats (Repeat)

The `repeat` action allows you to repeat a group of actions multiple times.

### Syntax

```json
{
  "type": "repeat",
  "count": 5,
  "actions": [
    /* actions to repeat */
  ]
}
```

### Examples

**Press spacebar 10 times:**
```json
{
  "type": "repeat",
  "count": 10,
  "actions": [
    { "type": "press", "keys": "Space", "wait": 100 }
  ]
}
```

**Rapid clicks:**
```json
{
  "type": "repeat",
  "count": 5,
  "actions": [
    { "type": "mouse_click", "button": "left", "wait": 50 }
  ]
}
```

**Complex sequence:**
```json
{
  "type": "repeat",
  "count": 3,
  "actions": [
    { "type": "press", "keys": "1", "wait": 200 },
    { "type": "press", "keys": "2", "wait": 200 },
    { "type": "press", "keys": "3", "wait": 1000 }
  ]
}
```

**Nested repeats (supported):**
```json
{
  "type": "repeat",
  "count": 2,
  "actions": [
    {
      "type": "repeat",
      "count": 3,
      "actions": [
        { "type": "press", "keys": "A", "wait": 100 }
      ]
    },
    { "type": "wait", "ms": 500 }
  ]
}
```

---

## Button Colors

You can configure the button backlight color for different states.

### `colors` Structure

```json
{
  "_id": "m_example",
  "name": "Example",
  "type": "toggle",
  "colors": {
    "ready": [0, 255, 0],      // Green - ready to run
    "active": [255, 0, 0],     // Red - running
    "waiting": [255, 255, 0]   // Yellow - waiting
  },
  "actions": [ /* ... */ ]
}
```

### Available States

- `ready` - button in SLEEP mode (green) - waiting for timer between cycles
- `loop` - button ACTIVE (blue) - executing actions, owns the slot
- `wait` - button in WAIT mode (yellow) - waiting between actions, holds slot
- `queued` - button in queue (purple) - woke up, waiting for slot to be freed

**Note:** States are applied automatically depending on what the macro is doing.
- **SLEEP (ready/green)**: Macro is enabled, but waiting for timer between loop iterations
- **IN_QUEUE (queued/purple)**: Timer expired, but slot is occupied by another macro
- **ACTIVE (loop/blue)**: Executing action sequence
- **WAIT (wait/yellow)**: Pause between actions within one iteration

### Color Format

Color is specified as an RGB array: `[R, G, B]`
- Values from 0 to 255
- For example: `[255, 0, 0]` - red, `[0, 255, 0]` - green, `[0, 0, 255]` - blue

### Color Examples

```json
[255, 0, 0]     // Red
[0, 255, 0]     // Green
[0, 0, 255]     // Blue
[255, 255, 0]   // Yellow
[255, 0, 255]   // Magenta
[0, 255, 255]   // Cyan
[255, 255, 255] // White
[128, 0, 128]   // Purple
[255, 165, 0]   // Orange
```

---

## Complete Examples

### Example 1: Simple Key Press Every 240 Seconds

```json
{
  "_id": "m_1734350001",
  "name": "F5 Every 240s",
  "type": "toggle",
  "loop": true,
  "actions": [
    {
      "type": "press",
      "keys": "F5",
      "wait": 240000
    }
  ]
}
```

### Example 2: Combo Attack (F7-3-F6-3 with Pauses)

```json
{
  "_id": "m_combo",
  "name": "Combo F7-3-F6-3",
  "type": "toggle",
  "loop": true,
  "actions": [
    { "type": "press", "keys": "F7", "wait": 250 },
    { "type": "press", "keys": "3", "wait": 250 },
    { "type": "press", "keys": "F6", "wait": 250 },
    { "type": "press", "keys": "3", "wait": 250 }
  ]
}
```

### Example 3: Quick Action Every 15 Seconds

```json
{
  "_id": "m_quick",
  "name": "F4 Every 15s",
  "type": "toggle",
  "loop": true,
  "actions": [
    {
      "type": "press",
      "keys": "F4",
      "wait": 15000
    }
  ]
}
```

### Example 4: Mouse Auto Clicker with Double Click

```json
{
  "_id": "m_mouseloop",
  "name": "Mouse Click Loop",
  "type": "toggle",
  "loop": true,
  "actions": [
    { "type": "mouse_click", "button": "left", "wait": 1000 },
    { "type": "mouse_click", "button": "left", "wait": 10000 }
  ]
}
```

### Example 5: Complex Farm Macro

```json
{
  "_id": "m_farm",
  "name": "Window 1 Farm",
  "type": "toggle",
  "loop": true,
  "actions": [
    { "type": "press", "keys": "Win+1", "wait": 3000 },
    { "type": "press", "keys": "F1", "wait": 1000 },
    { "type": "press", "keys": "F2", "wait": 1000 },
    { "type": "press", "keys": "F3", "wait": 1000 },
    { "type": "wait", "ms": 10000 },
    { "type": "press", "keys": "F4", "wait": 1000 },
    { "type": "press", "keys": "Win+3", "wait": 3000 },
    { "type": "wait", "ms": 300000 }
  ]
}
```

### Example 6: Rapid Click Series with Repeat

```json
{
  "_id": "m_rapidfire",
  "name": "Rapid Fire",
  "type": "once",
  "actions": [
    {
      "type": "repeat",
      "count": 10,
      "actions": [
        { "type": "mouse_click", "button": "left", "wait": 50 }
      ]
    }
  ]
}
```

### Example 7: Macro with Random Pauses (More Natural)

```json
{
  "_id": "m_natural",
  "name": "Natural Farming",
  "type": "toggle",
  "loop": true,
  "actions": [
    {
      "type": "press",
      "keys": "F1",
      "wait_random": { "min": 900, "max": 1100 }
    },
    {
      "type": "mouse_click",
      "button": "left",
      "wait_random": { "min": 2000, "max": 3000 }
    },
    {
      "type": "press",
      "keys": "Space",
      "wait_random": { "min": 5000, "max": 7000 }
    }
  ]
}
```

### Example 8: Macro with Colors

```json
{
  "_id": "m_colored",
  "name": "Colored Macro",
  "type": "toggle",
  "loop": true,
  "colors": {
    "ready": [0, 255, 0],
    "active": [255, 0, 0],
    "waiting": [255, 255, 0]
  },
  "actions": [
    { "type": "press", "keys": "F1", "wait": 5000 }
  ]
}
```

### Example 9: Complete Profile

```json
{
  "name": "Gaming Profile",
  "buttons": [
    {
      "_id": "m_001",
      "name": "Combo Attack",
      "type": "toggle",
      "loop": true,
      "actions": [
        { "type": "press", "keys": "F7", "wait": 250 },
        { "type": "press", "keys": "3", "wait": 250 },
        { "type": "press", "keys": "F6", "wait": 250 },
        { "type": "press", "keys": "3", "wait": 250 }
      ]
    },
    {
      "_id": "m_002",
      "name": "Quick Action",
      "type": "toggle",
      "loop": true,
      "actions": [
        { "type": "press", "keys": "F4", "wait": 15000 }
      ]
    },
    {
      "_id": "m_003",
      "name": "Long Timer",
      "type": "toggle",
      "loop": true,
      "actions": [
        { "type": "press", "keys": "F8", "wait": 240000 }
      ]
    },
    {
      "_id": "m_004",
      "name": "Auto Clicker",
      "type": "toggle",
      "loop": true,
      "actions": [
        { "type": "mouse_click", "button": "left", "wait": 1000 },
        { "type": "mouse_click", "button": "left", "wait": 10000 }
      ]
    },
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null
  ]
}
```

---

## Tips and Best Practices

### Wait Times

- **Short pauses (50-300 ms):** for quick combos
- **Medium pauses (1-5 seconds):** for regular actions
- **Long pauses (10+ seconds):** for waiting for loading/cooldown

### Using loop

- For infinite macros (farm, auto clicker) use `"loop": true` with `toggle` type
- For one-time actions use `"type": "once"` without `loop`

### Random Pauses

Use `wait_random` for more natural behavior:
```json
"wait_random": { "min": 900, "max": 1100 }
```
instead of fixed pause `"wait": 1000`

### Key Combinations

- Modifiers come first: `"Ctrl+C"`, `"Shift+Alt+F1"`
- Case doesn't matter: `"CTRL+C"` = `"ctrl+c"` = `"Ctrl+C"`
- Use `Win` for Windows, `Cmd` for Mac

### Testing

1. Start with a simple macro
2. Test each action
3. Gradually add complexity
4. Use `"type": "once"` for debugging before switching to `toggle`

---

## Time Units

**Important:** All pauses are specified in **milliseconds** (ms).

- 1 second = 1000 ms
- 5 seconds = 5000 ms
- 15 seconds = 15000 ms
- 1 minute = 60000 ms
- 4 minutes = 240000 ms
- 5 minutes = 300000 ms

### Time Calculator

```
seconds → milliseconds: multiply by 1000
minutes → milliseconds: multiply by 60000

Examples:
0.1 секунды = 100 мс
0.25 секунды = 250 мс
0.5 секунды = 500 мс
1 секунда = 1000 мс
2 секунды = 2000 мс
10 секунд = 10000 мс
30 секунд = 30000 мс
1 минута = 60000 мс
2 минуты = 120000 мс
5 минут = 300000 мс
```
