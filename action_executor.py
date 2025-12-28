"""
Action Executor - Executes individual macro actions.

This module handles:
- Keyboard key presses
- Mouse clicks and movements
- Wait delays (including random waits)
- Text typing
- Repeat blocks (nested support)
"""

import time
import random


class ActionExecutor:
    """
    Executes individual actions from a macro.
    
    Supports all action types:
    - press: Press and release keys
    - click: Mouse clicks
    - move: Mouse movement
    - scroll: Mouse scroll
    - wait: Fixed delay
    - wait_random: Random delay
    - type: Type text
    - repeat: Execute actions multiple times
    """
    
    def __init__(self, keyboard, mouse, consumer_control, parse_keys_func):
        """
        Initialize the action executor.
        
        Args:
            keyboard: Keyboard HID device
            mouse: Mouse HID device  
            consumer_control: Consumer control HID device
            parse_keys_func: Function to parse key strings
        """
        self.keyboard = keyboard
        self.mouse = mouse
        self.consumer_control = consumer_control
        self.parse_keys = parse_keys_func
        
    def execute(self, action, macro_state):
        """
        Execute a single action.
        
        Args:
            action (dict): Action configuration
            macro_state (MacroState): The macro state (for repeat blocks)
            
        Returns:
            int: Wait time in milliseconds (0 if no wait)
        """
        action_type = action.get('type')
        wait_ms = action.get('wait', 0)
        
        print(f"[ActionExecutor] Executing action: {action_type}")
        
        if action_type == 'press':
            self._execute_press(action)
        
        elif action_type == 'click':
            self._execute_click(action)
        
        elif action_type == 'move':
            self._execute_move(action)
        
        elif action_type == 'scroll':
            self._execute_scroll(action)
        
        elif action_type == 'wait':
            wait_ms = action.get('ms', 0)
        
        elif action_type == 'wait_random':
            min_ms = action.get('min', 0)
            max_ms = action.get('max', 1000)
            wait_ms = random.randint(min_ms, max_ms)
            print(f"[ActionExecutor] Random wait: {wait_ms}ms")
        
        elif action_type == 'type':
            self._execute_type(action)
        
        elif action_type == 'repeat':
            # Handle repeat block
            actions = action.get('actions', [])
            count = action.get('count', 1)
            macro_state.enter_repeat(actions, count)
            print(f"[ActionExecutor] Entered repeat block: {count} iterations")
            return 0  # No wait after entering repeat
        
        else:
            print(f"[ActionExecutor] WARNING: Unknown action type: {action_type}")
        
        return wait_ms
    
    def _execute_press(self, action):
        """
        Execute a key press action.
        
        Args:
            action (dict): Action with 'keys' field
        """
        keys_str = action.get('keys', '')
        if not keys_str:
            print(f"[ActionExecutor] WARNING: press action with no keys")
            return
        
        # Parse keys using the macro_parser function
        keycodes = self.parse_keys(keys_str)
        
        if not keycodes:
            print(f"[ActionExecutor] WARNING: Could not parse keys: {keys_str}")
            return
        
        # Press all keys
        for keycode in keycodes:
            self.keyboard.press(keycode)
        
        # Small delay for key registration
        time.sleep(0.01)
        
        # Release all keys
        self.keyboard.release_all()
        
        print(f"[ActionExecutor] Pressed keys: {keys_str}")
    
    def _execute_click(self, action):
        """
        Execute a mouse click action.
        
        Args:
            action (dict): Action with 'button' field (1=left, 2=right, 3=middle)
        """
        button = action.get('button', 1)  # Default: left click
        
        if button == 1:
            self.mouse.click(self.mouse.LEFT_BUTTON)
        elif button == 2:
            self.mouse.click(self.mouse.RIGHT_BUTTON)
        elif button == 3:
            self.mouse.click(self.mouse.MIDDLE_BUTTON)
        else:
            print(f"[ActionExecutor] WARNING: Unknown mouse button: {button}")
            return
        
        print(f"[ActionExecutor] Mouse click: button {button}")
    
    def _execute_move(self, action):
        """
        Execute a mouse move action.
        
        Args:
            action (dict): Action with 'x' and 'y' fields
        """
        x = action.get('x', 0)
        y = action.get('y', 0)
        
        self.mouse.move(x, y)
        
        print(f"[ActionExecutor] Mouse move: ({x}, {y})")
    
    def _execute_scroll(self, action):
        """
        Execute a mouse scroll action.
        
        Args:
            action (dict): Action with 'amount' field
        """
        amount = action.get('amount', 0)
        
        self.mouse.move(0, 0, amount)
        
        print(f"[ActionExecutor] Mouse scroll: {amount}")
    
    def _execute_type(self, action):
        """
        Execute a text typing action.
        
        Args:
            action (dict): Action with 'text' field
        """
        text = action.get('text', '')
        if not text:
            print(f"[ActionExecutor] WARNING: type action with no text")
            return
        
        # Type each character with small delay
        for char in text:
            self.keyboard.send(char)
            time.sleep(0.05)  # 50ms between characters
        
        print(f"[ActionExecutor] Typed text: {text[:20]}{'...' if len(text) > 20 else ''}")
    
    def release_all(self):
        """Release all pressed keys and buttons (emergency cleanup)."""
        try:
            self.keyboard.release_all()
            print(f"[ActionExecutor] Released all keys")
        except Exception as e:
            print(f"[ActionExecutor] ERROR releasing keys: {e}")
