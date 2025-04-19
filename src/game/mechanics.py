from enum import Enum, auto
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
import random
from datetime import datetime

class GameAction(Enum):
    CLAIM_HEX = auto()
    BUILD_IMPROVEMENT = auto()
    END_TURN = auto()

@dataclass
class GameEvent:
    action: GameAction
    player_id: int
    timestamp: float
    turn_number: int
    data: Dict  # Stores action-specific data

class ResourceType(Enum):
    FOOD = "food"
    WOOD = "wood"
    STONE = "stone"
    
class ImprovementType(Enum):
    FARM = "farm"  # Generates food
    LUMBER_CAMP = "lumber_camp"  # Generates wood
    QUARRY = "quarry"  # Generates stone
    SETTLEMENT = "settlement"  # Required to claim nearby hexes

@dataclass
class HexData:
    owner: Optional[int] = None  # Player ID who owns this hex
    improvement: Optional[ImprovementType] = None
    
    def can_build(self, improvement: ImprovementType) -> bool:
        return self.improvement is None

class Player:
    def __init__(self, player_id: int, color: Tuple[int, int, int]):
        self.id = player_id
        self.color = color
        self.resources = {
            ResourceType.FOOD: 10,
            ResourceType.WOOD: 10,
            ResourceType.STONE: 10
        }
        self.owned_hexes = set()  # Set of (col, row) tuples
        self.claims_this_turn = 0  # Track number of claims in current turn
        
    def can_afford(self, costs: Dict[ResourceType, int]) -> bool:
        return all(self.resources.get(res_type, 0) >= amount 
                  for res_type, amount in costs.items())
                  
    def spend_resources(self, costs: Dict[ResourceType, int]) -> bool:
        if not self.can_afford(costs):
            return False
        for res_type, amount in costs.items():
            self.resources[res_type] -= amount
        return True
        
    def add_resources(self, gains: Dict[ResourceType, int]):
        for res_type, amount in gains.items():
            self.resources[res_type] = self.resources.get(res_type, 0) + amount

