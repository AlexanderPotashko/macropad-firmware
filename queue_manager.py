"""
Queue Manager - Manages the macro execution queue (SLOT + QUEUE system).

This module implements:
- Single execution slot (SLOT) - one macro executes at a time
- FIFO queue (QUEUE) - waiting macros
- Overflow protection (max 1000 items)
- Duplicate prevention
"""


class QueueManager:
    """
    Manages the macro execution queue system.
    
    System:
    - SLOT: The currently executing macro (key_id or None)
    - QUEUE: List of key_ids waiting to execute (FIFO order)
    - MAX_QUEUE_SIZE: 1000 items (emergency limit)
    """
    
    MAX_QUEUE_SIZE = 1000
    
    def __init__(self):
        """Initialize the queue manager."""
        self.slot = None  # Currently executing macro (key_id or None)
        self.queue = []   # List of waiting key_ids (FIFO)
        
    def is_slot_free(self):
        """Check if execution slot is available."""
        return self.slot is None
    
    def get_slot(self):
        """Get the key_id of the macro owning the slot."""
        return self.slot
    
    def set_slot(self, key_id):
        """
        Assign a macro to the execution slot.
        
        Args:
            key_id (int or None): Key ID to assign, or None to free the slot
        """
        if key_id is not None:
            print(f"[QueueManager] SLOT = {key_id}")
        else:
            print(f"[QueueManager] SLOT freed")
        self.slot = key_id
    
    def free_slot(self):
        """Free the execution slot."""
        self.set_slot(None)
    
    def try_add_to_queue(self, key_id):
        """
        Try to add a macro to the queue.
        
        ✅ CRITICAL: Checks overflow BEFORE adding!
        
        Args:
            key_id (int): Key ID to add
            
        Returns:
            bool: True if added successfully, False if overflow or duplicate
        """
        # Check for duplicate
        if key_id in self.queue:
            print(f"[QueueManager] Macro {key_id} already in QUEUE")
            return True  # Not an error, just already there
        
        # ✅ CRITICAL: Check overflow BEFORE adding
        if len(self.queue) >= self.MAX_QUEUE_SIZE:
            print(f"[QueueManager] CRITICAL: Queue overflow! Size: {len(self.queue)}")
            return False
        
        # Add to queue
        self.queue.append(key_id)
        print(f"[QueueManager] Macro {key_id} → IN_QUEUE (position {len(self.queue)})")
        return True
    
    def remove_from_queue(self, key_id):
        """
        Remove a macro from the queue.
        
        Args:
            key_id (int): Key ID to remove
            
        Returns:
            bool: True if removed, False if not in queue
        """
        if key_id in self.queue:
            self.queue.remove(key_id)
            print(f"[QueueManager] Macro {key_id} removed from QUEUE")
            return True
        return False
    
    def is_in_queue(self, key_id):
        """Check if a macro is in the queue."""
        return key_id in self.queue
    
    def get_queue_size(self):
        """Get the current queue size."""
        return len(self.queue)
    
    def get_queue_copy(self):
        """Get a copy of the queue for display purposes."""
        return self.queue.copy()
    
    def pop_next_from_queue(self):
        """
        Get the next macro from the queue.
        
        Returns:
            int or None: Next key_id, or None if queue is empty
        """
        if self.queue:
            next_key_id = self.queue.pop(0)
            print(f"[QueueManager] Popped macro {next_key_id} from QUEUE (remaining: {len(self.queue)})")
            return next_key_id
        return None
    
    def clear_queue(self):
        """Clear all items from the queue."""
        if self.queue:
            print(f"[QueueManager] Clearing QUEUE (had {len(self.queue)} items)")
            self.queue.clear()
    
    def clear_all(self):
        """Clear both slot and queue (emergency stop)."""
        print(f"[QueueManager] EMERGENCY: Clearing SLOT and QUEUE")
        self.slot = None
        self.queue.clear()
    
    def get_status_string(self):
        """
        Get a human-readable status string for debugging.
        
        Returns:
            str: Status string
        """
        if self.slot is None:
            slot_str = "empty"
        else:
            slot_str = f"macro {self.slot}"
        
        return f"SLOT: {slot_str}, QUEUE: {len(self.queue)} items {self.queue}"
    
    def __repr__(self):
        """String representation for debugging."""
        return f"QueueManager(slot={self.slot}, queue_size={len(self.queue)})"
