# 模型输入输出设计

## 核心问题：输入是什么？

**简短回答**：输入是**结构化数据**，不是平面图图片！

### 为什么不用图片？
❌ 图片识别太复杂（需要CV技术）
❌ 不是这个数学建模比赛的重点
❌ 误差大，难以精确建模
✅ **我们用数据文件（JSON/CSV/Python字典）**

---

## 一、模型输入设计

### 输入方式对比

| 方式 | 优点 | 缺点 | 适用性 |
|------|------|------|--------|
| 📷 **平面图图片** | 直观、真实 | 需要图像处理、误差大 | ❌ 不推荐 |
| 📊 **结构化数据** | 精确、易处理、可重复 | 需要手动输入 | ✅ **推荐** |
| 🖊️ **CAD文件** | 专业、精确 | 解析复杂 | ⚠️ 可选扩展 |

### 推荐方案：分层数据输入

```
输入 = 建筑数据 + 响应者数据 + 场景参数
```

---

## 二、详细输入格式设计

### 2.1 建筑物数据（Building Data）

#### 方法A：基于坐标的表示（推荐用于可视化）

```python
building_data = {
    # 基本信息
    "name": "Single Floor Office Building",
    "floors": 1,
    
    # 房间定义（使用坐标）
    "rooms": [
        {
            "id": "R1",
            "floor": 1,
            "type": "office",
            "area": 16,  # m²
            "center": [5, 10],  # (x, y) 坐标
            "occupancy": 4,  # 典型人数
            "priority": 1,  # 优先级（1=普通，2=高，3=紧急）
            "check_complexity": 1.0  # 检查复杂度系数
        },
        {
            "id": "R2",
            "floor": 1,
            "type": "office",
            "area": 16,
            "center": [5, 20],
            "occupancy": 4,
            "priority": 1,
            "check_complexity": 1.0
        },
        # ... 更多房间
    ],
    
    # 走廊/连接点
    "corridors": [
        {
            "id": "C1",
            "floor": 1,
            "type": "corridor",
            "points": [[15, 5], [15, 25]],  # 走廊路径
            "width": 2  # m
        }
    ],
    
    # 出口
    "exits": [
        {
            "id": "E1",
            "position": [0, 15],
            "floor": 1
        },
        {
            "id": "E2",
            "position": [30, 15],
            "floor": 1
        }
    ],
    
    # 楼梯（多层建筑）
    "stairs": [
        {
            "id": "S1",
            "position": [15, 5],
            "connects": [1, 2]  # 连接楼层1和2
        }
    ]
}
```

#### 方法B：基于图的表示（推荐用于算法）

```python
building_graph = {
    # 节点列表
    "nodes": {
        "R1": {"type": "room", "area": 16, "floor": 1, "priority": 1},
        "R2": {"type": "room", "area": 16, "floor": 1, "priority": 1},
        "R3": {"type": "room", "area": 16, "floor": 1, "priority": 1},
        "R4": {"type": "room", "area": 16, "floor": 1, "priority": 1},
        "R5": {"type": "room", "area": 16, "floor": 1, "priority": 1},
        "R6": {"type": "room", "area": 16, "floor": 1, "priority": 1},
        "C1": {"type": "corridor", "length": 30},
        "E1": {"type": "exit"},
        "E2": {"type": "exit"}
    },
    
    # 邻接关系（边）
    "edges": [
        {"from": "E1", "to": "C1", "distance": 5},
        {"from": "C1", "to": "R1", "distance": 3},
        {"from": "C1", "to": "R2", "distance": 3},
        {"from": "C1", "to": "R3", "distance": 3},
        {"from": "C1", "to": "R4", "distance": 3},
        {"from": "C1", "to": "R5", "distance": 3},
        {"from": "C1", "to": "R6", "distance": 3},
        {"from": "C1", "to": "E2", "distance": 5}
    ]
}
```

#### 方法C：简化表格格式（最简单）

**rooms.csv**
```csv
room_id,floor,type,area,x,y,occupancy,priority
R1,1,office,16,5,10,4,1
R2,1,office,16,5,20,4,1
R3,1,office,16,5,30,4,1
R4,1,office,16,25,10,4,1
R5,1,office,16,25,20,4,1
R6,1,office,16,25,30,4,1
```

**connections.csv**
```csv
from,to,distance
R1,Corridor,3
R2,Corridor,3
R3,Corridor,3
R4,Corridor,3
R5,Corridor,3
R6,Corridor,3
Corridor,Exit1,15
Corridor,Exit2,15
```

---

### 2.2 响应者数据（Responder Data）

