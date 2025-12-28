"""
Macro Engine v2 - Core execution engine with hybrid priority system.

This module implements:
- Hybrid priority system (Press/Hold priority, Toggle queued)
- SLOT + QUEUE execution model
- Two-tier timer system (action_wait, cycle_wait)
- Stability checks (is_active validation, overflow protection, etc.)
"""

import time
from macro_state import MacroState
from queue_manager import QueueManager
from action_executor import ActionExecutor


class MacroEngine:
    """
    Enhanced macro execution engine with queue-based execution.
    
    Key features:
    - Press/Hold macros: Priority execution (interrupt everything)
    - Toggle macros: Queue-based execution (wait for slot)
    - SLOT + QUEUE system: One executor, FIFO waiting list
    - Overflow protection: Max 1000 items in queue
    - Stability checks: Validate state consistency
    """
    
    def __init__(self, keyboard, mouse, consumer_control, parse_keys_func):
        """
        Initialize the macro engine.
        
        Args:
            keyboard: Keyboard HID device
            mouse: Mouse HID device
            consumer_control: Consumer control HID device
            parse_keys_func: Function to parse key strings
        """
        # Hardware interfaces
        self.keyboard = keyboard
        self.mouse = mouse
        self.consumer_control = consumer_control
        
        # Action executor
        self.action_executor = ActionExecutor(keyboard, mouse, consumer_control, parse_keys_func)
        
        # Queue system
        self.queue_manager = QueueManager()
        
        # Macro states (key_id -> MacroState)
        self.macro_states = {}
        
        # Hold key tracking (key_id -> bool)
        self.key_held = {}
        
        # Emergency blink state
        self.emergency_blink_until = None
        self.emergency_blink_message = ""
        
    def load_profile(self, profile_config):
        """
        Load a new profile and initialize macro states.
        
        Args:
            profile_config (dict): Profile configuration with 'macros' key
        """
        print(f"[MacroEngine] Loading profile...")
        
        # Stop all current macros
        self.emergency_stop_all()
        
        # Clear old states
        self.macro_states.clear()
        self.key_held.clear()
        
        # Create new macro states
        macros = profile_config.get('macros', {})
        for key_id_str, macro_config in macros.items():
            key_id = int(key_id_str)
            self.macro_states[key_id] = MacroState(key_id, macro_config)
            self.key_held[key_id] = False
        
        print(f"[MacroEngine] Loaded {len(self.macro_states)} macros")
    
    # ============================================================
    # CORE EXECUTION FUNCTIONS
    # ============================================================
    
    def execute_active_macro(self):
        """
        Execute the macro currently in SLOT (if any).
        Called every loop iteration.
        """
        slot = self.queue_manager.get_slot()
        if slot is None:
            return
        
        state = self.macro_states.get(slot)
        if not state:
            print(f"[MacroEngine] ERROR: Invalid slot {slot}")
            self.queue_manager.free_slot()
            return
        
        # Check if macro is still active
        if not state.is_active:
            print(f"[MacroEngine] Macro {slot} is no longer active, freeing slot")
            self.queue_manager.free_slot()
            self.process_queue()
            return
        
        # Check action timer (WAIT state)
        if state.check_and_clear_action_timer():
            # Timer expired, continue execution
            pass
        
        # If still waiting, don't execute
        if state.is_waiting_between_actions():
            return
        
        # Get current action
        action = state.get_current_action()
        
        if action is None:
            # All actions completed
            self._handle_macro_completion(state)
            return
        
        # Execute the action
        wait_ms = self.action_executor.execute(action, state)
        
        # Advance to next action
        state.advance_action()
        
        # Set wait timer if needed
        if wait_ms > 0:
            state.set_action_wait(wait_ms)
    
    def _handle_macro_completion(self, state):
        """
        Handle macro completion (all actions executed).
        
        Args:
            state (MacroState): The completed macro state
        """
        if state.type == "toggle":
            # Toggle: Go to SLEEPING state
            print(f"[MacroEngine] Toggle macro {state.key_id} cycle complete → SLEEPING")
            state.set_cycle_wait()
            self.queue_manager.free_slot()
            self.process_queue()  # Start next macro from queue
        
        elif state.type == "hold":
            # Hold: Check if key is still held
            if state.is_key_held and self.key_held.get(state.key_id, False):
                # Key still held, restart from beginning
                print(f"[MacroEngine] Hold macro {state.key_id} restarting (key still held)")
                state.current_action_index = 0
                state.action_wait_until = None
            else:
                # Key released, stop
                print(f"[MacroEngine] Hold macro {state.key_id} complete → OFF")
                state.stop()
                self.queue_manager.free_slot()
                self.process_queue()
        
        else:  # press
            # Press: Complete and stop
            print(f"[MacroEngine] Press macro {state.key_id} complete → OFF")
            state.stop()
            self.queue_manager.free_slot()
            self.process_queue()
    
    def process_queue(self):
        """
        Process the queue - start next macro if slot is free.
        
        ✅ CRITICAL: Validates is_active before starting!
        """
        if not self.queue_manager.is_slot_free():
            return
        
        if self.queue_manager.get_queue_size() == 0:
            return
        
        # Pop next from queue
        next_key_id = self.queue_manager.pop_next_from_queue()
        if next_key_id is None:
            return
        
        state = self.macro_states.get(next_key_id)
        if not state:
            print(f"[MacroEngine] ERROR: Invalid key_id from queue: {next_key_id}")
            self.process_queue()  # Try next
            return
        
        # ✅ CRITICAL: Check if macro is still active
        if not state.is_active:
            print(f"[MacroEngine] Macro {next_key_id} was cancelled while in queue, skipping")
            self.process_queue()  # Try next
            return
        
        # Start the macro
        self.queue_manager.set_slot(next_key_id)
        state.current_action_index = 0
        state.action_wait_until = None
        state.cycle_wait_until = None
        print(f"[MacroEngine] Started macro {next_key_id} from QUEUE")
    
    def check_sleeping_macros(self):
        """
        Check all SLEEPING toggle macros and wake them if timer expired.
        
        ✅ CRITICAL: Checks overflow before adding to queue!
        """
        current_time = time.monotonic()
        
        for state in self.macro_states.values():
            # Only check SLEEPING macros (is_active + cycle_wait_until)
            if not state.is_sleeping():
                continue
            
            # Check if timer expired
            if not state.check_and_clear_cycle_timer():
                continue
            
            # Timer expired, macro wants to execute again
            if self.queue_manager.is_slot_free():
                # Slot is free, take it immediately
                self.queue_manager.set_slot(state.key_id)
                state.current_action_index = 0
                state.action_wait_until = None
                print(f"[MacroEngine] Macro {state.key_id} woke from SLEEPING → ACTIVE")
            else:
                # Slot is busy, try to add to queue
                # ✅ CRITICAL: Check overflow before adding
                if not self.queue_manager.try_add_to_queue(state.key_id):
                    # Overflow! Emergency stop
                    print(f"[MacroEngine] CRITICAL: Queue overflow on wake!")
                    self.emergency_stop_all()
                    self.start_error_blink(duration=3.0, message="QUEUE OVERFLOW!")
                    return
                
                print(f"[MacroEngine] Macro {state.key_id} woke from SLEEPING → IN_QUEUE")
    
    # ============================================================
    # EVENT HANDLERS
    # ============================================================
    
    def handle_key_press(self, key_id):
        """
        Handle key press event.
        Implements hybrid priority system.
        
        Args:
            key_id (int): Key ID that was pressed (0-11)
        """
        if key_id not in self.macro_states:
            return
        
        state = self.macro_states[key_id]
        
        # ============================================
        # PRIORITY MACROS (Press/Hold)
        # ============================================
        if state.type in ["press", "hold"]:
            # Interrupt current macro (if any)
            current_slot = self.queue_manager.get_slot()
            if current_slot is not None:
                current_state = self.macro_states.get(current_slot)
                if current_state:
                    if current_state.type == "toggle":
                        # Interrupt toggle → SLEEPING
                        current_state.interrupt_to_sleeping()
                        print(f"[MacroEngine] Toggle macro {current_slot} interrupted by {state.type} → SLEEPING")
                    else:
                        # Stop press/hold
                        current_state.stop()
                        if current_state.type == "hold":
                            self.key_held[current_slot] = False  # ✅ Clear flag
                        print(f"[MacroEngine] {current_state.type.upper()} macro {current_slot} stopped by priority")
            
            # Take the slot
            self.queue_manager.set_slot(key_id)
            state.start()
            
            if state.type == "hold":
                self.key_held[key_id] = True
            
            print(f"[MacroEngine] {state.type.upper()} macro {key_id} started (priority)")
            return
        
        # ============================================
        # TOGGLE MACROS (Queued)
        # ============================================
        if state.type == "toggle":
            # Second press = cancel
            if state.is_active:
                # Stop the macro
                state.stop()
                state.cycle_wait_until = None
                state.action_wait_until = None
                
                # Remove from queue if there
                if self.queue_manager.is_in_queue(key_id):
                    self.queue_manager.remove_from_queue(key_id)
                
                # Free slot if owning it
                if self.queue_manager.get_slot() == key_id:
                    self.queue_manager.free_slot()
                    self.process_queue()
                
                print(f"[MacroEngine] Toggle macro {key_id} cancelled")
                return
            
            # First press = start
            state.is_active = True
            
            # Try to take slot
            if self.queue_manager.is_slot_free():
                self.queue_manager.set_slot(key_id)
                state.current_action_index = 0
                state.action_wait_until = None
                state.cycle_wait_until = None
                print(f"[MacroEngine] Toggle macro {key_id} started (SLOT free)")
            else:
                # ✅ CRITICAL: Check overflow BEFORE adding
                if self.queue_manager.get_queue_size() >= QueueManager.MAX_QUEUE_SIZE:
                    print(f"[MacroEngine] CRITICAL: Queue overflow!")
                    self.emergency_stop_all()
                    self.start_error_blink(duration=3.0, message="QUEUE OVERFLOW!")
                    return
                
                # Add to queue
                self.queue_manager.try_add_to_queue(key_id)
    
    def handle_key_release(self, key_id):
        """
        Handle key release event.
        
        Args:
            key_id (int): Key ID that was released (0-11)
        """
        if key_id not in self.macro_states:
            return
        
        state = self.macro_states[key_id]
        
        # Only relevant for hold macros
        if state.type == "hold":
            self.key_held[key_id] = False
            print(f"[MacroEngine] Hold key {key_id} released")
            
            # Note: Macro will stop on next execute_active_macro() call
            # when it checks is_key_held
    
    # ============================================================
    # EMERGENCY FUNCTIONS
    # ============================================================
    
    def emergency_stop_all(self):
        """
        Emergency stop all macros and clear queue.
        Called on encoder button press or queue overflow.
        """
        print(f"[MacroEngine] EMERGENCY STOP ALL")
        
        # Stop all macros
        for state in self.macro_states.values():
            state.stop()
        
        # Clear queue and slot
        self.queue_manager.clear_all()
        
        # Reset key_held flags
        for key_id in self.key_held:
            self.key_held[key_id] = False
        
        # Release all keys
        self.action_executor.release_all()
    
    def start_error_blink(self, duration=1.5, message="ERROR"):
        """
        Start emergency error blink (red LED).
        
        Args:
            duration (float): Blink duration in seconds
            message (str): Error message to display
        """
        self.emergency_blink_until = time.monotonic() + duration
        self.emergency_blink_message = message
        print(f"[MacroEngine] Error blink: {message} for {duration}s")
    
    def is_emergency_blinking(self):
        """Check if emergency blink is active."""
        if self.emergency_blink_until is None:
            return False
        
        if time.monotonic() >= self.emergency_blink_until:
            self.emergency_blink_until = None
            self.emergency_blink_message = ""
            return False
        
        return True
    
    # ============================================================
    # UTILITY FUNCTIONS
    # ============================================================
    
    def get_macro_state(self, key_id):
        """Get the state of a specific macro."""
        return self.macro_states.get(key_id)
    
    def get_queue_info(self):
        """
        Get queue information for display.
        
        Returns:
            dict: Queue info {slot, queue_size, queue_items}
        """
        return {
            'slot': self.queue_manager.get_slot(),
            'queue_size': self.queue_manager.get_queue_size(),
            'queue_items': self.queue_manager.get_queue_copy()
        }
    
    def check_invariants(self):
        """
        Check system invariants for debugging.
        Raises AssertionError if invariant violated.
        """
        slot = self.queue_manager.get_slot()
        
        # SLOT must be valid or None
        assert slot is None or slot in self.macro_states, f"Invalid SLOT: {slot}"
        
        # All queue items must be valid and active
        for key_id in self.queue_manager.queue:
            assert key_id in self.macro_states, f"Invalid key_id in QUEUE: {key_id}"
            assert self.macro_states[key_id].is_active, f"Inactive macro in QUEUE: {key_id}"
        
        # No duplicates in queue
        queue = self.queue_manager.get_queue_copy()
        assert len(queue) == len(set(queue)), f"Duplicates in QUEUE: {queue}"
        
        # If slot is occupied, macro must be active
        if slot is not None:
            assert self.macro_states[slot].is_active, f"Inactive macro owns SLOT: {slot}"
        
        print(f"[MacroEngine] ✅ Invariants check passed")
