# Macro execution engine
import time
import random
from macro_parser import parse_keys


class MacroState:
    """Maintains the execution state of a single macro."""
    
    def __init__(self, key_id, config):
        """
        Initialize macro state.
        
        Args:
            key_id (int): Logical key number (0-11)
            config (dict): Macro configuration from JSON
        """
        self.key_id = key_id
        self.config = config
        self.actions = config['actions']
        self.current_index = 0
        self.is_active = False
        self.is_executing = False  # Currently executing actions (owns execution slot)
        self.is_key_held = False  # For 'hold' type macros
        
        # Timing
        self.wait_until = None  # Time when current wait finishes
        self.start_time = None  # When macro started
        
        # Configuration
        self.loop = config.get('loop', False)
        self.type = config.get('type', 'once')
        self.name = config.get('name', f'Macro {key_id}')
        
        # For nested repeat handling
        self.repeat_stack = []  # [(start_index, end_index, current_count, max_count), ...]
        self.repeat_just_finished = False  # Flag when repeat completes
    
    def start(self):
        """Start or restart the macro."""
        self.is_active = True
        self.is_executing = True  # Macro starts executing immediately
        self.current_index = 0
        self.wait_until = None
        self.start_time = time.monotonic()
        self.repeat_stack = []
        self.repeat_just_finished = False
        print(f"Started macro [{self.key_id}] {self.name}")
    
    def stop(self):
        """Stop the macro."""
        self.is_active = False
        self.is_executing = False
        self.wait_until = None
        self.repeat_stack = []
        self.repeat_just_finished = False
        print(f"Stopped macro [{self.key_id}] {self.name}")
    
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
            # Get action relative to repeat block
            repeat_actions = context['actions']
            repeat_index = context['current_index']
            
            if repeat_index < len(repeat_actions):
                return repeat_actions[repeat_index]
            else:
                # Finished one iteration of repeat
                context['current_count'] += 1
                if context['current_count'] < context['max_count']:
                    # Start next iteration
                    context['current_index'] = 0
                    return repeat_actions[0]
                else:
                    # Finished all repeats, pop from stack
                    self.repeat_stack.pop()
                    self.repeat_just_finished = True
                    # Don't advance yet - let execute_action handle wait
                    return self.actions[self.current_index]  # Return the repeat action itself
        
        # Normal action execution
        if self.current_index < len(self.actions):
            return self.actions[self.current_index]
        else:
            # Reached end of actions
            if self.loop:
                # Restart from beginning
                self.current_index = 0
                return self.actions[0]
            else:
                # Macro finished
                self.stop()
                return None
    
    def advance(self):
        """Move to the next action."""
        if self.repeat_stack:
            # Advance within repeat block
            self.repeat_stack[-1]['current_index'] += 1
        else:
            # Advance in main action list
            self.current_index += 1
    
    def enter_repeat(self, actions, count):
        """
        Enter a repeat block.
        
        Args:
            actions (list): Actions to repeat
            count (int): Number of times to repeat
        """
        self.repeat_stack.append({
            'actions': actions,
            'max_count': count,
            'current_count': 0,
            'current_index': 0
        })
    
    def get_elapsed_time(self):
        """Get elapsed time since macro started (in seconds)."""
        if self.start_time:
            return int(time.monotonic() - self.start_time)
        return 0
    
    def is_last_action(self):
        """
        Check if current action is the last one before loop/end.
        
        Returns:
            bool: True if this is the last action
        """
        if self.repeat_stack:
            # Inside repeat block
            context = self.repeat_stack[-1]
            repeat_actions = context['actions']
            repeat_index = context['current_index']
            
            # Check if last action in repeat AND last iteration
            if repeat_index == len(repeat_actions) - 1:
                if context['current_count'] == context['max_count'] - 1:
                    # Last action of last iteration
                    # Check if this repeat is last action in main sequence
                    if not self.repeat_stack[:-1]:  # No nested repeats
                        return self.current_index == len(self.actions) - 1
        else:
            # Normal action
            return self.current_index == len(self.actions) - 1
        
        return False


