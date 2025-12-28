"""
Main code v2 - Entry point with new hybrid priority system.

This implements the complete remaster architecture:
- Hybrid priority (Press/Hold interrupt, Toggle queued)
- SLOT + QUEUE execution
- Emergency stop support
- Profile switching
"""

from adafruit_macropad import MacroPad
import time

# Import supporting modules (unchanged)
from key_mapping import KEY_MAP, REVERSE_KEY_MAP
from profile_manager import ProfileManager
from macro_parser import parse_keys

# Import v2 modules
from macro_engine import MacroEngine
from display_manager import DisplayManager
from color_manager import ColorManager

# Initialize MacroPad hardware
macropad = MacroPad()

# Track encoder position for profile switching
last_encoder_position = macropad.encoder
last_encoder_button_state = False

# Startup
try:
    print("=" * 50)
    print("MacroPad Macro System v2 - REMASTER")
    print("=" * 50)
    
    # Initialize components
    display = DisplayManager(macropad)
    display.show_startup()
    
    color_manager = ColorManager('data/button_colors.json')
    profile_manager = ProfileManager('data/profiles', 'data/current_profile.json')
    
    # Initialize macro engine
    macro_engine = MacroEngine(
        keyboard=macropad.keyboard,
        mouse=macropad.mouse,
        consumer_control=macropad.consumer_control,
        parse_keys_func=parse_keys
    )
    
    # Load initial profile
    current_profile = profile_manager.get_current_profile()
    if current_profile is None:
        raise RuntimeError("No profiles found")
    
    # Convert profile format (buttons array -> macros dict)
    buttons_array = current_profile.get('buttons', [])
    macro_configs = {}
    if buttons_array:
        for i, button in enumerate(buttons_array):
            if button is not None:
                macro_configs[str(i)] = button
    
    if not macro_configs:
        raise RuntimeError("No macros in profile")
    
    # Load profile into engine
    profile_config = {'macros': macro_configs}
    macro_engine.load_profile(profile_config)
    
    # Initialize LEDs
    for i in range(12):
        physical_key = REVERSE_KEY_MAP.get(i, i)
        state = macro_engine.get_macro_state(i)
        if state:
            color = color_manager.get_color('ready')
        else:
            color = color_manager.get_color('off')
        macropad.pixels[physical_key] = color
    
    # Get all profile names for display navigation
    all_profiles = profile_manager.get_all_profile_names()
    
    # Initial display update
    display.update(macro_engine, current_profile['name'], all_profiles, last_encoder_position, force=True)
    
    print(f"✅ System ready! Profile: {current_profile['name']}")
    print(f"✅ Loaded {len(macro_configs)} macro(s)")
    print("=" * 50)

except Exception as e:
    error_msg = f"STARTUP ERROR:\n{str(e)[:50]}"
    print(error_msg)
    try:
        macropad.display_text(error_msg)
    except:
        pass
    while True:
        time.sleep(1)  # Halt

# ============================================================
# MAIN LOOP
# ============================================================