```python
responder_data = {
    "count": 2,  # 响应者数量
    
    # 响应者能力参数
    "capabilities": {
        "walk_speed": 1.5,  # m/s
        "stair_up_speed": 0.4,  # m/s
        "stair_down_speed": 0.7,  # m/s
        "check_rate": 1.0,  # s/m²
        "base_check_time": 10,  # s（进出房间的固定时间）
        "communication_delay": 2  # s
    },
    
    # 起始位置（可选，默认在出口）
    "initial_positions": [
        {"responder_id": 1, "position": "E1"},  # 出口1
        {"responder_id": 2, "position": "E2"}   # 出口2
    ]
}
```

---

### 2.3 场景参数（Scenario Parameters）

```python
scenario_data = {
    # 紧急情况类型
    "emergency_type": "fire",  # fire, gas_leak, earthquake
    
    # 火灾特定参数（如果是火灾）
    "fire_params": {
        "origin": "R3",  # 起火点
        "spread_rate": 1.0,  # 房间/分钟
        "smoke_speed": 3.0,  # m/s
        "visibility_decay": 0.1  # 能见度衰减率
    },
    
    # 环境约束
    "constraints": {
        "max_time": 600,  # 最大时间限制（秒）
        "hazard_threshold": 80,  # 危险度阈值（超过不可进入）
        "communication_reliability": 0.95  # 通信可靠性
    },
    
    # 策略选项
    "strategy_options": {
        "redundancy": False,  # 是否需要冗余检查
        "redundancy_high_priority": True,  # 高优先级房间冗余
        "dynamic_replan": False  # 是否动态重新规划
    }
}
```

---

## 三、模型输出设计

### 3.1 主要输出

```python
output = {
    # 核心结果
    "results": {
        "total_time": 127.5,  # 秒
        "all_rooms_cleared": True,
        "success": True
    },
    
    # 每个响应者的路径
    "responder_paths": [
        {
            "responder_id": 1,
            "path": ["E1", "C1", "R1", "C1", "R2", "C1", "R3", "C1", "E1"],
            "timeline": [
                {"time": 0, "action": "start", "location": "E1"},
                {"time": 5, "action": "arrive", "location": "C1"},
                {"time": 8, "action": "arrive", "location": "R1"},
                {"time": 34, "action": "check_complete", "location": "R1"},
                # ... 更多时间步
            ],
            "total_time": 127.5,
            "rooms_checked": ["R1", "R2", "R3"]
        },
        {
            "responder_id": 2,
            "path": ["E2", "C1", "R4", "C1", "R5", "C1", "R6", "C1", "E2"],
            "timeline": [
                # ... 类似结构
            ],
            "total_time": 120.0,
            "rooms_checked": ["R4", "R5", "R6"]
        }
    ],
    
    # 房间清理时间表
    "room_clearance": {
        "R1": {"cleared_at": 34, "cleared_by": 1},
        "R2": {"cleared_at": 68, "cleared_by": 1},
        "R3": {"cleared_at": 102, "cleared_by": 1},
        "R4": {"cleared_at": 30, "cleared_by": 2},
        "R5": {"cleared_at": 60, "cleared_by": 2},
        "R6": {"cleared_at": 90, "cleared_by": 2}
    },
    
    # 性能指标
    "metrics": {
        "average_clearance_time": 64.0,
        "load_balance": 0.95,  # 负载均衡度
        "redundancy_coverage": 0.0,  # 冗余覆盖率
        "total_distance_traveled": 120,  # m
        "efficiency": 0.85  # 效率分数
    }
}
```

### 3.2 可视化输出

```python
visualization_data = {
    # 用于动画的时间序列数据
    "animation_frames": [
        {
            "time": 0,
            "responders": [
                {"id": 1, "position": [0, 15]},
                {"id": 2, "position": [30, 15]}
            ],
            "cleared_rooms": [],
            "hazard_levels": {"R3": 10, "R2": 5, ...}
        },
        # ... 每秒一帧
    ],
    
    # 静态图表数据
    "plots": {
        "gantt_chart_data": {...},  # 甘特图数据
        "heatmap_data": {...},  # 热力图数据
        "path_overlay": {...}  # 路径叠加图
    }
}
```

---

## 四、完整的输入输出流程

### 流程图

```
[用户输入数据]
      ↓
[数据解析和验证]
      ↓
[建立内部图结构] ← 这是核心数据结构
      ↓
[运行优化算法]
      ↓
[仿真执行]
      ↓
[生成输出结果]
      ↓
[可视化展示]
```

### 代码接口设计