class MacroExecutor:
    """Manages and executes all active macros in parallel."""
    
    def __init__(self, macropad, macro_configs):
        """
        Initialize the macro executor.
        
        Args:
            macropad: MacroPad instance
            macro_configs (dict): Dictionary of macro configs keyed by logical key number
        """
        self.macropad = macropad
        self.macro_states = {}
        
        # Execution queue system
        self.currently_executing = None  # key_id of macro currently owning execution slot
        self.execution_queue = []  # FIFO queue of key_ids waiting to execute
        self.MAX_QUEUE_SIZE = 50  # Maximum queue size to prevent overflow
        
        # Create MacroState for each configured macro
        for key_id, config in macro_configs.items():
            self.macro_states[key_id] = MacroState(key_id, config)
        
        print(f"MacroExecutor initialized with {len(self.macro_states)} macro(s)")
    
    def _try_start_macro(self, key_id):
        """
        Try to start a macro, or add it to queue if execution slot is taken.
        
        Args:
            key_id (int): Logical key number (0-11)
        """
        state = self.macro_states[key_id]
        
        # Check if execution slot is available
        if self.currently_executing is None:
            # Slot is free, take it and start
            self.currently_executing = key_id
            state.start()  # Sets is_active=True, is_executing=True
            print(f"Macro {key_id} acquired execution slot")
        else:
            # Slot is taken, add to queue
            if len(self.execution_queue) >= self.MAX_QUEUE_SIZE:
                print(f"WARNING: Execution queue is full ({self.MAX_QUEUE_SIZE}), cannot add macro {key_id}")
                return
            
            if key_id not in self.execution_queue:
                # Mark as active but not executing (waiting in queue)
                state.is_active = True
                state.start_time = time.monotonic()
                self.execution_queue.append(key_id)
                print(f"Macro {key_id} added to queue (position {len(self.execution_queue)})")
    
    def _release_execution_slot(self):
        """
        Release the current execution slot.
        Next macro from queue will be started in update() loop.
        """
        if self.currently_executing is not None:
            print(f"Macro {self.currently_executing} released execution slot")
            self.currently_executing = None
        # Note: Queue processing moved to update() for better control flow
    
    def handle_key_press(self, key_id):
        """
        Handle a key press event.
        
        Args:
            key_id (int): Logical key number (0-11)
        """
        if key_id not in self.macro_states:
            print(f"No macro configured for key {key_id}")
            return
        
        state = self.macro_states[key_id]
        
        if state.type == 'once':
            # Start macro (will run once)
            self._try_start_macro(key_id)
        
        elif state.type == 'hold':
            # Start macro and mark key as held
            state.is_key_held = True
            if not state.is_active:
                self._try_start_macro(key_id)
        
        elif state.type == 'toggle':
            # Toggle on/off
            if state.is_active:
                state.stop()
                # Release all held keys (in case press_down was used)
                self.macropad.keyboard.release_all()
                # Remove ALL instances of this macro from queue
                self.execution_queue = [kid for kid in self.execution_queue if kid != key_id]
                # If this was the currently executing macro, release slot
                if self.currently_executing == key_id:
                    self._release_execution_slot()
                print(f"Macro {key_id} cancelled and removed from queue")
            else:
                self._try_start_macro(key_id)
    
    def handle_key_release(self, key_id):
        """
        Handle a key release event.
        
        Args:
            key_id (int): Logical key number (0-11)
        """
        if key_id not in self.macro_states:
            return
        
        state = self.macro_states[key_id]
        
        if state.type == 'hold':
            # Stop macro when key released
            state.is_key_held = False
            if state.is_active:
                state.stop()
                # Release all held keys (in case press_down was used)
                self.macropad.keyboard.release_all()
                # Remove ALL instances of this macro from queue
                self.execution_queue = [kid for kid in self.execution_queue if kid != key_id]
                # If this was the currently executing macro, release slot
                if self.currently_executing == key_id:
                    self._release_execution_slot()
                print(f"Hold macro {key_id} released and removed from queue")
    
    def update(self):
        """
        Update all active macros. Call this every loop iteration.
        This is the main execution loop for all macros.
        """
        current_time = time.monotonic()
        
        # Step 1: Check SLEEPING macros (waiting for timer to wake up)
        for state in self.macro_states.values():
            if state.is_active and not state.is_executing:
                # Macro is in SLEEP mode (waiting for timer)
                if state.wait_until and current_time >= state.wait_until:
                    # Timer expired - macro wants to wake up
                    state.wait_until = None
                    
                    # Try to acquire execution slot
                    if self.currently_executing is None:
                        # Slot is free - start executing immediately
                        self.currently_executing = state.key_id
                        state.is_executing = True
                        state.current_index = 0  # Restart from beginning
                        state.repeat_stack = []
                        state.repeat_just_finished = False
                        print(f"Macro {state.key_id} woke up from SLEEP and acquired slot")
                    else:
                        # Slot is taken - add to queue
                        if state.key_id not in self.execution_queue:
                            self.execution_queue.append(state.key_id)
                            # NOTE: Do NOT set is_executing or reset index yet
                            # This will be done in Step 2 of update() when starting from queue
                            print(f"Macro {state.key_id} woke up from SLEEP → IN_QUEUE (position {len(self.execution_queue)})")
        
        # Step 2: Process execution queue - start macros that are waiting
        # If macro is in queue, it MUST execute (removal only via toggle OFF or emergency stop)
        if self.currently_executing is None and self.execution_queue:
            next_key_id = self.execution_queue.pop(0)
            self.currently_executing = next_key_id
            state = self.macro_states[next_key_id]
            
            # Start executing from queue
            state.is_executing = True
            state.is_active = True  # Ensure active when executing from queue
            state.current_index = 0
            state.wait_until = None
            state.repeat_stack = []
            state.repeat_just_finished = False
        
        # Step 3: Execute ACTIVE macro (the one that owns execution slot)
        if self.currently_executing is not None:
            state = self.macro_states.get(self.currently_executing)
            if state and state.is_executing:
                # Check if waiting between actions (WAIT state)
                if state.wait_until:
                    if current_time >= state.wait_until:
                        # Wait finished, clear it and advance
                        state.wait_until = None
                        state.advance()
                        # Note: if this was last action, slot was already released in _handle_action_wait
                    else:
                        # Still waiting
                        pass  # Do nothing, continue waiting
                else:
                    # Not waiting, execute next action
                    action = state.get_current_action()
                    
                    if action is None:
                        # Macro finished (shouldn't happen often)
                        # For non-loop macros that somehow get here
                        if not state.loop:
                            state.stop()
                            self._release_execution_slot()
                    else:
                        # Execute the action
                        self._execute_action(action, state)
    
    def _execute_action(self, action, state):
        """
        Execute a single action.
        
        Args:
            action (dict): Action configuration
            state (MacroState): Macro state
        """
        action_type = action['type']
        is_last = state.is_last_action()
        
        try:
            if action_type == 'press':
                self._execute_press(action)
                self._handle_action_wait(action, state, is_last)
            
            elif action_type == 'press_down':
                self._execute_press_down(action)
                self._handle_action_wait(action, state, is_last)
            
            elif action_type == 'press_up':
                self._execute_press_up(action)
                self._handle_action_wait(action, state, is_last)
            
            elif action_type == 'type':
                self._execute_type(action)
                self._handle_action_wait(action, state, is_last)
            
            elif action_type == 'wait':
                ms = action['ms']
                # If last action in loop, ensure minimum 1000ms
                if is_last and state.loop:
                    ms = max(ms, 1000)
                    print(f"Macro {state.key_id} last wait action: {ms}ms (min 1000ms)")
                    # Set wait timer and immediately go to SLEEP
                    state.wait_until = time.monotonic() + (ms / 1000.0)
                    state.is_executing = False
                    state.current_index = 0
                    self._release_execution_slot()
                    print(f"Macro {state.key_id} → SLEEP for {ms}ms, slot released")
                else:
                    # Wait between actions - hold slot
                    state.wait_until = time.monotonic() + (ms / 1000.0)
            
            elif action_type == 'wait_random':
                min_ms = action['min']
                max_ms = action['max']
                ms = random.randint(min_ms, max_ms)
                # If last action in loop, ensure minimum 1000ms
                if is_last and state.loop:
                    ms = max(ms, 1000)
                    print(f"Macro {state.key_id} last wait_random action: {ms}ms (min 1000ms)")
                    # Set wait timer and immediately go to SLEEP
                    state.wait_until = time.monotonic() + (ms / 1000.0)
                    state.is_executing = False
                    state.current_index = 0
                    self._release_execution_slot()
                    print(f"Macro {state.key_id} → SLEEP for {ms}ms, slot released")
                else:
                    # Wait between actions - hold slot
                    state.wait_until = time.monotonic() + (ms / 1000.0)
            
            elif action_type == 'mouse_click':
                self._execute_mouse_click(action)
                self._handle_action_wait(action, state, is_last)
            
            elif action_type == 'mouse_move':
                self._execute_mouse_move(action)
                self._handle_action_wait(action, state, is_last)
            
            elif action_type == 'mouse_scroll':
                self._execute_mouse_scroll(action)
                self._handle_action_wait(action, state, is_last)
            
            elif action_type == 'repeat':
                if state.repeat_just_finished:
                    # Repeat just completed - handle wait parameter
                    state.repeat_just_finished = False
                    self._handle_action_wait(action, state, is_last)
                    # NOTE: _handle_action_wait already calls advance() if needed
                else:
                    # First time seeing repeat - enter it
                    self._execute_repeat(action, state)
                    # Don't advance, enter_repeat will handle it
            
            else:
                print(f"Unknown action type: {action_type}")
                state.advance()
        
        except Exception as e:
            print(f"Error executing action {action_type}: {e}")
            state.advance()
    
    def _handle_action_wait(self, action, state, is_last):
        """
        Handle wait timing for actions (press, type, mouse_click, etc).
        Ensures minimum 1000ms wait for last action in loop.
        """
        # Calculate wait time
        if 'wait' in action:
            wait_ms = action['wait']
        elif 'wait_random' in action:
            wr = action['wait_random']
            wait_ms = random.randint(wr['min'], wr['max'])
        else:
            wait_ms = 0
        
        # If this is the last action in a loop, ensure minimum 1000ms
        if is_last and state.loop:
            wait_ms = max(wait_ms, 1000)
            print(f"Macro {state.key_id} last action wait: {wait_ms}ms (min 1000ms)")
        
        if wait_ms > 0:
            state.wait_until = time.monotonic() + (wait_ms / 1000.0)
            
            # CRITICAL: If last action in loop - transition to SLEEP immediately
            if is_last and state.loop:
                # Go to SLEEP mode - release slot NOW
                state.is_executing = False
                state.current_index = 0  # Reset for next cycle
                self._release_execution_slot()
                print(f"Macro {state.key_id} → SLEEP for {wait_ms}ms, slot released")
            # Otherwise wait will be handled in update() while holding slot
        else:
            # No wait
            if is_last:
                if state.loop:
                    # Last action without wait - add default 1000ms
                    state.wait_until = time.monotonic() + 1.0
                    state.is_executing = False
                    state.current_index = 0
                    self._release_execution_slot()
                    print(f"Macro {state.key_id} last action no wait → SLEEP 1000ms, slot released")
                else:
                    # Once macro finished
                    state.stop()
                    self._release_execution_slot()
            else:
                # Not last - advance immediately
                state.advance()
    
    def _transition_to_sleep(self, state):
        """
        Transition macro to SLEEP state.
        Releases execution slot and prepares for next cycle.
        """
        state.is_executing = False
        self._release_execution_slot()
        print(f"Macro {state.key_id} → SLEEP (wait_until set)")
    
    def _execute_press(self, action):
        """Execute keyboard press action."""
        keys_string = action['keys']
        keycodes = parse_keys(keys_string)
        
        if keycodes:
            self.macropad.keyboard.send(*keycodes)
        else:
            print(f"Failed to parse keys: {keys_string}")
    
    def _execute_press_down(self, action):
        """Execute keyboard press down (hold) action."""
        keys_string = action['keys']
        keycodes = parse_keys(keys_string)
        
        if keycodes:
            self.macropad.keyboard.press(*keycodes)
        else:
            print(f"Failed to parse keys: {keys_string}")
    
    def _execute_press_up(self, action):
        """Execute keyboard press up (release) action."""
        keys_string = action['keys']
        keycodes = parse_keys(keys_string)
        
        if keycodes:
            self.macropad.keyboard.release(*keycodes)
        else:
            print(f"Failed to parse keys: {keys_string}")
    
    def _execute_type(self, action):
        """Execute text typing action."""
        text = action['text']
        self.macropad.keyboard_layout.write(text)
    
    def _execute_wait(self, action, state):
        """Execute wait action."""
        ms = action['ms']
        state.wait_until = time.monotonic() + (ms / 1000.0)
    
    def _execute_wait_random(self, action, state):
        """Execute random wait action."""
        min_ms = action['min']
        max_ms = action['max']
        ms = random.randint(min_ms, max_ms)
        state.wait_until = time.monotonic() + (ms / 1000.0)
    
    def _execute_mouse_click(self, action):
        """Execute mouse click action."""
        button = action.get('button', 'left')
        
        if button == 'left':
            self.macropad.mouse.click(self.macropad.Mouse.LEFT_BUTTON)
        elif button == 'right':
            self.macropad.mouse.click(self.macropad.Mouse.RIGHT_BUTTON)
        elif button == 'middle':
            self.macropad.mouse.click(self.macropad.Mouse.MIDDLE_BUTTON)
    
    def _execute_mouse_move(self, action):
        """Execute mouse move action."""
        x = action.get('x', 0)
        y = action.get('y', 0)
        self.macropad.mouse.move(x, y)
    
    def _execute_mouse_scroll(self, action):
        """Execute mouse scroll action."""
        amount = action.get('amount', 0)
        self.macropad.mouse.move(wheel=amount)
    
    def _execute_repeat(self, action, state):
        """Execute repeat action (enter repeat context)."""
        count = action['count']
        actions = action['actions']
        state.enter_repeat(actions, count)
    
    def get_active_macros(self):
        """
        Get list of active macro states.
        
        Returns:
            list: List of (key_id, MacroState) tuples for active macros
        """
        return [(k, v) for k, v in self.macro_states.items() if v.is_active]
    
    def stop_all(self):
        """Stop all active macros and clear execution queue."""
        for state in self.macro_states.values():
            if state.is_active:
                state.stop()
        
        # Release all held keys (important for press_down/press_up)
        self.macropad.keyboard.release_all()
        
        # Clear execution system
        self.currently_executing = None
        self.execution_queue = []
        print("Stopped all macros and cleared execution queue")
