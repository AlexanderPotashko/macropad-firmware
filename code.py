from adafruit_macropad import MacroPad
from key_mapping import KEY_MAP, REVERSE_KEY_MAP
from macro_engine import MacroExecutor
from display_manager import DisplayManager
from profile_manager import ProfileManager
from color_manager import ColorManager

# Initialize MacroPad
macropad = MacroPad()

# Track encoder position for profile switching
last_encoder_position = macropad.encoder

# Emergency stop blink state
emergency_blink_until = None
emergency_blink_state = False
last_blink_time = 0

try:
    # Show loading screen
    print("MacroPad Macro System Starting...")
    macropad.display_text("  Loading...\n\n Please wait")

    # Load color configuration
    color_manager = ColorManager('data/button_colors.json')

    # Load profiles
    profile_manager = ProfileManager('data/profiles', 'data/current_profile.json')
    current_profile = profile_manager.get_current_profile()
    
    if current_profile is None:
        print("ERROR: No profiles found")
        macropad.display_text("ERROR!\n\nNo profiles\nfound")
        while True:
            pass  # Halt
    
    # Load macros directly from profile buttons
    buttons_array = current_profile['buttons']
    
    # Convert array to dict (skip null entries)
    macro_configs = {}
    if buttons_array is not None:
        for i, button in enumerate(buttons_array):
            if button is not None:
                macro_configs[i] = button

    if not macro_configs:
        # Error loading macros
        print(f"ERROR: Failed to load profile macros")
        macropad.display_text(f"ERROR!\n\nFailed to load\nprofile")
        while True:
            pass  # Halt

    # Initialize components
    executor = MacroExecutor(macropad, macro_configs)
    display = DisplayManager(macropad)

    # Initial display update
    display.update(executor, current_profile['name'], force=True)

    # Initialize RGB LEDs using color manager
    for i in range(12):
        physical_key = REVERSE_KEY_MAP.get(i, i)
        if i in executor.macro_states:
            color = color_manager.get_color('ready', executor.macro_states[i].config.get('colors'))
        else:
            color = color_manager.get_color('no_macro')
        macropad.pixels[physical_key] = color

    print(f"System ready! Profile: {current_profile['name']}")

except Exception as e:
    # Critical startup error
    error_msg = f"STARTUP ERROR:\n{str(e)[:50]}"
    print(error_msg)
    macropad.display_text(error_msg)
    while True:
        pass  # Halt

# Main loop
while True:
    try:
        # Process encoder rotation (profile switching)
        current_encoder_position = macropad.encoder
        if current_encoder_position != last_encoder_position:
            direction = 1 if current_encoder_position > last_encoder_position else -1
            last_encoder_position = current_encoder_position
            
            print(f"ENCODER ROTATED - Switching profile (direction: {direction})")
            
            # Stop all current macros
            executor.stop_all()
            
            # Switch profile
            current_profile = profile_manager.switch_profile(direction)
            
            # Load macros directly from profile buttons
            buttons_array = current_profile['buttons']
            
            # Convert array to dict (skip null entries)
            macro_configs = {}
            if buttons_array is not None:
                for i, button in enumerate(buttons_array):
                    if button is not None:
                        macro_configs[i] = button
            
            if macro_configs:
                # Reinitialize executor with new macros
                executor = MacroExecutor(macropad, macro_configs)
                print(f"Loaded profile: {current_profile['name']}")
                
                # Reset all LEDs using color manager
                for i in range(12):
                    physical_key = REVERSE_KEY_MAP.get(i, i)
                    if i in executor.macro_states:
                        color = color_manager.get_color('ready', executor.macro_states[i].config.get('colors'))
                    else:
                        color = color_manager.get_color('no_macro')
                    macropad.pixels[physical_key] = color
                
                # Show profile name briefly
                macropad.display_text(f"  Profile:\n\n{current_profile['name']}")
                import time
                time.sleep(1.5)
            else:
                print(f"ERROR: Failed to load {macros_file}")
            
            # Force display update
            display.update(executor, current_profile['name'], force=True)
        
        # Process encoder button (emergency stop all macros)
        encoder_switch = macropad.encoder_switch
        if encoder_switch:
            print("ENCODER PRESSED - STOPPING ALL MACROS")
            executor.stop_all()
            # Start emergency blink (1.5 seconds)
            import time
            emergency_blink_until = time.monotonic() + 1.5
            emergency_blink_state = True
            last_blink_time = time.monotonic()
            # Force display update
            display.update(executor, current_profile['name'], force=True)
        
        # Process key events
        event = macropad.keys.events.get()
        
        if event:
            # Convert physical key number to logical
            physical_key = event.key_number
            logical_key = KEY_MAP.get(physical_key)
            
            if logical_key is not None:
                if event.pressed:
                    print(f"Key pressed: physical={physical_key}, logical={logical_key}")
                    executor.handle_key_press(logical_key)
                elif event.released:
                    print(f"Key released: physical={physical_key}, logical={logical_key}")
                    executor.handle_key_release(logical_key)
        
        # Update all active macros
        executor.update()
        
        # Update display (pass profile name)
        display.update(executor, current_profile['name'])
        
        # Handle emergency blink
        import time
        current_time = time.monotonic()
        
        if emergency_blink_until and current_time < emergency_blink_until:
            # Emergency blink active - toggle every 200ms
            if current_time - last_blink_time >= 0.2:
                emergency_blink_state = not emergency_blink_state
                last_blink_time = current_time
            
            # Set all LEDs to blink state
            if emergency_blink_state:
                blink_color = color_manager.get_color('error')
            else:
                blink_color = (0, 0, 0)
            
            for i in range(12):
                physical_key = REVERSE_KEY_MAP.get(i, i)
                macropad.pixels[physical_key] = blink_color
        elif emergency_blink_until and current_time >= emergency_blink_until:
            # Blink finished, clear state
            emergency_blink_until = None
            # Continue to normal LED update below
        
        # Update RGB LEDs based on macro states using ColorManager
        if not emergency_blink_until:
            for logical_key in range(12):
                physical_key = REVERSE_KEY_MAP.get(logical_key, logical_key)
                
                if logical_key in executor.macro_states:
                    state = executor.macro_states[logical_key]
                    color = color_manager.get_button_color(state, executor)
                    macropad.pixels[physical_key] = color
                else:
                    # No macro configured
                    color = color_manager.get_color('no_macro')
                    macropad.pixels[physical_key] = color
    
    except Exception as e:
        print(f"Main loop error: {e}")
        # Continue running despite errors
        import time
        time.sleep(0.1)