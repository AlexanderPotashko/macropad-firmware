"""
MacroState v2 - Enhanced state management for macros.

This module implements the new hybrid priority system with:
- Two-tier timer system (action_wait_until, cycle_wait_until)
- Five distinct states (OFF, ACTIVE, WAIT, SLEEPING, IN_QUEUE)
- Support for Press, Hold, and Toggle macro types
"""

import time


class MacroState:
    """
    Manages the execution state of a single macro.
    
    States:
    - OFF: is_active = False
    - ACTIVE: is_active = True, action_wait_until = None (executing action)
    - WAIT: is_active = True, action_wait_until != None (waiting between actions)
    - SLEEPING: is_active = True, cycle_wait_until != None (Toggle waiting between cycles)
    - IN_QUEUE: is_active = True, key_id in execution_queue
    """
    
    def __init__(self, key_id, config):
        """
        Initialize macro state.
        
        Args:
            key_id (int): Physical key ID (0-11)
            config (dict): Macro configuration from JSON
        """
        self.key_id = key_id
        self.config = config
        self.type = config['type']  # "press", "hold", "toggle"
        self.name = config.get('name', f'Macro {key_id}')
        self.actions = config['actions']
        self.wait_time = config.get('wait', 0)  # Only for toggle (ms between cycles)
        
        # Execution state
        self.is_active = False  # Is the macro enabled?
        self.current_action_index = 0  # Current action being executed
        
        # Two-tier timer system
        self.action_wait_until = None  # Timer for waits between actions
        self.cycle_wait_until = None   # Timer for waits between cycles (toggle only)
        
        # For hold type macros
        self.is_key_held = False  # Is the physical key still held down?
        
        # For nested repeat handling
        self.repeat_stack = []  # [(start_index, end_index, current_count, max_count), ...]
        
    def start(self):
        """
        Start or restart the macro.
        Resets all state to beginning.
        """
        self.is_active = True
        self.current_action_index = 0
        self.action_wait_until = None
        self.cycle_wait_until = None
        self.repeat_stack = []
        
        if self.type == "hold":
            self.is_key_held = True
        
        print(f"[MacroState] Started macro {self.key_id} ({self.name}, type={self.type})")
    
    def stop(self):
        """
        Stop the macro completely.
        Clears all timers and resets state.
        """
        was_active = self.is_active
        
        self.is_active = False
        self.current_action_index = 0
        self.action_wait_until = None
        self.cycle_wait_until = None
        self.is_key_held = False
        self.repeat_stack = []
        
        if was_active:
            print(f"[MacroState] Stopped macro {self.key_id} ({self.name})")
    
    def get_current_action(self):
        """
        Get the current action to execute.
        
        Returns:
            dict: Current action, or None if no more actions
        """
        if not self.is_active:
            return None
        
        # Check if we're in a repeat block
        if self.repeat_stack:
            context = self.repeat_stack[-1]
            repeat_actions = context['actions']
            repeat_index = context['current_index']
            
            if repeat_index < len(repeat_actions):
                return repeat_actions[repeat_index]
            else:
                # Finished one iteration of repeat
                context['current_count'] += 1
                if context['current_count'] < context['max_count']:
                    # Continue with next iteration
                    context['current_index'] = 0
                    return repeat_actions[0]
                else:
                    # Repeat block finished
                    self.repeat_stack.pop()
                    self.current_action_index += 1
                    return self.get_current_action()
        
        # Normal action execution
        if self.current_action_index < len(self.actions):
            return self.actions[self.current_action_index]
        
        # All actions completed
        return None
    
    def advance_action(self):
        """
        Move to the next action.
        Handles repeat blocks and normal progression.
        """
        if self.repeat_stack:
            # Inside a repeat block
            context = self.repeat_stack[-1]
            context['current_index'] += 1
        else:
            # Normal progression
            self.current_action_index += 1
    
    def enter_repeat(self, actions, count):
        """
        Enter a repeat block.
        
        Args:
            actions (list): Actions to repeat
            count (int): Number of iterations
        """
        self.repeat_stack.append({
            'actions': actions,
            'current_index': 0,
            'current_count': 0,
            'max_count': count
        })
        print(f"[MacroState] Entering repeat block: {count} iterations")
    
    def is_waiting_between_actions(self):
        """Check if macro is waiting between actions (WAIT state)."""
        return self.is_active and self.action_wait_until is not None
    
    def is_sleeping(self):
        """Check if macro is sleeping between cycles (SLEEPING state)."""
        return self.is_active and self.cycle_wait_until is not None
    
    def is_ready_to_execute(self):
        """Check if macro is ready to execute an action (ACTIVE state)."""
        return (self.is_active and 
                self.action_wait_until is None and 
                self.cycle_wait_until is None)
    
    def get_state_name(self):
        """
        Get human-readable state name.
        
        Returns:
            str: One of "OFF", "ACTIVE", "WAIT", "SLEEPING", "IN_QUEUE"
        """
        if not self.is_active:
            return "OFF"
        
        if self.cycle_wait_until is not None:
            return "SLEEPING"
        
        if self.action_wait_until is not None:
            return "WAIT"
        
        # Note: IN_QUEUE state is determined externally by checking if key_id in QUEUE
        return "ACTIVE"
    
    def set_action_wait(self, wait_ms):
        """
        Set timer for waiting between actions.
        
        Args:
            wait_ms (int): Wait time in milliseconds
        """
        if wait_ms > 0:
            self.action_wait_until = time.monotonic() + (wait_ms / 1000.0)
        else:
            self.action_wait_until = None
    
    def set_cycle_wait(self):
        """
        Set timer for waiting between cycles (toggle only).
        Uses the macro's configured wait time.
        """
        if self.wait_time > 0:
            self.cycle_wait_until = time.monotonic() + (self.wait_time / 1000.0)
            print(f"[MacroState] Macro {self.key_id} → SLEEPING for {self.wait_time}ms")
        else:
            self.cycle_wait_until = None
    
    def check_and_clear_action_timer(self):
        """
        Check if action wait timer has expired.
        
        Returns:
            bool: True if timer expired (and was cleared), False otherwise
        """
        if self.action_wait_until is not None:
            if time.monotonic() >= self.action_wait_until:
                self.action_wait_until = None
                return True
        return False
    
    def check_and_clear_cycle_timer(self):
        """
        Check if cycle wait timer has expired.
        
        Returns:
            bool: True if timer expired (and was cleared), False otherwise
        """
        if self.cycle_wait_until is not None:
            if time.monotonic() >= self.cycle_wait_until:
                self.cycle_wait_until = None
                print(f"[MacroState] Macro {self.key_id} woke from SLEEPING")
                return True
        return False
    
    def interrupt_to_sleeping(self):
        """
        Interrupt a toggle macro and put it to SLEEPING state.
        ✅ CRITICAL: Resets current_action_index to 0 (will restart from beginning)
        """
        if self.type != "toggle":
            print(f"[MacroState] WARNING: interrupt_to_sleeping called on non-toggle macro {self.key_id}")
            return
        
        # Set cycle timer
        self.set_cycle_wait()
        
        # ✅ CRITICAL: Reset to beginning
        self.current_action_index = 0
        self.action_wait_until = None
        self.repeat_stack = []
        
        print(f"[MacroState] Macro {self.key_id} interrupted → SLEEPING (will restart from beginning)")
    
    def __repr__(self):
        """String representation for debugging."""
        state = self.get_state_name()
        return f"MacroState(id={self.key_id}, type={self.type}, state={state}, action={self.current_action_index}/{len(self.actions)})"
