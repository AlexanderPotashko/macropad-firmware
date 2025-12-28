# JSON macro file parser and validator
import json
from key_mapping import KEY_NAMES, MODIFIERS


def load_macros(filename='macros.json'):
    """
    Load and parse macros from JSON file.
    
    Returns:
        dict: Dictionary of macro configurations keyed by logical key number (0-11)
        None: If file not found or invalid JSON
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        if 'macros' not in data:
            print(f"ERROR: 'macros' key not found in {filename}")
            return None
        
        macros = {}
        for key_str, macro_config in data['macros'].items():
            try:
                key_id = int(key_str)
                if 0 <= key_id <= 11:
                    if validate_macro(macro_config, key_id):
                        macros[key_id] = macro_config
                    else:
                        print(f"WARNING: Invalid macro config for key {key_id}, skipping")
                else:
                    print(f"WARNING: Key {key_id} out of range (0-11), skipping")
            except ValueError:
                print(f"WARNING: Invalid key '{key_str}', must be number 0-11")
        
        print(f"Loaded {len(macros)} macro(s)")
        return macros
    
    except OSError as e:
        print(f"ERROR: Could not read {filename}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {filename}: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error loading macros: {e}")
        return None


def validate_macro(config, key_id):
    """
    Validate macro configuration structure.
    
    Args:
        config (dict): Macro configuration
        key_id (int): Key number for error messages
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(config, dict):
        print(f"Key {key_id}: Config must be a dictionary")
        return False
    
    # Check required fields
    if 'actions' not in config:
        print(f"Key {key_id}: Missing 'actions' field")
        return False
    
    if not isinstance(config['actions'], list):
        print(f"Key {key_id}: 'actions' must be a list")
        return False
    
    if len(config['actions']) == 0:
        print(f"Key {key_id}: 'actions' list is empty")
        return False
    
    # Validate type field
    macro_type = config.get('type', 'once')
    if macro_type not in ['once', 'hold', 'toggle']:
        print(f"Key {key_id}: Invalid type '{macro_type}', must be once/hold/toggle")
        return False
    
    # Validate loop field
    loop = config.get('loop', False)
    if not isinstance(loop, bool):
        print(f"Key {key_id}: 'loop' must be true or false")
        return False
    
    # Validate each action
    for i, action in enumerate(config['actions']):
        if not validate_action(action, key_id, i):
            return False
    
    return True


