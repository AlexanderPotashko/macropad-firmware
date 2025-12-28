"""
Display Manager v2 - Simple and clear display.

Two modes:
1. Idle mode: Show 3 profiles (prev | CURRENT | next)
2. Active mode: Show toggle macros with countdown timers
"""

import time


class DisplayManager:
    """
    Manages the OLED display output.
    
    Shows:
    - Idle: 3 profiles for navigation
    - Active: Toggle macros with timers only
    """
    
    def __init__(self, macropad):
        """
        Initialize display manager.
        
        Args:
            macropad: MacroPad instance
        """
        self.macropad = macropad
        self.last_update = 0
        self.update_interval = 0.2  # Update every 200ms
        self.last_text = ""
        
        # Create text display object once
        try:
            self.text_display = macropad.display_text()
        except AttributeError:
            self.text_display = None
            print("[DisplayManager] WARNING: No display available")
    
    def update(self, macro_engine, profile_name="", all_profiles=None, encoder_position=0, force=False):
        """
        Update the display.
        
        Args:
            macro_engine (MacroEngine): The macro engine instance
            profile_name (str): Current profile name
            all_profiles (list): List of all profile names for navigation
            encoder_position (int): Current encoder position for profile selection
            force (bool): Force update even if interval hasn't passed
        """
        if not self.text_display:
            return
        
        current_time = time.monotonic()
        
        # Throttle updates unless forced
        if not force and (current_time - self.last_update) < self.update_interval:
            return
        
        self.last_update = current_time
        
        # Check for emergency
        if macro_engine.is_emergency_blinking():
            text = self._format_emergency(macro_engine.emergency_blink_message)
        else:
            # Check if any toggle macros are active
            active_toggles = self._get_active_toggles(macro_engine)
            
            if active_toggles:
                # Mode 2: Show active toggles with timers
                text = self._format_active_toggles(active_toggles, current_time)
            else:
                # Mode 1: Show profile navigation
                text = self._format_profile_navigation(profile_name, all_profiles, encoder_position)
        
        # Only update if text changed
        if text != self.last_text:
            self.last_text = text
            self._render(text)
    
    def _get_active_toggles(self, macro_engine):
        """
        Get all active toggle macros.
        
        Args:
            macro_engine (MacroEngine): Macro engine
        
        Returns:
            list: List of (key_id, state) tuples for active toggles
        """
        active = []
        for key_id in range(12):
            state = macro_engine.get_macro_state(key_id)
            if state and state.type == 'toggle':
                state_name = state.get_state_name()
                # Show if ACTIVE, WAIT, SLEEPING, or IN_QUEUE
                if state_name in ['ACTIVE', 'WAIT', 'SLEEPING', 'IN_QUEUE']:
                    active.append((key_id, state))
        return active
    
    def _format_profile_navigation(self, current_profile, all_profiles, encoder_position):
        """
        Format profile navigation view.
        Shows: < Prev | CURRENT | Next >
        
        Args:
            current_profile (str): Current profile name
            all_profiles (list): All available profiles
            encoder_position (int): Encoder position
        
        Returns:
            str: Formatted display text
        """
        if not all_profiles or len(all_profiles) == 0:
            return "No profiles\navailable\n\nCheck data/"
        
        # Find current profile index
        try:
            current_idx = all_profiles.index(current_profile)
        except ValueError:
            current_idx = 0
        
        # Calculate prev/next based on encoder position
        # Encoder changes are relative to current profile
        total = len(all_profiles)
        prev_idx = (current_idx - 1) % total
        next_idx = (current_idx + 1) % total
        
        prev_name = all_profiles[prev_idx] if total > 1 else ""
        next_name = all_profiles[next_idx] if total > 1 else ""
        
        # Build display (4 lines, 16 chars each)
        lines = []
        lines.append("Profile Select:")
        lines.append("")
        
        # Show navigation
        if total > 1:
            lines.append(f"< {prev_name[:8]}")
            lines.append(f"> {current_profile[:13]}")
        else:
            lines.append("")
            lines.append(f"  {current_profile[:13]}")
        
        # Note: we don't show next here to keep it simple
        # User rotates encoder to see other profiles
        
        return "\n".join(lines)
    
    def _format_active_toggles(self, active_toggles, current_time):
        """
        Format active toggle macros with countdown timers.
        
        Args:
            active_toggles (list): List of (key_id, state) tuples
            current_time (float): Current time
        
        Returns:
            str: Formatted display text
        """
        lines = []
        
        # Header
        lines.append("Active Toggles:")
        
        # Show up to 3 toggle macros
        for i, (key_id, state) in enumerate(active_toggles[:3]):
            if i >= 3:
                break
            
            line = self._format_toggle_line(key_id, state, current_time)
            lines.append(line)
        
        # Pad to 4 lines
        while len(lines) < 4:
            lines.append("")
        
        return "\n".join(lines[:4])
    
    def _format_toggle_line(self, key_id, state, current_time):
        """
        Format single toggle line with countdown.
        Format: "#N Name: TIME"
        
        Args:
            key_id (int): Key ID
            state (MacroState): Macro state
            current_time (float): Current time
        
        Returns:
            str: Formatted line
        """
        state_name = state.get_state_name()
        
        # Short name (max 5 chars to fit timer)
        name = state.name[:5]
        
        # Calculate countdown
        if state_name == 'SLEEPING':
            # Time until next cycle
            remaining = state.cycle_wait_until - current_time
        elif state_name == 'WAIT':
            # Time until next action
            remaining = state.action_wait_until - current_time
        elif state_name == 'ACTIVE':
            remaining = 0
        elif state_name == 'IN_QUEUE':
            return f"#{key_id} {name:5s}: Q"
        else:
            return f"#{key_id} {name:5s}: ?"
        
        # Format time
        if remaining < 0:
            remaining = 0
        
        if remaining >= 3600:  # >= 1 hour
            time_str = f"{int(remaining/3600)}h"
        elif remaining >= 60:  # >= 1 minute
            time_str = f"{int(remaining/60)}m"
        else:
            time_str = f"{int(remaining)}s"
        
        return f"#{key_id} {name:5s}: {time_str}"
    
    def _format_emergency(self, message):
        """
        Format emergency error display.
        
        Args:
            message (str): Error message
        
        Returns:
            str: Formatted display text (4 lines)
        """
        lines = []
        lines.append("!!! ERROR !!!")
        lines.append("")
        lines.append(message[:16])
        lines.append("Press Enc=Reset")
        return "\n".join(lines)
    
    def _render(self, text):
        """
        Render text to display.
        
        Args:
            text (str): Text to display
        """
        try:
            if self.text_display:
                self.text_display.text = text
                self.text_display.show()
        except Exception as e:
            print(f"[DisplayManager] ERROR rendering: {e}")
    
    def show_profile_change(self, old_profile, new_profile):
        """
        Show profile change animation.
        
        Args:
            old_profile (str): Previous profile name
            new_profile (str): New profile name
        """
        text = f"Profile Change\n\n{old_profile} ->\n{new_profile}"
        self._render(text)
        time.sleep(0.5)  # Show for half second
    
    def show_startup(self):
        """Show startup screen."""
        text = "MacroPad v2\n\nInitializing...\nPlease wait"
        self._render(text)
    
    def clear(self):
        """Clear the display."""
        if self.text_display:
            try:
                self.text_display.text = ""
                self.text_display.show()
            except:
                pass
