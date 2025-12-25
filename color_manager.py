# Color management system for button LEDs
import json


class ColorManager:
    """Manages LED colors for MacroPad buttons based on macro states."""
    
    # Hardcoded fallback colors (if JSON files fail)
    FALLBACK_COLORS = {
        'ready': (0, 80, 0),
        'active': (60, 30, 0),
        'loop': (0, 0, 80),
        'wait': (80, 80, 0),
        'queued': (60, 0, 60),
        'executing': (0, 60, 60),
        'repeat_active': (80, 0, 80),
        'no_macro': (0, 0, 0),
        'error': (255, 0, 0)
    }
    
    def __init__(self, colors_file='data/button_colors.json'):
        """
        Initialize the color manager.
        
        Args:
            colors_file (str): Path to global colors configuration
        """
        self.colors_file = colors_file
        self.global_colors = {}
        self.load_global_colors()
    
    def load_global_colors(self):
        """Load global color configuration from JSON file."""
        try:
            with open(self.colors_file, 'r') as f:
                data = json.load(f)
            
            if 'default' in data:
                # Convert lists to tuples
                for state, color in data['default'].items():
                    if self._validate_color(color):
                        self.global_colors[state] = tuple(color)
                    else:
                        print(f"WARNING: Invalid color for state '{state}': {color}")
                
                print(f"Loaded {len(self.global_colors)} global color(s)")
            else:
                print(f"WARNING: 'default' key not found in {self.colors_file}")
        
        except OSError as e:
            print(f"WARNING: Could not read {self.colors_file}: {e}")
        except json.JSONDecodeError as e:
            print(f"WARNING: Invalid JSON in {self.colors_file}: {e}")
        except Exception as e:
            print(f"WARNING: Error loading colors: {e}")
    
    def get_color(self, state, macro_colors=None):
        """
        Get color for a specific state with priority system.
        
        Priority:
        1. Macro-specific colors (if provided)
        2. Global colors from JSON
        3. Hardcoded fallback
        
        Args:
            state (str): State name ('ready', 'active', 'loop', etc.)
            macro_colors (dict): Optional macro-specific color overrides
        
        Returns:
            tuple: RGB color tuple (R, G, B) where values are 0-255
        """
        # Priority 1: Macro-specific colors
        if macro_colors and state in macro_colors:
            color = macro_colors[state]
            if self._validate_color(color):
                return tuple(color) if isinstance(color, list) else color
            else:
                print(f"WARNING: Invalid macro color for state '{state}': {color}")
        
        # Priority 2: Global colors from JSON
        if state in self.global_colors:
            return self.global_colors[state]
        
        # Priority 3: Hardcoded fallback
        if state in self.FALLBACK_COLORS:
            return self.FALLBACK_COLORS[state]
        
        # Unknown state - return dim white
        print(f"WARNING: Unknown LED state '{state}', using dim white")
        return (10, 10, 10)
    
    def get_button_color(self, macro_state, macro_executor):
        """
        Determine the appropriate color for a button based on macro state.
        
        States:
        - SLEEP (active): is_active=True, is_executing=False, not in queue → Orange
        - IN_QUEUE (queued): is_active=True, in execution_queue → Purple
        - ACTIVE (loop): is_executing=True, wait_until=None → Blue
        - WAIT (wait): is_executing=True, wait_until set → Yellow
        - OFF (no_macro): is_active=False → Dim
        
        Args:
            macro_state: MacroState object
            macro_executor: MacroExecutor instance (for checking queue)
        
        Returns:
            tuple: RGB color tuple (R, G, B)
        """
        # Get macro-specific colors if defined
        macro_colors = macro_state.config.get('colors', {})
        key_id = macro_state.key_id
        
        # Check if macro is active (toggle on)
        if not macro_state.is_active:
            # Macro is OFF (toggle off) - show green to indicate available button
            return self.get_color('ready', macro_colors)
        
        # Macro is active - determine state
        
        # Check if in queue (woke up but waiting for slot)
        if key_id in macro_executor.execution_queue:
            # IN_QUEUE state
            return self.get_color('queued', macro_colors)
        
        # Check if executing inside repeat block
        if macro_state.repeat_stack:
            # Inside repeat - special color
            return self.get_color('repeat_active', macro_colors)
        
        # Check if executing (owns execution slot)
        if macro_state.is_executing:
            # ACTIVE or WAIT state
            if macro_state.wait_until:
                # Waiting between actions - WAIT state
                return self.get_color('wait', macro_colors)
            else:
                # Executing actions - ACTIVE state
                return self.get_color('loop', macro_colors)
        else:
            # SLEEP state (waiting for timer, not in queue) - show as active
            return self.get_color('active', macro_colors)
    
    @staticmethod
    def _validate_color(color):
        """
        Validate that a color is in correct format.
        
        Args:
            color: Color to validate (should be list or tuple of 3 ints)
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(color, (list, tuple)):
            return False
        
        if len(color) != 3:
            return False
        
        for value in color:
            if not isinstance(value, int):
                return False
            if value < 0 or value > 255:
                return False
        
        return True
    
    @staticmethod
    def validate_macro_colors(colors_dict):
        """
        Validate colors dictionary from macro configuration.
        
        Args:
            colors_dict (dict): Dictionary of state: color pairs
        
        Returns:
            bool: True if all colors are valid
        """
        if not isinstance(colors_dict, dict):
            return False
        
        for state, color in colors_dict.items():
            if not ColorManager._validate_color(color):
                print(f"Invalid color for state '{state}': {color}")
                return False
        
        return True
