# Display manager for OLED screen
import time


class DisplayManager:
    """Manages the OLED display output for macro status."""
    
    def __init__(self, macropad):
        """
        Initialize display manager.
        
        Args:
            macropad: MacroPad instance
        """
        self.macropad = macropad
        self.last_update = 0
        self.update_interval = 0.5  # Update every 500ms
        self.last_text = ""
        
        # Create text display object once
        self.text_display = macropad.display_text()
    
    def update(self, macro_executor, profile_name="", force=False):
        """
        Update the display with current macro states.
        
        Args:
            macro_executor (MacroExecutor): The macro executor instance
            profile_name (str): Current profile name to display
            force (bool): Force update even if interval hasn't passed
        """
        current_time = time.monotonic()
        
        # Throttle updates unless forced
        if not force and (current_time - self.last_update) < self.update_interval:
            return
        
        self.last_update = current_time
        
        # Get active macros
        active_macros = macro_executor.get_active_macros()
        
        # Build display text - use 4 lines (real screen capacity)
        lines = []
        
        if len(active_macros) == 0:
            # No active macros - show ready screen with profile name
            lines.append(" MacroPad Ready")
            lines.append(f" [{profile_name}]")
            lines.append(" Press any key")
            lines.append(" Enc=Prof Btn=STOP")
        else:
            # Show up to 4 active macros
            for i, (key_id, state) in enumerate(active_macros[:4]):
                line = self._format_macro_line(key_id, state)
                lines.append(line)
            
            # If more than 4, show count on last line
            if len(active_macros) > 4:
                # Replace last line with counter
                lines[3] = f"+{len(active_macros) - 3} more"
        
        # Join lines and display
        text = "\n".join(lines)
        
        # Only update if text changed (saves CPU)
        if text != self.last_text:
            self.last_text = text
            self._render(text)
    
    def _format_macro_line(self, key_id, state):
        """
        Format a line for displaying a macro.
        Optimized for 16 chars width, 4 lines.
        
        Timer logic by type:
        - ON: показывает wait обратный отсчет
        - HL: показывает wait обратный отсчет
        - TL: показывает общее время работы (прямой)
        
        Args:
            key_id (int): Logical key number (0-11)
            state (MacroState): Macro state
        
        Returns:
            str: Formatted line (max 16 chars)
        """
        # Type (2 letters) - only 3 types supported
        if state.loop:
            type_map = {
                'once': 'ON',
                'hold': 'HL',
                'toggle': 'TL'
            }
        else:
            type_map = {
                'once': 'ON',
                'hold': 'HL',
                'toggle': 'TL'
            }
        type_str = type_map.get(state.type, 'ON')
        
        # Timer logic depends on type
        timer_str = ""
        
        if state.type == 'toggle':
            # TL: Show total elapsed time (прямой отсчет)
            elapsed = state.get_elapsed_time()
            if elapsed < 60:
                timer_str = f"{elapsed}s"
            elif elapsed < 3600:
                mins = elapsed // 60
                secs = elapsed % 60
                timer_str = f"{mins}:{secs:02d}"
            else:
                hours = elapsed // 3600
                mins = (elapsed % 3600) // 60
                timer_str = f"{hours}h{mins:02d}"
        else:
            # ON or HL: Show only wait countdown (обратный отсчет)
            if state.wait_until:
                remaining = int(state.wait_until - time.monotonic())
                if remaining > 0:
                    timer_str = f"{remaining}s"
        
        # Format: "0 ON" or "0 ON 5s" or "2 TL 1:25"
        if timer_str:
            return f"{key_id} {type_str} {timer_str}"
        else:
            return f"{key_id} {type_str}"

    
    def _render(self, text):
        """
        Render text to the display.
        
        Args:
            text (str): Text to display (with newlines for multiple lines)
        """
        try:
            # Split text into lines
            lines = text.split('\n')
            
            # Update each line (SimpleTextDisplay supports 0-3 lines for 4 total)
            for i in range(4):
                if i < len(lines):
                    self.text_display[i].text = lines[i]
                else:
                    self.text_display[i].text = ""  # Clear unused lines
            
            # Show updated display
            self.text_display.show()
        except Exception as e:
            print(f"Display error: {e}")
    
    def show_error(self, message):
        """
        Show an error message on the display.
        
        Args:
            message (str): Error message
        """
        lines = [
            "ERROR!",
            "-" * 20,
            message[:40]  # Truncate long messages
        ]
        text = "\n".join(lines)
        self._render(text)
        self.last_text = text
    
    def show_loading(self):
        """Show loading screen."""
        text = "  MacroPad\n\n  Loading...\n  Please wait"
        self._render(text)
        self.last_text = text
