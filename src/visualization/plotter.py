"""
Visualization tools for building sweep results
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import Dict, Optional
import os


class Plotter:
    """Visualization tools for sweep results"""
    
    def __init__(self, building, results: Dict):
        """
        Initialize plotter
        
        Args:
            building: Building instance
            results: Simulation results dictionary
        """
        self.building = building
        self.results = results
        
        # Color palette
        self.colors = plt.cm.Set3(np.linspace(0, 1, 12))
        
    def plot_paths(self, save_path: Optional[str] = None, show: bool = True):
        """
        Plot building layout with responder paths
        
        Args:
            save_path: Path to save figure (optional)
            show: Whether to display the plot
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw rooms
        for room_id, room in self.building.rooms.items():
            x, y = room.position
            # Assume rooms are 4x4m squares centered at position
            rect = patches.Rectangle(
                (x-2, y-2), 4, 4,
                linewidth=2,
                edgecolor='black',
                facecolor='lightgray',
                alpha=0.5
            )
            ax.add_patch(rect)
            ax.text(x, y, room_id, ha='center', va='center', fontsize=10, fontweight='bold')
            
        # Draw exits
        for exit_id, exit_data in self.building.exits.items():
            x, y = exit_data['position']
            ax.plot(x, y, 'gs', markersize=15, label=exit_id if exit_id == 'E1' else '')
            ax.text(x, y-2, exit_id, ha='center', va='top', fontsize=10, fontweight='bold')
            
        # Draw responder paths
        for i, path_data in enumerate(self.results['responder_paths']):
            responder_id = path_data['responder_id']
            path = path_data['path']
            
            # Get positions
            positions = []
            for loc_id in path:
                if loc_id in self.building.rooms:
                    positions.append(self.building.rooms[loc_id].position)
                elif loc_id in self.building.exits:
                    positions.append(self.building.exits[loc_id]['position'])
                elif loc_id in self.building.corridors:
                    corridor = self.building.corridors[loc_id]
                    start = np.array(corridor['start'])
                    end = np.array(corridor['end'])
                    positions.append(tuple((start + end) / 2))
                    
            if positions:
                xs, ys = zip(*positions)
                color = self.colors[i % len(self.colors)]
                ax.plot(xs, ys, 'o-', color=color, linewidth=2, markersize=8,
                       label=f'Responder {responder_id} ({path_data["total_time"]:.1f}s)',
                       alpha=0.7)
                
                # Add arrows to show direction
                for j in range(len(positions)-1):
                    dx = xs[j+1] - xs[j]
                    dy = ys[j+1] - ys[j]
                    if dx != 0 or dy != 0:
                        ax.arrow(xs[j], ys[j], dx*0.3, dy*0.3,
                               head_width=0.5, head_length=0.3,
                               fc=color, ec=color, alpha=0.5)
        
        ax.set_xlabel('X Position (m)', fontsize=12)
        ax.set_ylabel('Y Position (m)', fontsize=12)
        ax.set_title(f'Building Sweep Paths - Total Time: {self.results["total_time"]:.1f}s',
                    fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
        if show:
            plt.show()
        else:
            plt.close()
            
    def plot_gantt(self, save_path: Optional[str] = None, show: bool = True):
        """
        Plot Gantt chart of responder timelines
        
        Args:
            save_path: Path to save figure
            show: Whether to display the plot
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        
        for i, path_data in enumerate(self.results['responder_paths']):
            responder_id = path_data['responder_id']
            timeline = path_data['timeline']
            
            y_pos = i
            color = self.colors[i % len(self.colors)]
            
            for j in range(len(timeline) - 1):
                event = timeline[j]
                next_event = timeline[j + 1]
                
                start_time = event['time']
                duration = next_event['time'] - start_time
                
                if event['action'] == 'arrive' or event['action'] == 'start':
                    # Travel or wait (light color)
                    ax.barh(y_pos, duration, left=start_time,
                           height=0.6, color=color, alpha=0.3,
                           edgecolor='black', linewidth=0.5)
                elif event['action'] == 'check_complete':
                    # Should not happen (this is end of check)
                    pass
                    
                # Check if next action is check_complete
                if next_event['action'] == 'check_complete':
                    # Room check (darker color)
                    room_id = next_event['location']
                    ax.barh(y_pos, duration, left=start_time,
                           height=0.6, color=color, alpha=0.8,
                           edgecolor='black', linewidth=1)
                    # Add room label
                    ax.text(start_time + duration/2, y_pos, room_id,
                           ha='center', va='center', fontsize=8, fontweight='bold')
            
            ax.text(-2, y_pos, f'Responder {responder_id}',
                   ha='right', va='center', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Responder', fontsize=12)
        ax.set_title('Sweep Timeline (Gantt Chart)', fontsize=14, fontweight='bold')
        ax.set_yticks(range(len(self.results['responder_paths'])))
        ax.set_yticklabels([f"R{i+1}" for i in range(len(self.results['responder_paths']))])
        ax.grid(True, axis='x', alpha=0.3)
        ax.set_xlim(0, self.results['total_time'] * 1.05)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
        if show:
            plt.show()
        else:
            plt.close()
            
    def plot_metrics(self, save_path: Optional[str] = None, show: bool = True):
        """
        Plot performance metrics
        
        Args:
            save_path: Path to save figure
            show: Whether to display the plot
        """
        metrics = self.results['metrics']
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Time comparison
        ax = axes[0, 0]
        responder_times = [p['total_time'] for p in self.results['responder_paths']]
        responder_ids = [p['responder_id'] for p in self.results['responder_paths']]
        
        bars = ax.bar(responder_ids, responder_times, color=self.colors[:len(responder_ids)])
        ax.axhline(y=metrics['average_clearance_time'], color='r', linestyle='--',
                  label='Avg clearance time')
        ax.set_xlabel('Responder ID', fontsize=11)
        ax.set_ylabel('Time (seconds)', fontsize=11)
        ax.set_title('Responder Completion Times', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 2. Rooms checked
        ax = axes[0, 1]
        rooms_checked = [len(p['rooms_checked']) for p in self.results['responder_paths']]
        ax.bar(responder_ids, rooms_checked, color=self.colors[:len(responder_ids)])
        ax.set_xlabel('Responder ID', fontsize=11)
        ax.set_ylabel('Number of Rooms', fontsize=11)
        ax.set_title('Rooms Checked per Responder', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 3. Overall metrics
        ax = axes[1, 0]
        metric_names = ['Load\nBalance', 'Redundancy\nCoverage']
        metric_values = [
            metrics['load_balance'],
            metrics['redundancy_coverage']
        ]
        bars = ax.bar(metric_names, metric_values, color=['skyblue', 'lightcoral'])
        ax.set_ylabel('Score (0-1)', fontsize=11)
        ax.set_title('Performance Metrics', fontsize=12, fontweight='bold')
        ax.set_ylim(0, 1.1)
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontsize=10)
        
        # 4. Summary text
        ax = axes[1, 1]
        ax.axis('off')
        
        summary_text = f"""
        SUMMARY STATISTICS
        
        Total Sweep Time: {self.results['total_time']:.2f} s
        Average Clearance Time: {metrics['average_clearance_time']:.2f} s
        
        Building: {self.building.name}
        Floors: {self.building.n_floors}
        Rooms: {metrics['n_rooms']}
        Responders: {metrics['n_responders']}
        
        All Rooms Cleared: {'Yes' if metrics['all_rooms_cleared'] else 'No'}
        Load Balance: {metrics['load_balance']:.2%}
        Redundancy Coverage: {metrics['redundancy_coverage']:.2%}
        Total Distance: {metrics['total_distance_traveled']:.1f} m
        """
        
        ax.text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
               verticalalignment='center')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
        if show:
            plt.show()
        else:
            plt.close()
            
    def save_all(self, output_dir: str = 'results'):
        """
        Save all plots to directory
        
        Args:
            output_dir: Output directory path
        """
        os.makedirs(output_dir, exist_ok=True)
        
        self.plot_paths(
            save_path=os.path.join(output_dir, 'paths.png'),
            show=False
        )
        self.plot_gantt(
            save_path=os.path.join(output_dir, 'gantt.png'),
            show=False
        )
        self.plot_metrics(
            save_path=os.path.join(output_dir, 'metrics.png'),
            show=False
        )
        
        print(f"All plots saved to {output_dir}/")

