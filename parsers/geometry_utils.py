from typing import List, Tuple
from math import atan2, pi
import logging

logger = logging.getLogger(__name__)

class GeometryUtils:
    @staticmethod
    def get_ring_direction(coords: List[List[float]]) -> int:
        """Calculate ring direction"""
        if len(coords) < 3:
            return 0
            
        points = coords[:-1] if coords[0] == coords[-1] else coords
        angle_sum = sum(
            atan2(points[(i + 1) % len(points)][1] - p1[1],
                  points[(i + 1) % len(points)][0] - p1[0])
            for i, p1 in enumerate(points)
        )
        
        angle_sum = angle_sum % (2 * pi)
        return 1 if abs(angle_sum) > 0.1 and angle_sum > 0 else -1 if abs(angle_sum) > 0.1 else 0

    @staticmethod
    def ensure_ring_direction(coords: List[List[float]], force_ccw: bool = True) -> List[List[float]]:
        """Ensure ring follows right-hand rule"""
        if len(coords) < 3:
            return coords
            
        ring = [list(p) for p in coords]
        direction = GeometryUtils.get_ring_direction(ring)
        
        if direction == 0:
            logger.warning("Invalid or degenerate ring detected")
            return ring
            
        if (direction < 0) == force_ccw:
            ring = ring[:-1] if ring[0] == ring[-1] else ring
            ring.reverse()
            
        if ring[0] != ring[-1]:
            ring.append(list(ring[0]))
            
        return ring