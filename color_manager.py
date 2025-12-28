"""
Color Manager v2 - Adapted for new macro states.

New states:
- OFF: Macro disabled (black or dim)
- ACTIVE: Executing action (bright blue)
- WAIT: Waiting between actions (yellow)
- SLEEPING: Toggle waiting between cycles (green)
- IN_QUEUE: Waiting in queue (purple)
- READY: Ready to execute (dim green)
"""

import json


class ColorManager:
    """
    Manages LED colors for MacroPad buttons based on macro states.
    
    State colors (from REMASTER_PLAN.md):
    - SLEEPING: Green (0, 255, 0) - Toggle waiting between cycles
    - ACTIVE: Blue (0, 80, 255) - Executing action
    - WAIT: Yellow (255, 200, 0) - Waiting between actions
    - IN_QUEUE: Purple (200, 0, 200) - In execution queue
    - READY: Dim green (0, 40, 0) - Ready to start
    - OFF: Black (0, 0, 0) - Macro disabled
    - ERROR: Red (255, 0, 0) - Error state
    """
    
    # Default colors from plan
    DEFAULT_COLORS = {
        'sleeping': (0, 255, 0),      # 🟢 Toggle waiting (bright green)
        'active': (0, 80, 255),        # 🔵 Executing (bright blue)
        'wait': (255, 200, 0),         # 🟡 Waiting between actions (yellow)
        'in_queue': (200, 0, 200),     # 🟣 In queue (purple)
        'ready': (0, 40, 0),           # 🟢 Ready to start (dim green)
        'off': (0, 0, 0),              # ⚫ Disabled (black)
        'error': (255, 0, 0),          # 🔴 Error (red)
        'emergency': (255, 0, 0)       # 🔴 Emergency blink (red)
    }
    
    def __init__(self, colors_file='data/button_colors.json'):
        """
        Initialize the color manager.
        
        Args:
            colors_file (str): Path to global colors configuration (optional)
        """
        self.colors_file = colors_file
        self.custom_colors = {}
        self.load_custom_colors()
    
    def load_custom_colors(self):
        """Load custom color configuration from JSON file (optional)."""
        try:
            with open(self.colors_file, 'r') as f:
                data = json.load(f)
            
            # Look for 'remaster' section
            if 'remaster' in data:
                color_data = data['remaster']
            elif 'default' in data:
                color_data = data['default']
            else:
                print(f"[ColorManager] No custom colors found in {self.colors_file}")
                return
            
            # Validate and load colors
            for state, color in color_data.items():
                if self._validate_color(color):
                    self.custom_colors[state] = tuple(color) if isinstance(color, list) else color
                else:
                    print(f"[ColorManager] WARNING: Invalid color for state '{state}': {color}")
            
            print(f"[ColorManager] Loaded {len(self.custom_colors)} custom color(s)")
        
        except OSError:
            # File not found - use defaults
            pass
        except json.JSONDecodeError as e:
            print(f"[ColorManager] WARNING: Invalid JSON in {self.colors_file}: {e}")
        except Exception as e:
            print(f"[ColorManager] WARNING: Error loading colors: {e}")
    
    def get_color_for_macro(self, macro_state, is_in_queue=False):
        """
        Get color for a macro based on its state.
        
        Args:
            macro_state (MacroState): The macro state object
            is_in_queue (bool): Whether macro is in execution queue
        
        Returns:
            tuple: RGB color (R, G, B) where values are 0-255
        """
        if not macro_state:
            return self.get_color('off')
        
        # Determine state
        if not macro_state.is_active:
            # OFF state
            return self.get_color('ready')  # Show as ready when configured but not active
        
        if is_in_queue:
            # IN_QUEUE state
            return self.get_color('in_queue')
        
        if macro_state.is_sleeping():
            # SLEEPING state (Toggle waiting between cycles)
            return self.get_color('sleeping')
        
        if macro_state.is_waiting_between_actions():
            # WAIT state (waiting between actions)
            return self.get_color('wait')
        
        if macro_state.is_ready_to_execute():
            # ACTIVE state (executing action)
            return self.get_color('active')
        
        # Default fallback
        return self.get_color('off')
    
    def get_color(self, state_name):
        """
        Get color for a specific state.
        
        Priority:
        1. Custom colors from JSON
        2. Default colors from plan
        
        Args:
            state_name (str): State name ('sleeping', 'active', 'wait', etc.)
        
        Returns:
            tuple: RGB color (R, G, B)
        """
        # Try custom colors first
        if state_name in self.custom_colors:
            return self.custom_colors[state_name]
        
        # Fall back to defaults
        if state_name in self.DEFAULT_COLORS:
            return self.DEFAULT_COLORS[state_name]
        
        # Unknown state - return off
        print(f"[ColorManager] WARNING: Unknown state '{state_name}'")
        return self.DEFAULT_COLORS['off']
    
    def get_emergency_color(self):
        """Get color for emergency blink (red)."""
        return self.get_color('emergency')
    
    def _validate_color(self, color):
        """
        Validate that a color is a valid RGB tuple/list.
        
        Args:
            color: Color to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(color, (tuple, list)):
            return False
        
        if len(color) != 3:
            return False
        
        for value in color:
            if not isinstance(value, int):
                return False
            if value < 0 or value > 255:
                return False
        
        return True
    
    def get_all_default_colors(self):
        """
        Get all default colors for reference.
        
        Returns:
            dict: All default colors
        """
        return self.DEFAULT_COLORS.copy()
