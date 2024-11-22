from pathlib import Path
from typing import Dict, Any, List
import logging
import re
from .base_parser import BaseParser
from .types import LayerDefinition, GeometryType  # types module import added

logger = logging.getLogger(__name__)

class NDAParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self._layer_definitions: Dict[str, LayerDefinition] = {}

    def get_layer_definition(self, layer_name: str) -> LayerDefinition:
        """Returns layer definition"""
        if layer_name not in self._layer_definitions:
            return LayerDefinition(
                name=layer_name,
                fields=[],  # NDA file has no predefined fields
                geometry_type=GeometryType.UNKNOWN
            )
        return self._layer_definitions[layer_name]

    def _parse_csv_line(self, line: str) -> List[str]:
        """Parse CSV line handling quoted values"""
        values = []
        current_value = ''
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                values.append(current_value.strip())
                current_value = ''
            else:
                current_value += char
                
        # Append the last value
        values.append(current_value.strip())
        return values

    def parse_file(self, file_path: str) -> Dict[str, Dict[str, Any]]:
        """Parse NDA file and group by layer name"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        parsed_data: Dict[str, Dict[str, Any]] = {}
        current_layer = None
        layer_fields: Dict[str, List[str]] = {}  # Store field information by layer
        layer_field_types: Dict[str, List[str]] = {}  # Store field types by layer
        in_data_section = False
        total_records = 0
        
        try:
            with open(file_path, 'r', encoding=self.encoding) as file:
                lines = file.readlines()
                i = 0
                
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Parse layer information
                    if line == '<LAYER_START>':
                        i += 1
                        while i < len(lines):
                            line = lines[i].strip()
                            if line == '$LAYER_NAME':
                                i += 1
                                current_layer = lines[i].strip().strip('"')
                                logger.info(f"Processing layer: {current_layer}")
                                if current_layer not in parsed_data:
                                    parsed_data[current_layer] = {}
                                    layer_fields[current_layer] = []
                                    layer_field_types[current_layer] = []
                                break
                            i += 1
                    
                    # Parse field definitions
                    elif line == '$ASPATIAL_FIELD_DEF' and current_layer:
                        logger.info(f"\n=== Start field definitions of layer {current_layer} ===")
                        i += 1
                        while i < len(lines):
                            line = lines[i].strip()
                            if line == '$END':
                                break
                            if line.startswith('ATTRIB'):
                                try:
                                    field_def = line[7:-1]  # Remove ATTRIB( and )
                                    parts = field_def.split(',')
                                    field_name = parts[0].strip('"')
                                    field_type = parts[1].strip()
                                    
                                    layer_fields[current_layer].append(field_name)
                                    layer_field_types[current_layer].append(field_type)
                                    logger.info(f"Field added: {field_name} ({field_type})")
                                except Exception as e:
                                    logger.error(f"Failed to parse field definition: {line}, {str(e)}")
                            i += 1
                        logger.info(f"=== Layer {current_layer} field definitions completed (Total: {len(layer_fields[current_layer])}) ===")
                    
                    # Parse data records
                    elif line == '<DATA>':
                        in_data_section = True
                        logger.debug(f"Data section started: layer {current_layer}")
                        i += 1
                        continue
                    
                    elif in_data_section and line.startswith('$RECORD') and current_layer:
                        record_id = line.split()[1].strip()
                        if i + 1 >= len(lines):
                            i += 1
                            continue
                        
                        data_line = lines[i + 1].strip()
                        values = self._parse_csv_line(data_line)
                        
                        field_names = layer_fields[current_layer]
                        field_types = layer_field_types[current_layer]
                        
                        if len(values) != len(field_names):
                            logger.warning(f"Layer {current_layer}, record {record_id}: Field count mismatch (expected: {len(field_names)}, actual: {len(values)})")
                            i += 2
                            continue
                        
                        properties = {}
                        for field_name, field_type, value in zip(field_names, field_types, values):
                            if value and value.strip('"'):  # Exclude empty values or only quotes
                                parsed_value = self._parse_field_value(value, field_type)
                                if parsed_value is not None:
                                    properties[field_name] = parsed_value
                        
                        if properties:  # Save only if there is at least one property
                            parsed_data[current_layer][record_id] = properties
                            total_records += 1
                            
                            if total_records == 1:
                                logger.info(f"\n=== First record of layer {current_layer} ===")
                                for field_name, value in properties.items():
                                    logger.info(f"- {field_name}: {value}")
                                logger.info("============================")
                        
                        i += 2
                        continue
                    
                    elif line == '<END>':
                        if in_data_section and current_layer:
                            logger.info(f"Layer {current_layer} data section ended: {len(parsed_data[current_layer])} records")
                        in_data_section = False
                    
                    i += 1
                
                logger.info(f"Total {total_records} records parsed from {len(parsed_data)} layers")
                
        except Exception as e:
            logger.error(f"Error occurred during parsing NDA file: {e}")
            raise
        
        return parsed_data

    def _parse_field_value(self, value: str, field_type: str) -> Any:
        """Parse field value according to its type"""
        if not value or value == '""':
            return None
        
        # Handle values enclosed in quotes
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        
        try:
            if field_type.upper() == 'NUMERIC':
                if '.' in value:
                    return float(value)
                return int(value)
            elif field_type.upper() == 'STRING':
                # Handle Korean string
                try:
                    return value.encode('cp949').decode('cp949')
                except UnicodeError:
                    return value
            else:
                logger.warning(f"Unknown field type: {field_type}")
                return value
        except ValueError:
            logger.warning(f"Failed to parse value '{value}' as {field_type}")
            return value