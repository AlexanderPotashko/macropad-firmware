# Profile management system
import json

# CircuitPython has basic os support
try:
    import os
    HAS_OS = True
except ImportError:
    HAS_OS = False
    print("WARNING: No os module, profile loading may fail")


class ProfileManager:
    """Manages macro profiles and switching between them."""
    
    def __init__(self, profiles_dir='data/profiles', current_profile_file='data/current_profile.json'):
        """
        Initialize the profile manager.
        
        Args:
            profiles_dir (str): Directory containing profile JSON files
            current_profile_file (str): File storing current profile name
        """
        self.profiles_dir = profiles_dir
        self.current_profile_file = current_profile_file
        self.profiles = []
        self.current_profile_name = None
        self.load_profiles()
        self.load_current_profile()
    
    def load_profiles(self):
        """
        Load all profiles from profiles directory.
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            # List files in directory
            if not HAS_OS:
                print("ERROR: Cannot load profiles without os module")
                return False
            
            try:
                profile_files = [f for f in os.listdir(self.profiles_dir) 
                               if f.endswith('.json')]
            except Exception as e:
                print(f"ERROR: Cannot list profiles directory: {e}")
                return False
            
            if not profile_files:
                print("ERROR: No profile files found")
                return False
            
            self.profiles = []
            for filename in sorted(profile_files):
                filepath = self.profiles_dir + '/' + filename
                try:
                    with open(filepath, 'r') as f:
                        profile_data = json.load(f)
                    
                    # Profile format: {name: "...", buttons: [{macro}, null, ...]}
                    if 'name' in profile_data and 'buttons' in profile_data:
                        self.profiles.append({
                            'filename': filename,
                            'name': profile_data['name'],
                            'data': profile_data
                        })
                        print(f"Loaded profile: {profile_data['name']} from {filename}")
                except Exception as e:
                    print(f"ERROR loading {filename}: {e}")
                    continue
            
            return len(self.profiles) > 0
            
        except Exception as e:
            print(f"ERROR scanning profiles directory: {e}")
            return False
    
    def load_current_profile(self):
        """Load current profile name from file."""
        try:
            try:
                with open(self.current_profile_file, 'r') as f:
                    data = json.load(f)
                    profile_path = data.get('current', '').strip()
                
                # Извлекаем имя профиля из пути к файлу
                if profile_path:
                    # Загружаем профиль напрямую из файла
                    try:
                        with open(profile_path, 'r') as f:
                            profile_data = json.load(f)
                            self.current_profile_name = profile_data.get('name', '').lower()
                            print(f"Current profile: {self.current_profile_name} (from {profile_path})")
                    except OSError:
                        print(f"WARNING: Profile file not found: {profile_path}")
                        # Fallback to first profile
                        if self.profiles:
                            self.current_profile_name = self.profiles[0]['name'].lower()
                            self.save_current_profile()
                else:
                    # Fallback to first profile
                    if self.profiles:
                        self.current_profile_name = self.profiles[0]['name'].lower()
                        self.save_current_profile()
            except OSError:
                # File doesn't exist, default to first profile
                if self.profiles:
                    self.current_profile_name = self.profiles[0]['name'].lower()
                    self.save_current_profile()
        except Exception as e:
            print(f"ERROR loading current profile: {e}")
            if self.profiles:
                self.current_profile_name = self.profiles[0]['name'].lower()
    
    def save_current_profile(self):
        """Save current profile path to file."""
        try:
            # Найти путь к файлу профиля по имени
            profile_path = None
            for profile in self.profiles:
                if profile['name'].lower() == self.current_profile_name:
                    profile_path = self.profiles_dir + '/' + profile['filename']
                    break
            
            if profile_path:
                print(f"DEBUG: Writing to {self.current_profile_file}: {profile_path}")
                with open(self.current_profile_file, 'w') as f:
                    json.dump({'current': profile_path}, f, indent=2)
                    f.flush()  # Force write to disk
                print(f"Saved current profile: {self.current_profile_name} -> {profile_path}")
                
                # Verify write
                try:
                    with open(self.current_profile_file, 'r') as f:
                        verify = json.load(f)
                        print(f"DEBUG: Verification read: {verify.get('current')}")
                except Exception as e:
                    print(f"WARNING: Could not verify write: {e}")
            else:
                print(f"ERROR: Could not find profile file for {self.current_profile_name}")
        except Exception as e:
            print(f"ERROR saving current profile: {e}")
    
    def get_current_profile(self):
        """
        Get current active profile data.
        
        Returns:
            dict: Profile data or None if not found
        """
        for profile in self.profiles:
            if profile['name'].lower() == self.current_profile_name:
                return profile['data']
        
        # Fallback to first profile
        if self.profiles:
            return self.profiles[0]['data']
        return None
    
    def get_profile_count(self):
        """Get number of available profiles."""
        return len(self.profiles)
    
    def switch_profile(self, direction=1):
        """
        Switch to next/previous profile.
        
        Args:
            direction (int): 1 for next, -1 for previous
        
        Returns:
            dict: New current profile data or None
        """
        if not self.profiles:
            return None
        
        # Find current profile index
        current_idx = 0
        for i, profile in enumerate(self.profiles):
            if profile['name'].lower() == self.current_profile_name:
                current_idx = i
                break
        
        # Calculate new index
        new_idx = (current_idx + direction) % len(self.profiles)
        self.current_profile_name = self.profiles[new_idx]['name'].lower()
        self.save_current_profile()
        
        print(f"Switched to profile: {self.profiles[new_idx]['name']}")
        return self.profiles[new_idx]['data']
    
    def get_profile_name(self):
        """Get current profile name."""
        current = self.get_current_profile()
        return current['name'] if current else "Unknown"
    
    def get_all_profile_names(self):
        """
        Get list of all profile names.
        
        Returns:
            list: List of profile names
        """
        return [profile['name'] for profile in self.profiles]

