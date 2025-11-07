"""
Responder model for emergency evacuation sweep
"""

from typing import List, Tuple, Optional


class Responder:
    """Represents an emergency responder (firefighter, security, etc.)"""
    
    def __init__(self, responder_id: int, initial_position: str,
                 walk_speed: float = 1.5, stair_up_speed: float = 0.4,
                 stair_down_speed: float = 0.7, check_rate: float = 1.0,
                 base_check_time: float = 10.0):
        """
        Initialize a responder
        
        Args:
            responder_id: Unique identifier
            initial_position: Starting location ID
            walk_speed: Walking speed in m/s
            stair_up_speed: Speed going up stairs in m/s
            stair_down_speed: Speed going down stairs in m/s
            check_rate: Room check rate in s/m²
            base_check_time: Base time to check a room in seconds
        """
        self.id = responder_id
        self.initial_position = initial_position
        self.position = initial_position
        self.walk_speed = walk_speed
        self.stair_up_speed = stair_up_speed
        self.stair_down_speed = stair_down_speed
        self.check_rate = check_rate
        self.base_check_time = base_check_time
        
        # Path and timeline
        self.path: List[str] = [initial_position]
        self.timeline: List[dict] = [{
            'time': 0,
            'action': 'start',
            'location': initial_position
        }]
        self.current_time = 0.0
        self.rooms_checked: List[str] = []
        
    def move_to(self, location: str, distance: float, is_stairs: bool = False,
                floor_change: int = 0):
        """
        Move to a new location
        
        Args:
            location: Target location ID
            distance: Distance to travel in meters
            is_stairs: Whether movement involves stairs
            floor_change: Number of floors moved (positive=up, negative=down)
        """
        if is_stairs:
            if floor_change > 0:
                travel_time = distance / self.stair_up_speed
            else:
                travel_time = distance / self.stair_down_speed
        else:
            travel_time = distance / self.walk_speed
            
        self.current_time += travel_time
        self.position = location
        self.path.append(location)
        self.timeline.append({
            'time': self.current_time,
            'action': 'arrive',
            'location': location,
            'travel_time': travel_time
        })
        
    def check_room(self, room):
        """
        Check a room
        
        Args:
            room: Room object to check
        """
        check_time = room.calculate_check_time(self.base_check_time, self.check_rate)
        self.current_time += check_time
        self.rooms_checked.append(room.id)
        
        room.cleared = True
        room.cleared_at = self.current_time
        room.cleared_by = self.id
        
        self.timeline.append({
            'time': self.current_time,
            'action': 'check_complete',
            'location': room.id,
            'check_time': check_time
        })
        
    def reset(self):
        """Reset responder to initial state"""
        self.position = self.initial_position
        self.path = [self.initial_position]
        self.timeline = [{
            'time': 0,
            'action': 'start',
            'location': self.initial_position
        }]
        self.current_time = 0.0
        self.rooms_checked = []
        
    def get_total_time(self) -> float:
        """Get total time spent"""
        return self.current_time
    
    def get_total_distance(self) -> float:
        """Get total distance traveled (approximate)"""
        total_distance = 0
        for event in self.timeline:
            if 'travel_time' in event:
                # Approximate distance from travel time
                total_distance += event['travel_time'] * self.walk_speed
        return total_distance
    
    def __repr__(self):
        return f"Responder({self.id}, checked {len(self.rooms_checked)} rooms, time={self.current_time:.1f}s)"


class ResponderTeam:
    """Manages a team of responders"""
    
    def __init__(self, n_responders: int, initial_positions: Optional[List[str]] = None,
                 capabilities: Optional[dict] = None):
        """
        Initialize a team of responders
        
        Args:
            n_responders: Number of responders
            initial_positions: List of starting positions (default: all at 'E1')
            capabilities: Dictionary of capability parameters
        """
        if capabilities is None:
            capabilities = {}
            
        if initial_positions is None:
            initial_positions = ['E1'] * n_responders
        elif len(initial_positions) < n_responders:
            # Pad with 'E1'
            initial_positions.extend(['E1'] * (n_responders - len(initial_positions)))
            
        self.responders = []
        for i in range(n_responders):
            responder = Responder(
                responder_id=i + 1,
                initial_position=initial_positions[i],
                walk_speed=capabilities.get('walk_speed', 1.5),
                stair_up_speed=capabilities.get('stair_up_speed', 0.4),
                stair_down_speed=capabilities.get('stair_down_speed', 0.7),
                check_rate=capabilities.get('check_rate', 1.0),
                base_check_time=capabilities.get('base_check_time', 10.0)
            )
            self.responders.append(responder)
            
    def get_responder(self, responder_id: int) -> Responder:
        """Get responder by ID"""
        for responder in self.responders:
            if responder.id == responder_id:
                return responder
        raise ValueError(f"Responder {responder_id} not found")
    
    def reset_all(self):
        """Reset all responders"""
        for responder in self.responders:
            responder.reset()
            
    def get_max_time(self) -> float:
        """Get maximum time among all responders"""
        return max(r.current_time for r in self.responders)
    
    def get_total_distance(self) -> float:
        """Get total distance traveled by all responders"""
        return sum(r.get_total_distance() for r in self.responders)
    
    def __len__(self):
        return len(self.responders)
    
    def __iter__(self):
        return iter(self.responders)
    
    def __repr__(self):
        return f"ResponderTeam({len(self.responders)} responders, max_time={self.get_max_time():.1f}s)"

