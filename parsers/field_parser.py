from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class FieldParser:
    @staticmethod
    def parse_value(value: str, field_type: str, encoding: str = 'cp949') -> Optional[Any]:
        """Parse field value according to its type"""
        if not value or value == '""':
            return None
            
        value = value.strip('"')
        
        try:
            if field_type.upper() == 'NUMERIC':
                return float(value) if '.' in value else int(value)
            elif field_type.upper() == 'STRING':
                try:
                    return value.encode(encoding).decode(encoding)
                except UnicodeError:
                    return value
            else:
                logger.warning(f"Unknown field type: {field_type}")
                return value
        except ValueError:
            logger.warning(f"Failed to parse value '{value}' as {field_type}")
            return value