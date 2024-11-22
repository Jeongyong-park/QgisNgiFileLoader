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
                                            
                        
                        parsed_data[current_layer][current_record] = {
                            "type": "Polygon",
                            "coordinates": [coords]
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
                    elif line == 'NETWORKCHAIN' or line == 'NETWORK CHAIN':
                        i += 1
                        coords, i = self.parse_coordinates(lines, i)
                        parsed_data[current_layer][current_record] = {
                            "type": "MultiLineString",
                            "coordinates": [coords]
                        }
                    elif line == 'MULTIPOINT':
                        i += 1
                        coords, i = self.parse_coordinates(lines, i)
                        parsed_data[current_layer][current_record] = {
                            "type": "MultiPoint",
                            "coordinates": coords
                        }
                    elif line == 'TEXT':
                        i += 1
                        line = lines[i].strip()
                        try:
                            x, y = map(float, line.split())
                            parsed_data[current_layer][current_record] = {
                                "type": "Point",
                                "coordinates": [x, y],
                                "properties": {"text_type": True}
                            }
                        except ValueError:
                            self.logger.warning(f"Failed to parse text point: {line}")
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

    def parse_geometry_type(self, lines: List[str], start_idx: int) -> Tuple[GeometryType, int]:
        if len(lines) <= start_idx + 1:
            raise ValueError("Not enough lines to parse geometry type")
        
        line = lines[start_idx + 1]
        if not line.startswith("MASK(") or not line.endswith(")"):
            raise ValueError(f"Invalid geometry type format: {line}")
        
        type_str = line[5:-1]  # Remove MASK( and )
        types = [t.strip().upper() for t in type_str.split(",")]
        
        if not types or not types[0]:
            raise ValueError("Empty geometry type")
        
        # handle complex types
        if len(types) > 1:
            if "POLYGON" in types:
                return GeometryType.MULTIPOLYGON, start_idx + 2
            elif "LINESTRING" in types:
                return GeometryType.MULTILINESTRING, start_idx + 2
            elif "POINT" in types:
                return GeometryType.MULTIPOINT, start_idx + 2
        
        # handle single type
        type_mapping = {
            "POINT": GeometryType.POINT,
            "LINESTRING": GeometryType.LINESTRING,
            "POLYGON": GeometryType.POLYGON,
            "MULTIPOINT": GeometryType.MULTIPOINT,
            "MULTILINESTRING": GeometryType.MULTILINESTRING,
            "MULTIPOLYGON": GeometryType.MULTIPOLYGON,
            "TEXT": GeometryType.TEXT,
            "NETWORKCHAIN": GeometryType.NETWORKCHAIN
        }
        
        if types[0] not in type_mapping:
            raise ValueError(f"Invalid geometry type: {types[0]}")
        
        return type_mapping[types[0]], start_idx + 2

    def parse_bounds(self, lines: List[str], start_idx: int) -> Tuple[List[float], int]:
        """Parse bounding box coordinates"""
        i = start_idx
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('BOUND('):
                # BOUND(150609.210000, 203279.010000, 152265.620000, 205171.560000)
                coords_str = line[6:-1]  # remove BOUND( and )
                try:
                    x1, y1, x2, y2 = map(float, coords_str.split(','))
                    return [x1, y1, x2, y2], i + 1
                except ValueError:
                    self.logger.warning(f"Failed to parse bounds: {line}")
                    return [], i + 1
            i += 1
        return [], start_idx