```python
class BuildingSweepModel:
    def __init__(self):
        self.building = None
        self.responders = None
        self.scenario = None
    
    # ========== 输入接口 ==========
    
    def load_building_from_json(self, filepath):
        """从JSON文件加载建筑数据"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.building = self._parse_building(data)
    
    def load_building_from_dict(self, building_dict):
        """从Python字典加载建筑数据"""
        self.building = self._parse_building(building_dict)
    
    def load_building_from_csv(self, rooms_file, connections_file):
        """从CSV文件加载建筑数据"""
        rooms_df = pd.read_csv(rooms_file)
        connections_df = pd.read_csv(connections_file)
        self.building = self._parse_building_from_tables(rooms_df, connections_df)
    
    def create_simple_building(self, n_rooms, layout='linear'):
        """快速创建简单建筑（用于测试）"""
        self.building = self._generate_simple_building(n_rooms, layout)
    
    def set_responders(self, count, capabilities=None):
        """设置响应者参数"""
        self.responders = self._initialize_responders(count, capabilities)
    
    def set_scenario(self, emergency_type='fire', params=None):
        """设置场景参数"""
        self.scenario = self._initialize_scenario(emergency_type, params)
    
    # ========== 核心算法 ==========
    
    def optimize(self, method='genetic_algorithm'):
        """运行优化算法
        
        Args:
            method: 'greedy', 'genetic_algorithm', 'integer_programming', 'a_star'
        
        Returns:
            optimal_assignment: 响应者和房间的最优分配
        """
        if method == 'greedy':
            return self._greedy_optimize()
        elif method == 'genetic_algorithm':
            return self._genetic_optimize()
        # ... 其他方法
    
    def simulate(self, assignment):
        """仿真执行扫描过程
        
        Args:
            assignment: 响应者分配方案
        
        Returns:
            simulation_results: 详细的执行结果
        """
        return self._run_simulation(assignment)
    
    # ========== 输出接口 ==========
    
    def get_results(self):
        """获取结果摘要"""
        return self.results
    
    def export_results_json(self, filepath):
        """导出结果为JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def export_results_csv(self, filepath):
        """导出结果为CSV"""
        df = self._results_to_dataframe()
        df.to_csv(filepath, index=False)
    
    def visualize(self, output_format='html'):
        """生成可视化
        
        Args:
            output_format: 'html', 'png', 'gif', 'interactive'
        """
        if output_format == 'html':
            return self._create_interactive_html()
        elif output_format == 'gif':
            return self._create_animation()
        # ...
    
    def plot_paths(self):
        """绘制路径图"""
        self._plot_building_with_paths()
    
    def plot_gantt(self):
        """绘制甘特图"""
        self._plot_timeline()
    
    def plot_metrics(self):
        """绘制性能指标"""
        self._plot_performance_metrics()
```

---

## 五、实际使用示例

### 示例1：基础场景（最简单的使用方式）

```python
from building_sweep_model import BuildingSweepModel

# 创建模型
model = BuildingSweepModel()

# 方式A：使用内置的简单建筑生成器
model.create_simple_building(
    n_rooms=6,
    layout='two_sided_corridor',
    room_size=16,
    corridor_length=30
)

# 设置响应者
model.set_responders(count=2)

# 运行优化
solution = model.optimize(method='greedy')

# 仿真
results = model.simulate(solution)

# 查看结果
print(f"Total time: {results['total_time']} seconds")
print(f"Responder 1 path: {results['responder_paths'][0]['path']}")
print(f"Responder 2 path: {results['responder_paths'][1]['path']}")

# 可视化
model.visualize(output_format='html')
model.plot_gantt()
```

### 示例2：从JSON文件加载

```python
# 创建模型
model = BuildingSweepModel()

# 从文件加载
model.load_building_from_json('buildings/scenario1.json')
model.load_responders_from_json('responders/standard_team.json')
model.load_scenario_from_json('scenarios/fire_alarm.json')

# 运行
solution = model.optimize(method='genetic_algorithm')
results = model.simulate(solution)

# 导出
model.export_results_json('results/scenario1_results.json')
model.export_results_csv('results/scenario1_results.csv')
```

### 示例3：手动创建数据

```python
# 手动定义建筑
building_data = {
    "rooms": [
        {"id": "R1", "area": 16, "position": [5, 10], "priority": 1},
        {"id": "R2", "area": 16, "position": [5, 20], "priority": 1},
        # ... 更多房间
    ],
    "connections": [
        {"from": "R1", "to": "Corridor", "distance": 3},
        # ... 更多连接
    ],
    "exits": [
        {"id": "E1", "position": [0, 15]},
        {"id": "E2", "position": [30, 15]}
    ]
}

model = BuildingSweepModel()
model.load_building_from_dict(building_data)
model.set_responders(count=2)

# 运行
solution = model.optimize()
results = model.simulate(solution)
```

---

## 六、数据文件示例

### scenario1_basic.json（完整示例）