def validate_action(action, key_id, action_index):
    """
    Validate a single action.
    
    Args:
        action (dict): Action configuration
        key_id (int): Key number for error messages
        action_index (int): Action index for error messages
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(action, dict):
        print(f"Key {key_id}, action {action_index}: Must be a dictionary")
        return False
    
    if 'type' not in action:
        print(f"Key {key_id}, action {action_index}: Missing 'type' field")
        return False
    
    action_type = action['type']
    
    # Validate based on action type
    if action_type == 'press':
        if 'keys' not in action:
            print(f"Key {key_id}, action {action_index}: 'press' requires 'keys' field")
            return False
        # Validate optional inline wait
        if 'wait' in action:
            if not isinstance(action['wait'], (int, float)) or action['wait'] < 0:
                print(f"Key {key_id}, action {action_index}: 'wait' must be positive number")
                return False
        # Validate optional inline wait_random
        if 'wait_random' in action:
            wr = action['wait_random']
            if not isinstance(wr, dict) or 'min' not in wr or 'max' not in wr:
                print(f"Key {key_id}, action {action_index}: 'wait_random' must be dict with 'min' and 'max'")
                return False
            if wr['min'] > wr['max']:
                print(f"Key {key_id}, action {action_index}: 'wait_random' min cannot be greater than max")
                return False
    
    elif action_type == 'press_down':
        if 'keys' not in action:
            print(f"Key {key_id}, action {action_index}: 'press_down' requires 'keys' field")
            return False
        # Validate optional inline wait
        if 'wait' in action:
            if not isinstance(action['wait'], (int, float)) or action['wait'] < 0:
                print(f"Key {key_id}, action {action_index}: 'wait' must be positive number")
                return False
        # Validate optional inline wait_random
        if 'wait_random' in action:
            wr = action['wait_random']
            if not isinstance(wr, dict) or 'min' not in wr or 'max' not in wr:
                print(f"Key {key_id}, action {action_index}: 'wait_random' must be dict with 'min' and 'max'")
                return False
            if wr['min'] > wr['max']:
                print(f"Key {key_id}, action {action_index}: 'wait_random' min cannot be greater than max")
                return False
    
    elif action_type == 'press_up':
        if 'keys' not in action:
            print(f"Key {key_id}, action {action_index}: 'press_up' requires 'keys' field")
            return False
        # Validate optional inline wait
        if 'wait' in action:
            if not isinstance(action['wait'], (int, float)) or action['wait'] < 0:
                print(f"Key {key_id}, action {action_index}: 'wait' must be positive number")
                return False
        # Validate optional inline wait_random
        if 'wait_random' in action:
            wr = action['wait_random']
            if not isinstance(wr, dict) or 'min' not in wr or 'max' not in wr:
                print(f"Key {key_id}, action {action_index}: 'wait_random' must be dict with 'min' and 'max'")
                return False
            if wr['min'] > wr['max']:
                print(f"Key {key_id}, action {action_index}: 'wait_random' min cannot be greater than max")
                return False
    
    elif action_type == 'type':
        if 'text' not in action:
            print(f"Key {key_id}, action {action_index}: 'type' requires 'text' field")
            return False
        # Validate optional inline wait
        if 'wait' in action:
            if not isinstance(action['wait'], (int, float)) or action['wait'] < 0:
                print(f"Key {key_id}, action {action_index}: 'wait' must be positive number")
                return False
        # Validate optional inline wait_random
        if 'wait_random' in action:
            wr = action['wait_random']
            if not isinstance(wr, dict) or 'min' not in wr or 'max' not in wr:
                print(f"Key {key_id}, action {action_index}: 'wait_random' must be dict with 'min' and 'max'")
                return False
            if wr['min'] > wr['max']:
                print(f"Key {key_id}, action {action_index}: 'wait_random' min cannot be greater than max")
                return False
    
    elif action_type == 'wait':
        if 'ms' not in action:
            print(f"Key {key_id}, action {action_index}: 'wait' requires 'ms' field")
            return False
        if not isinstance(action['ms'], (int, float)) or action['ms'] < 0:
            print(f"Key {key_id}, action {action_index}: 'ms' must be positive number")
            return False
    
    elif action_type == 'wait_random':
        if 'min' not in action or 'max' not in action:
            print(f"Key {key_id}, action {action_index}: 'wait_random' requires 'min' and 'max'")
            return False
        if action['min'] > action['max']:
            print(f"Key {key_id}, action {action_index}: 'min' cannot be greater than 'max'")
            return False
    
    elif action_type == 'mouse_click':
        button = action.get('button', 'left')
        if button not in ['left', 'right', 'middle']:
            print(f"Key {key_id}, action {action_index}: Invalid mouse button '{button}'")
            return False
        # Validate optional inline wait
        if 'wait' in action:
            if not isinstance(action['wait'], (int, float)) or action['wait'] < 0:
                print(f"Key {key_id}, action {action_index}: 'wait' must be positive number")
                return False
        # Validate optional inline wait_random
        if 'wait_random' in action:
            wr = action['wait_random']
            if not isinstance(wr, dict) or 'min' not in wr or 'max' not in wr:
                print(f"Key {key_id}, action {action_index}: 'wait_random' must be dict with 'min' and 'max'")
                return False
            if wr['min'] > wr['max']:
                print(f"Key {key_id}, action {action_index}: 'wait_random' min cannot be greater than max")
                return False
    
    elif action_type == 'mouse_move':
        if 'x' not in action or 'y' not in action:
            print(f"Key {key_id}, action {action_index}: 'mouse_move' requires 'x' and 'y'")
            return False
        # Validate optional inline wait
        if 'wait' in action:
            if not isinstance(action['wait'], (int, float)) or action['wait'] < 0:
                print(f"Key {key_id}, action {action_index}: 'wait' must be positive number")
                return False
        # Validate optional inline wait_random
        if 'wait_random' in action:
            wr = action['wait_random']
            if not isinstance(wr, dict) or 'min' not in wr or 'max' not in wr:
                print(f"Key {key_id}, action {action_index}: 'wait_random' must be dict with 'min' and 'max'")
                return False
            if wr['min'] > wr['max']:
                print(f"Key {key_id}, action {action_index}: 'wait_random' min cannot be greater than max")
                return False
    
    elif action_type == 'mouse_scroll':
        if 'amount' not in action:
            print(f"Key {key_id}, action {action_index}: 'mouse_scroll' requires 'amount'")
            return False
        # Validate optional inline wait
        if 'wait' in action:
            if not isinstance(action['wait'], (int, float)) or action['wait'] < 0:
                print(f"Key {key_id}, action {action_index}: 'wait' must be positive number")
                return False
        # Validate optional inline wait_random
        if 'wait_random' in action:
            wr = action['wait_random']
            if not isinstance(wr, dict) or 'min' not in wr or 'max' not in wr:
                print(f"Key {key_id}, action {action_index}: 'wait_random' must be dict with 'min' and 'max'")
                return False
            if wr['min'] > wr['max']:
                print(f"Key {key_id}, action {action_index}: 'wait_random' min cannot be greater than max")
                return False
    
    elif action_type == 'repeat':
        if 'count' not in action or 'actions' not in action:
            print(f"Key {key_id}, action {action_index}: 'repeat' requires 'count' and 'actions'")
            return False
        if not isinstance(action['actions'], list):
            print(f"Key {key_id}, action {action_index}: 'repeat' actions must be a list")
            return False
        # Recursively validate nested actions
        for i, nested_action in enumerate(action['actions']):
            if not validate_action(nested_action, key_id, f"{action_index}.{i}"):
                return False
    
    else:
        print(f"Key {key_id}, action {action_index}: Unknown action type '{action_type}'")
        return False
    
    return True


def parse_keys(keys_string):
    """
    Parse key combination string into list of Keycode objects.
    
    Examples:
        "Ctrl+C" -> [Keycode.CONTROL, Keycode.C]
        "Shift+Alt+F1" -> [Keycode.SHIFT, Keycode.ALT, Keycode.F1]
        "A" -> [Keycode.A]
    
    Args:
        keys_string (str): Key combination string
    
    Returns:
        list: List of Keycode objects, or None if invalid
    """
    if not keys_string:
        return None
    
    # Split by + and normalize
    parts = [p.strip().upper() for p in keys_string.split('+')]
    
    keycodes = []
    for part in parts:
        if part in KEY_NAMES:
            keycodes.append(KEY_NAMES[part])
        else:
            print(f"WARNING: Unknown key '{part}' in '{keys_string}'")
            return None
    
    return keycodes if keycodes else None
