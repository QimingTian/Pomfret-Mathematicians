#!/usr/bin/env python3
"""
Unit tests for basic scenario
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.models.building import Building, Room
from src.models.responder import Responder, ResponderTeam
from src.algorithms.greedy import GreedyOptimizer
from src.algorithms.simulator import Simulator


class TestBuilding(unittest.TestCase):
    """Test Building class"""
    
    def test_create_simple_building(self):
        """Test simple building creation"""
        building = Building.create_simple(n_rooms=6)
        self.assertEqual(len(building.rooms), 6)
        self.assertEqual(building.n_floors, 1)
        self.assertEqual(len(building.exits), 2)
        
    def test_room_creation(self):
        """Test room creation"""
        room = Room('R1', area=16, position=(5, 10))
        self.assertEqual(room.id, 'R1')
        self.assertEqual(room.area, 16)
        self.assertFalse(room.cleared)
        
    def test_check_time_calculation(self):
        """Test room check time calculation"""
        room = Room('R1', area=16, position=(5, 10))
        check_time = room.calculate_check_time(base_time=10, rate=1.0)
        expected = 10 + 1.0 * 16
        self.assertEqual(check_time, expected)


class TestResponder(unittest.TestCase):
    """Test Responder class"""
    
    def test_responder_creation(self):
        """Test responder creation"""
        responder = Responder(1, 'E1')
        self.assertEqual(responder.id, 1)
        self.assertEqual(responder.position, 'E1')
        self.assertEqual(responder.current_time, 0.0)
        
    def test_responder_team(self):
        """Test responder team creation"""
        team = ResponderTeam(2, ['E1', 'E2'])
        self.assertEqual(len(team), 2)
        self.assertEqual(team.responders[0].initial_position, 'E1')


class TestGreedyOptimizer(unittest.TestCase):
    """Test Greedy Optimizer"""
    
    def setUp(self):
        """Set up test building"""
        self.building = Building.create_simple(n_rooms=6)
        
    def test_greedy_nearest(self):
        """Test greedy nearest strategy"""
        optimizer = GreedyOptimizer(self.building, n_responders=2, strategy='nearest')
        assignment = optimizer.optimize()
        
        # Check that all rooms are assigned
        all_rooms = []
        for rooms in assignment.values():
            all_rooms.extend(rooms)
        self.assertEqual(len(all_rooms), 6)
        self.assertEqual(len(set(all_rooms)), 6)  # No duplicates
        
    def test_greedy_balanced(self):
        """Test greedy balanced strategy"""
        optimizer = GreedyOptimizer(self.building, n_responders=2, strategy='balanced')
        assignment = optimizer.optimize()
        
        # Check assignment
        self.assertEqual(len(assignment), 2)
        
        # Check that workload is somewhat balanced
        counts = [len(rooms) for rooms in assignment.values()]
        self.assertLessEqual(abs(counts[0] - counts[1]), 1)


class TestSimulator(unittest.TestCase):
    """Test Simulator"""
    
    def setUp(self):
        """Set up test scenario"""
        self.building = Building.create_simple(n_rooms=6)
        self.optimizer = GreedyOptimizer(self.building, n_responders=2)
        self.assignment = self.optimizer.optimize()
        self.team = self.optimizer.get_team()
        
    def test_simulation_run(self):
        """Test simulation execution"""
        results = Simulator.run_quick(self.building, self.team, self.assignment)
        
        # Check results structure
        self.assertIn('total_time', results)
        self.assertIn('success', results)
        self.assertIn('responder_paths', results)
        self.assertIn('metrics', results)
        
        # Check that all rooms were cleared
        self.assertTrue(results['success'])
        
        # Check that total_time is positive
        self.assertGreater(results['total_time'], 0)
        
    def test_all_rooms_cleared(self):
        """Test that all rooms are cleared after simulation"""
        Simulator.run_quick(self.building, self.team, self.assignment)
        
        for room in self.building.rooms.values():
            self.assertTrue(room.cleared)
            self.assertIsNotNone(room.cleared_at)
            self.assertIsNotNone(room.cleared_by)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_full_workflow(self):
        """Test complete workflow from building to results"""
        # Create building
        building = Building.create_simple(n_rooms=6)
        
        # Optimize
        optimizer = GreedyOptimizer(building, n_responders=2, strategy='balanced')
        assignment = optimizer.optimize()
        
        # Simulate
        team = optimizer.get_team()
        results = Simulator.run_quick(building, team, assignment)
        
        # Verify results
        self.assertTrue(results['success'])
        self.assertEqual(len(results['responder_paths']), 2)
        self.assertGreater(results['total_time'], 0)
        self.assertLessEqual(results['total_time'], 600)  # Should be under 10 minutes


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    print("="*60)
    print("RUNNING UNIT TESTS")
    print("="*60 + "\n")
    
    run_tests()
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)