```json
{
  "building": {
    "name": "Basic Office Building",
    "description": "Single floor, 6 rooms, 2 exits",
    "floors": 1,
    "rooms": [
      {
        "id": "R1",
        "floor": 1,
        "type": "office",
        "area": 16,
        "position": {"x": 5, "y": 5},
        "occupancy": 4,
        "priority": 1
      },
      {
        "id": "R2",
        "floor": 1,
        "type": "office",
        "area": 16,
        "position": {"x": 5, "y": 15},
        "occupancy": 4,
        "priority": 1
      },
      {
        "id": "R3",
        "floor": 1,
        "type": "office",
        "area": 16,
        "position": {"x": 5, "y": 25},
        "occupancy": 4,
        "priority": 1
      },
      {
        "id": "R4",
        "floor": 1,
        "type": "office",
        "area": 16,
        "position": {"x": 25, "y": 5},
        "occupancy": 4,
        "priority": 1
      },
      {
        "id": "R5",
        "floor": 1,
        "type": "office",
        "area": 16,
        "position": {"x": 25, "y": 15},
        "occupancy": 4,
        "priority": 1
      },
      {
        "id": "R6",
        "floor": 1,
        "type": "office",
        "area": 16,
        "position": {"x": 25, "y": 25},
        "occupancy": 4,
        "priority": 1
      }
    ],
    "corridors": [
      {
        "id": "C_main",
        "start": {"x": 0, "y": 15},
        "end": {"x": 30, "y": 15},
        "width": 2
      }
    ],
    "exits": [
      {
        "id": "E1",
        "position": {"x": 0, "y": 15},
        "floor": 1
      },
      {
        "id": "E2",
        "position": {"x": 30, "y": 15},
        "floor": 1
      }
    ],
    "connections": [
      {"from": "E1", "to": "C_main", "distance": 0},
      {"from": "C_main", "to": "R1", "distance": 10},
      {"from": "C_main", "to": "R2", "distance": 3},
      {"from": "C_main", "to": "R3", "distance": 10},
      {"from": "C_main", "to": "R4", "distance": 10},
      {"from": "C_main", "to": "R5", "distance": 3},
      {"from": "C_main", "to": "R6", "distance": 10},
      {"from": "C_main", "to": "E2", "distance": 0}
    ]
  },
  "responders": {
    "count": 2,
    "capabilities": {
      "walk_speed": 1.5,
      "check_rate": 1.0,
      "base_check_time": 10
    },
    "initial_positions": [
      {"responder_id": 1, "location": "E1"},
      {"responder_id": 2, "location": "E2"}
    ]
  },
  "scenario": {
    "emergency_type": "fire",
    "fire_origin": null,
    "max_time": 600,
    "strategy": {
      "redundancy": false,
      "dynamic_replan": false
    }
  }
}
```

---

## 七、推荐的实现方案

### 方案总结

| 场景 | 推荐输入方式 | 理由 |
|------|-------------|------|
| **快速测试** | Python代码直接创建 | 灵活、快速迭代 |
| **标准场景** | JSON文件 | 易读、易分享、可重复 |
| **批量测试** | CSV文件 | Excel编辑、批量生成 |
| **论文展示** | JSON + 配图 | 专业、清晰 |

### 我的建议

**对于这次比赛，我推荐：**

1. **基础场景**：用代码直接生成（simple_building函数）
   - 快速实现
   - 参数化调整

2. **扩展场景**：用JSON文件定义
   - 场景1：`scenario1_basic.json`（基础6房间）
   - 场景2：`scenario2_three_floors.json`（三层办公楼）
   - 场景3：`scenario3_daycare.json`（儿童日托中心）

3. **输出**：JSON + CSV + 可视化图表
   - JSON：完整数据
   - CSV：Excel分析
   - 图表：论文插图

---

## 八、总结

### ✅ 回答您的问题：

**Q: 模型的input是什么？平面图还是数据？**

**A: 输入是结构化数据（JSON/CSV/Python字典），不是图片！**

具体包括：
1. **建筑结构** - 房间列表、连接关系、出口位置
2. **响应者能力** - 数量、速度、检查时间
3. **场景参数** - 紧急类型、约束条件

### 📊 输入的三种格式：

1. **Python字典**（代码中直接创建）- 推荐用于快速测试
2. **JSON文件**（标准格式）- 推荐用于正式场景
3. **CSV文件**（表格）- 推荐用于批量数据

### 🎯 输出包括：

1. **数值结果**（总时间、路径等）
2. **时间线数据**（每个响应者的详细行动）
3. **可视化**（路径图、甘特图、动画）

---

## 下一步

我准备为您创建：
1. ✅ 完整的数据结构定义
2. ✅ 3个示例JSON文件（对应3个场景）
3. ✅ Python类接口
4. ✅ 简单建筑生成器（代码创建）

**这样回答清楚了吗？现在可以开始编写代码了吗？** 🚀

