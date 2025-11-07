"""
Building model for emergency evacuation sweep optimization
"""

import json
import numpy as np
from typing import List, Dict, Tuple, Optional


class Room:
    """Represents a room in the building"""
    
    def __init__(self, room_id: str, area: float, position: Tuple[float, float],
                 floor: int = 1, room_type: str = "office", occupancy: int = 0,
                 priority: int = 1, check_complexity: float = 1.0):
        """
        Initialize a room
        
        Args:
            room_id: Unique room identifier
            area: Room area in square meters
            position: (x, y) coordinates
            floor: Floor number (1-indexed)
            room_type: Type of room (office, daycare, lab, etc.)
            occupancy: Typical number of occupants
            priority: Priority level (1=normal, 2=high, 3=critical)
            check_complexity: Multiplier for check time (1.0=normal, 2.0=complex)
        """
        self.id = room_id
        self.area = area
        self.position = position
        self.floor = floor
        self.type = room_type
        self.occupancy = occupancy
        self.priority = priority
        self.check_complexity = check_complexity
        self.cleared = False
        self.cleared_at = None
        self.cleared_by = None
        
    def calculate_check_time(self, base_time: float = 10, rate: float = 1.0) -> float:
        """
        Calculate time required to check this room
        
        Args:
            base_time: Base check time in seconds
            rate: Check rate in seconds per square meter
            
        Returns:
            Total check time in seconds
        """
        return base_time + rate * self.area * self.check_complexity
    
    def __repr__(self):
        return f"Room({self.id}, floor={self.floor}, area={self.area}m²)"