class GameState:
    # Improvement costs
    IMPROVEMENT_COSTS = {
        ImprovementType.FARM: {ResourceType.WOOD: 2},
        ImprovementType.LUMBER_CAMP: {ResourceType.WOOD: 3},
        ImprovementType.QUARRY: {ResourceType.WOOD: 2, ResourceType.STONE: 1},
        ImprovementType.SETTLEMENT: {
            ResourceType.WOOD: 5,
            ResourceType.STONE: 3,
            ResourceType.FOOD: 2
        }
    }
    
    # Resource generation per improvement per turn
    RESOURCE_GENERATION = {
        ImprovementType.FARM: {ResourceType.FOOD: 2},
        ImprovementType.LUMBER_CAMP: {ResourceType.WOOD: 2},
        ImprovementType.QUARRY: {ResourceType.STONE: 1}
    }
    
    # Game rules
    MAX_CLAIMS_PER_TURN = 1
    
    def __init__(self):
        self.players = [
            Player(0, (200, 0, 0)),    # Red player
            Player(1, (0, 0, 200))     # Blue player
        ]
        self.current_player_idx = 0
        self.hex_data = {}  # Dict of (col, row) -> HexData
        self.turn_number = 1
        self.action_log: List[str] = []  # Human-readable log
        self.game_events: List[GameEvent] = []  # Machine-readable events
        
    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_idx]
    
    def get_hex_data(self, col: int, row: int) -> HexData:
        """Get or create hex data for a position"""
        key = (col, row)
        if key not in self.hex_data:
            self.hex_data[key] = HexData()
        return self.hex_data[key]
    
    def can_claim_hex(self, col: int, row: int) -> bool:
        """Check if current player can claim this hex"""
        # Check claims per turn limit
        if self.current_player.claims_this_turn >= self.MAX_CLAIMS_PER_TURN:
            return False
            
        hex_data = self.get_hex_data(col, row)
        if hex_data.owner is not None:
            return False
            
        # Must have a settlement within 2 hexes
        for dc in range(-2, 3):
            for dr in range(-2, 3):
                if abs(dc) + abs(dr) > 2:
                    continue
                neighbor_data = self.get_hex_data(col + dc, row + dr)
                if (neighbor_data.owner == self.current_player.id and 
                    neighbor_data.improvement == ImprovementType.SETTLEMENT):
                    return True
        return False
    
    def log_action(self, message: str, action: GameAction, data: Dict):
        """Log an action both for display and replay"""
        timestamp = datetime.now().timestamp()
        
        # Add human-readable log
        self.action_log.append(f"Turn {self.turn_number} - Player {self.current_player.id + 1}: {message}")
        
        # Add machine-readable event
        event = GameEvent(
            action=action,
            player_id=self.current_player.id,
            timestamp=timestamp,
            turn_number=self.turn_number,
            data=data
        )
        self.game_events.append(event)
        
    def get_recent_logs(self, count: int = 5) -> List[str]:
        """Get the most recent log messages"""
        return self.action_log[-count:]
    
    def claim_hex(self, col: int, row: int) -> bool:
        """Attempt to claim a hex for the current player"""
        if not self.can_claim_hex(col, row):
            self.log_action(
                f"Failed to claim hex at ({col}, {row})" + 
                (" - No claims remaining this turn" if self.current_player.claims_this_turn >= self.MAX_CLAIMS_PER_TURN else ""),
                GameAction.CLAIM_HEX,
                {"col": col, "row": row, "success": False}
            )
            return False
            
        hex_data = self.get_hex_data(col, row)
        hex_data.owner = self.current_player.id
        self.current_player.owned_hexes.add((col, row))
        self.current_player.claims_this_turn += 1
        
        self.log_action(
            f"Claimed hex at ({col}, {row})",
            GameAction.CLAIM_HEX,
            {"col": col, "row": row, "success": True}
        )
        return True
    
    def can_build(self, col: int, row: int, improvement: ImprovementType) -> bool:
        """Check if current player can build the improvement here"""
        hex_data = self.get_hex_data(col, row)
        return (hex_data.owner == self.current_player.id and
                hex_data.can_build(improvement) and
                self.current_player.can_afford(self.IMPROVEMENT_COSTS[improvement]))
    
    def build_improvement(self, col: int, row: int, improvement: ImprovementType) -> bool:
        """Attempt to build an improvement on the hex"""
        if not self.can_build(col, row, improvement):
            self.log_action(
                f"Failed to build {improvement.value} at ({col}, {row})",
                GameAction.BUILD_IMPROVEMENT,
                {"col": col, "row": row, "improvement": improvement.value, "success": False}
            )
            return False
            
        # Spend resources
        if not self.current_player.spend_resources(self.IMPROVEMENT_COSTS[improvement]):
            return False
            
        # Build improvement
        hex_data = self.get_hex_data(col, row)
        hex_data.improvement = improvement
        
        self.log_action(
            f"Built {improvement.value} at ({col}, {row})",
            GameAction.BUILD_IMPROVEMENT,
            {"col": col, "row": row, "improvement": improvement.value, "success": True}
        )
        return True
    
    def end_turn(self):
        """End current player's turn and process turn effects"""
        resources_gained = {}
        
        # Generate resources from improvements
        for col, row in self.current_player.owned_hexes:
            hex_data = self.get_hex_data(col, row)
            if hex_data.improvement in self.RESOURCE_GENERATION:
                gains = self.RESOURCE_GENERATION[hex_data.improvement]
                self.current_player.add_resources(gains)
                for res_type, amount in gains.items():
                    resources_gained[res_type.value] = resources_gained.get(res_type.value, 0) + amount
        
        self.log_action(
            f"Ended turn, gained resources: {', '.join(f'{amount} {res}' for res, amount in resources_gained.items())}",
            GameAction.END_TURN,
            {"resources_gained": resources_gained}
        )
        
        # Reset claims counter and switch to next player
        self.current_player.claims_this_turn = 0
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        if self.current_player_idx == 0:
            self.turn_number += 1 