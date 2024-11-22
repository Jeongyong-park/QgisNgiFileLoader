from pathlib import Path
from typing import Dict, Any, List, Tuple
import logging
from math import atan2, pi
from .base_parser import BaseParser
from .types import LayerDefinition, GeometryType, FieldDefinition

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('debug.log'),
            logging.StreamHandler()
        ]
    )

class NGIParser(BaseParser):
    def get_ring_direction(self, coords: List[List[float]]) -> int:
        """
        Calculate ring direction using winding number
        Returns:
         1 for counterclockwise
        -1 for clockwise
         0 for invalid/degenerate cases
        """
        if len(coords) < 3:
            return 0
            
        # Remove duplicate end point
        points = coords[:-1] if coords[0] == coords[-1] else coords
        
        # Calculate winding number
        angle_sum = 0.0
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            angle = atan2(p2[1] - p1[1], p2[0] - p1[0])
            angle_sum += angle
            
        # Normalize to [-2π, 2π]
        angle_sum = angle_sum % (2 * pi)
        
        # Determine direction
        if abs(angle_sum) < 0.1:  # Allow for numerical errors
            return 0
        return 1 if angle_sum > 0 else -1

    def ensure_ring_direction(self, coords: List[List[float]], force_ccw: bool = True) -> List[List[float]]:
        """
        Ensure ring follows right-hand rule
        force_ccw: True for outer rings (CCW), False for inner rings (CW)
        """
        if len(coords) < 3:
            return coords
            
        # Work with a copy
        ring = [list(p) for p in coords]
        
        # Get current direction
        direction = self.get_ring_direction(ring)
        if direction == 0:
            logger.warning("Invalid or degenerate ring detected")
            return ring
            
        # Check if reversal is needed
        needs_reversal = (direction < 0) if force_ccw else (direction > 0)
        
        if needs_reversal:
            logger.debug(f"Reversing ring direction (CCW={force_ccw})")
            ring = ring[:-1] if ring[0] == ring[-1] else ring
            ring.reverse()
            
        # Ensure ring is closed
        if ring[0] != ring[-1]:
            ring.append(list(ring[0]))
            
        return ring

    def parse_coordinates(self, lines: List[str], start_idx: int) -> Tuple[List[List[float]], int]:
        """Parse coordinate data from lines"""
        coordinates = []
        try:
            num_points = int(lines[start_idx].strip())
            
            for i in range(num_points):
                if start_idx + 1 + i >= len(lines):
                    break
                line = lines[start_idx + 1 + i].strip()
                if not line or line.startswith('$') or line in ['POLYGON', 'LINESTRING', 'POINT']:
                    break
                try:
                    x, y = map(float, line.split())
                    coordinates.append([x, y])
                except ValueError:
                    logger.warning(f"Failed to parse coordinates: {line}")
                    continue
            
            return coordinates, start_idx + num_points + 1
            
        except ValueError as e:
            logger.error(f"Failed to parse number of points: {lines[start_idx]}, {e}")
            return [], start_idx + 1

    def parse_file(self, file_path: str) -> Dict[str, Dict[str, Any]]:
        """Parse NGI file and group by layer name"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        parsed_data: Dict[str, Dict[str, Any]] = {}  # layer_name -> {record_id -> geometry}
        current_record = None
        current_layer = None
        
        with open(file_path, 'r', encoding=self.encoding) as file:
            lines = file.readlines()
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if not line:
                    i += 1
                    continue
                
                # Parse layer name
                if line == '$LAYER_NAME':
                    i += 1
                    if i < len(lines):
                        current_layer = self.parse_value(lines[i].strip())
                        if current_layer not in parsed_data:
                            parsed_data[current_layer] = {}
                        logger.debug(f"Processing layer: {current_layer}")
                
                if line.startswith('$RECORD'):
                    current_record = line.split()[1]
                    i += 1
                    continue
                
                if current_record and current_layer:
                    if line == 'POLYGON':
                        i += 1  # Move to NUMPARTS 1 line
                        if lines[i].strip() == 'NUMPARTS 1':
                            i += 1  # Move to coordinate count line
                        coords, i = self.parse_coordinates(lines, i)
                        
                        if len(coords) < 4:
                            logger.warning(f"Layer {current_layer}, Record {current_record}: Polygon has less than 4 coordinates")
                            i += 1
                            continue
                        
                        fixed_coords = self.ensure_ring_direction(coords, force_ccw=True)
                        
                        if self.get_ring_direction(fixed_coords) <= 0:
                            logger.error(f"Layer {current_layer}, Record {current_record}: Failed to ensure CCW direction")
                            i += 1
                            continue
                        
                        parsed_data[current_layer][current_record] = {
                            "type": "Polygon",
                            "coordinates": [fixed_coords]
                        }
                        
                    elif line == 'LINESTRING':
                        i += 1
                        coords, i = self.parse_coordinates(lines, i)
                        parsed_data[current_layer][current_record] = {
                            "type": "LineString",
                            "coordinates": coords
                        }
                    elif line == 'POINT':
                        i += 1
                        line = lines[i].strip()
                        x, y = map(float, line.split())
                        parsed_data[current_layer][current_record] = {
                            "type": "Point",
                            "coordinates": [x, y]
                        }
                        i += 1
                i += 1
                
        return parsed_data

    def get_layer_definition(self, layer_name: str) -> LayerDefinition:
        """Returns layer definition"""
        geometry_types = {
            "POINT": GeometryType.POINT,
            "LINESTRING": GeometryType.LINESTRING,
            "POLYGON": GeometryType.POLYGON
        }
        
        # default field definition
        base_fields: List[FieldDefinition] = [
            {
                "name": "record_id",
                "type": "STRING",
                "width": 50,
                "precision": 0,
                "nullable": False
            }
        ]
        
        if layer_name not in geometry_types:
            return LayerDefinition(
                name=layer_name,
                fields=base_fields,
                geometry_type=GeometryType.UNKNOWN
            )
        
        return LayerDefinition(
            name=layer_name,
            fields=base_fields,
            geometry_type=geometry_types[layer_name]
        )

    def parse_value(self, value: str) -> str:
        """Parse and return string value"""
        return value.strip().strip('"')  # remove double quotation and space