class Building:
    """Represents a building with rooms, corridors, exits, and stairs"""
    
    def __init__(self, name: str = "Building", n_floors: int = 1):
        """
        Initialize a building
        
        Args:
            name: Building name
            n_floors: Number of floors
        """
        self.name = name
        self.n_floors = n_floors
        self.rooms: Dict[str, Room] = {}
        self.corridors: Dict[str, Dict] = {}
        self.exits: Dict[str, Dict] = {}
        self.stairs: Dict[str, Dict] = {}
        self.connections: List[Dict] = []
        
        # Distance cache for performance
        self._distance_cache: Dict[Tuple[str, str], float] = {}
        
    def add_room(self, room: Room):
        """Add a room to the building"""
        self.rooms[room.id] = room
        
    def add_exit(self, exit_id: str, position: Tuple[float, float], floor: int = 1):
        """Add an exit to the building"""
        self.exits[exit_id] = {
            'id': exit_id,
            'position': position,
            'floor': floor
        }
        
    def add_corridor(self, corridor_id: str, start: Tuple[float, float],
                    end: Tuple[float, float], floor: int = 1, width: float = 2.0):
        """Add a corridor to the building"""
        self.corridors[corridor_id] = {
            'id': corridor_id,
            'start': start,
            'end': end,
            'floor': floor,
            'width': width,
            'length': np.linalg.norm(np.array(end) - np.array(start))
        }
        
    def add_stairs(self, stair_id: str, position: Tuple[float, float],
                  connects: List[int]):
        """Add stairs connecting multiple floors"""
        self.stairs[stair_id] = {
            'id': stair_id,
            'position': position,
            'connects': connects
        }
        
    def add_connection(self, from_id: str, to_id: str, distance: float):
        """Add a connection between two locations"""
        self.connections.append({
            'from': from_id,
            'to': to_id,
            'distance': distance
        })
        # Add reverse connection
        self.connections.append({
            'from': to_id,
            'to': from_id,
            'distance': distance
        })
        
    def get_distance(self, loc1: str, loc2: str) -> float:
        """
        Get distance between two locations
        
        Args:
            loc1: First location ID
            loc2: Second location ID
            
        Returns:
            Distance in meters, or np.inf if not connected
        """
        # Check cache
        cache_key = (loc1, loc2)
        if cache_key in self._distance_cache:
            return self._distance_cache[cache_key]
            
        # Direct connection
        for conn in self.connections:
            if conn['from'] == loc1 and conn['to'] == loc2:
                self._distance_cache[cache_key] = conn['distance']
                return conn['distance']
                
        # Not directly connected
        return np.inf
    
    def get_all_rooms(self) -> List[Room]:
        """Get list of all rooms"""
        return list(self.rooms.values())
    
    def get_rooms_by_floor(self, floor: int) -> List[Room]:
        """Get all rooms on a specific floor"""
        return [room for room in self.rooms.values() if room.floor == floor]
    
    def get_high_priority_rooms(self) -> List[Room]:
        """Get all high priority rooms"""
        return [room for room in self.rooms.values() if room.priority >= 2]
    
    def reset_clearance(self):
        """Reset clearance status of all rooms"""
        for room in self.rooms.values():
            room.cleared = False
            room.cleared_at = None
            room.cleared_by = None
            
    @classmethod
    def from_json(cls, filepath: str) -> 'Building':
        """
        Load building from JSON file
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Building instance
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        building_data = data.get('building', data)
        
        building = cls(
            name=building_data.get('name', 'Building'),
            n_floors=building_data.get('floors', 1)
        )
        
        # Add rooms
        for room_data in building_data.get('rooms', []):
            pos = room_data.get('position', {})
            if isinstance(pos, dict):
                position = (pos['x'], pos['y'])
            else:
                position = tuple(pos)
                
            room = Room(
                room_id=room_data['id'],
                area=room_data.get('area', 16),
                position=position,
                floor=room_data.get('floor', 1),
                room_type=room_data.get('type', 'office'),
                occupancy=room_data.get('occupancy', 0),
                priority=room_data.get('priority', 1),
                check_complexity=room_data.get('check_complexity', 1.0)
            )
            building.add_room(room)
            
        # Add exits
        for exit_data in building_data.get('exits', []):
            pos = exit_data.get('position', {})
            if isinstance(pos, dict):
                position = (pos['x'], pos['y'])
            else:
                position = tuple(pos)
            building.add_exit(
                exit_data['id'],
                position,
                exit_data.get('floor', 1)
            )
            
        # Add corridors
        for corridor_data in building_data.get('corridors', []):
            start = corridor_data.get('start', {})
            end = corridor_data.get('end', {})
            if isinstance(start, dict):
                start = (start['x'], start['y'])
                end = (end['x'], end['y'])
            building.add_corridor(
                corridor_data['id'],
                start, end,
                corridor_data.get('floor', 1),
                corridor_data.get('width', 2.0)
            )
            
        # Add stairs
        for stair_data in building_data.get('stairs', []):
            pos = stair_data.get('position', {})
            if isinstance(pos, dict):
                position = (pos['x'], pos['y'])
            else:
                position = tuple(pos)
            building.add_stairs(
                stair_data['id'],
                position,
                stair_data['connects']
            )
            
        # Add connections
        for conn_data in building_data.get('connections', []):
            building.add_connection(
                conn_data['from'],
                conn_data['to'],
                conn_data['distance']
            )
            
        return building
    
    @classmethod
    def create_simple(cls, n_rooms: int = 6, layout: str = 'two_sided_corridor',
                     room_size: float = 16, corridor_length: float = 30) -> 'Building':
        """
        Create a simple building for testing
        
        Args:
            n_rooms: Number of rooms
            layout: Layout type ('linear', 'two_sided_corridor', 'grid')
            room_size: Room area in square meters
            corridor_length: Corridor length in meters
            
        Returns:
            Building instance
        """
        building = cls(name=f"Simple {layout.replace('_', ' ').title()}", n_floors=1)
        
        if layout == 'two_sided_corridor':
            # Create rooms on both sides of corridor
            rooms_per_side = n_rooms // 2
            spacing = corridor_length / (rooms_per_side + 1)
            
            # Left side rooms
            for i in range(rooms_per_side):
                y = spacing * (i + 1)
                room = Room(
                    room_id=f"R{i+1}",
                    area=room_size,
                    position=(5, y),
                    floor=1,
                    room_type='office',
                    priority=1
                )
                building.add_room(room)
                
            # Right side rooms
            for i in range(rooms_per_side):
                y = spacing * (i + 1)
                room = Room(
                    room_id=f"R{rooms_per_side + i + 1}",
                    area=room_size,
                    position=(25, y),
                    floor=1,
                    room_type='office',
                    priority=1
                )
                building.add_room(room)
                
            # Add corridor
            building.add_corridor('C_main', (15, 0), (15, corridor_length), floor=1)
            
            # Add exits at both ends
            building.add_exit('E1', (15, 0), floor=1)
            building.add_exit('E2', (15, corridor_length), floor=1)
            
            # Add connections
            for i, room in enumerate(building.rooms.values()):
                # Distance from corridor center to room
                distance = np.abs(room.position[0] - 15) + 2
                building.add_connection(room.id, 'C_main', distance)
                
            # Connect corridor to exits
            building.add_connection('C_main', 'E1', 0)
            building.add_connection('C_main', 'E2', 0)
            
        return building
    
    def to_dict(self) -> Dict:
        """Export building to dictionary"""
        return {
            'name': self.name,
            'floors': self.n_floors,
            'rooms': [
                {
                    'id': room.id,
                    'area': room.area,
                    'position': {'x': room.position[0], 'y': room.position[1]},
                    'floor': room.floor,
                    'type': room.type,
                    'occupancy': room.occupancy,
                    'priority': room.priority
                }
                for room in self.rooms.values()
            ],
            'exits': list(self.exits.values()),
            'corridors': list(self.corridors.values()),
            'stairs': list(self.stairs.values()),
            'connections': self.connections
        }
    
    def __repr__(self):
        return f"Building({self.name}, {self.n_floors} floors, {len(self.rooms)} rooms)"