while True:
    try:
        # ⏰ Current time (used for emergency blink timing)
        current_time = time.monotonic()
        
        # ============================================
        # 1. ENCODER ROTATION (Profile switching)
        # ============================================
        current_encoder_position = macropad.encoder
        if current_encoder_position != last_encoder_position:
            direction = 1 if current_encoder_position > last_encoder_position else -1
            last_encoder_position = current_encoder_position
            
            print(f"\n{'='*50}")
            print(f"🔄 ENCODER ROTATION - Switching profile (direction: {direction})")
            print(f"{'='*50}")
            
            # CRITICAL: Full stop + queue clear
            macro_engine.emergency_stop_all()
            
            # Switch profile
            old_profile_name = current_profile['name']
            current_profile = profile_manager.switch_profile(direction)
            
            # Load new profile
            buttons_array = current_profile.get('buttons', [])
            macro_configs = {}
            if buttons_array:
                for i, button in enumerate(buttons_array):
                    if button is not None:
                        macro_configs[str(i)] = button
            
            profile_config = {'macros': macro_configs}
            macro_engine.load_profile(profile_config)
            
            # Reset LEDs
            for i in range(12):
                physical_key = REVERSE_KEY_MAP.get(i, i)
                state = macro_engine.get_macro_state(i)
                if state:
                    color = color_manager.get_color('ready')
                else:
                    color = color_manager.get_color('off')
                macropad.pixels[physical_key] = color
            
            # Show profile change
            display.show_profile_change(old_profile_name, current_profile['name'])
            display.update(macro_engine, current_profile['name'], all_profiles, last_encoder_position, force=True)
            
            print(f"✅ Loaded profile: {current_profile['name']}")
        
        # ============================================
        # 2. ENCODER BUTTON (Emergency stop)
        # ============================================
        encoder_button_pressed = macropad.encoder_switch
        if encoder_button_pressed and not last_encoder_button_state:
            print(f"\n🚨 EMERGENCY STOP - Encoder button pressed")
            macro_engine.emergency_stop_all()
            macro_engine.start_error_blink(duration=1.5, message="EMERGENCY STOP")
            
            # Reset LEDs to ready
            for i in range(12):
                physical_key = REVERSE_KEY_MAP.get(i, i)
                state = macro_engine.get_macro_state(i)
                if state:
                    color = color_manager.get_color('ready')
                else:
                    color = color_manager.get_color('off')
                macropad.pixels[physical_key] = color
        
        last_encoder_button_state = encoder_button_pressed
        
        # ============================================
        # 3. KEY EVENTS (Press/Release)
        # ============================================
        event = macropad.keys.events.get()
        if event:
            logical_key = KEY_MAP.get(event.key_number, event.key_number)
            
            if event.pressed:
                print(f"\n⬇️  KEY PRESS: {logical_key}")
                macro_engine.handle_key_press(logical_key)
            else:
                print(f"⬆️  KEY RELEASE: {logical_key}")
                macro_engine.handle_key_release(logical_key)
        
        # ============================================
        # 4. CHECK SLEEPING MACROS
        # ✅ BEFORE process_queue - so woken macros can enter queue
        # ============================================
        macro_engine.check_sleeping_macros()
        
        # ============================================
        # 5. PROCESS QUEUE
        # ✅ BEFORE execute_active_macro - so freed slot can be filled
        # ============================================
        macro_engine.process_queue()
        
        # ============================================
        # 6. EXECUTE ACTIVE MACRO
        # ✅ IN THE END - execution in stable state
        # ============================================
        macro_engine.execute_active_macro()
        
        # ============================================
        # 7. UPDATE DISPLAY
        # ============================================
        display.update(macro_engine, current_profile['name'], all_profiles, last_encoder_position)
        
        # ============================================
        # 8. UPDATE LEDS
        # ============================================
        # Handle emergency blink
        if macro_engine.is_emergency_blinking():
            # Flash all LEDs red
            emergency_color = color_manager.get_emergency_color()
            for i in range(12):
                physical_key = REVERSE_KEY_MAP.get(i, i)
                macropad.pixels[physical_key] = emergency_color
        else:
            # Normal LED updates
            queue_info = macro_engine.get_queue_info()
            
            for i in range(12):
                physical_key = REVERSE_KEY_MAP.get(i, i)
                state = macro_engine.get_macro_state(i)
                
                if state:
                    is_in_queue = i in queue_info['queue_items']
                    color = color_manager.get_color_for_macro(state, is_in_queue)
                else:
                    color = color_manager.get_color('off')
                
                macropad.pixels[physical_key] = color
        
        # ============================================
        # 9. (OPTIONAL) CHECK INVARIANTS
        # ============================================
        # Uncomment for debugging:
        # macro_engine.check_invariants()
        
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
        macro_engine.emergency_stop_all()
        break
    
    except Exception as e:
        print(f"\n❌ RUNTIME ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        macro_engine.emergency_stop_all()
        macro_engine.start_error_blink(duration=3.0, message=f"ERROR: {str(e)[:20]}")
        
        # Continue running (don't crash)
        time.sleep(0.1)
