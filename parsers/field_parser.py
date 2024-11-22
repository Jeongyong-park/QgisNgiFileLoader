import logging

logger = logging.getLogger(__name__)


class FieldParser:
    @staticmethod
    def parse_value(value: str, field_type: str):
        if not value or value == '""':
            return None

        # if field type is string, remove whitespace and quotes
        if field_type == "STRING":
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1].strip()
            return value

        # if field type is numeric, check if it contains non-numeric characters
        if field_type == "NUMERIC":
            value = value.strip()
            # check if it contains non-numeric characters
            if any(c.isalpha() for c in value):
                raise ValueError(f"Failed to parse value '{value}' as NUMERIC")

            try:
                if "." in value:
                    return float(value)
                return int(value)
            except (ValueError, TypeError):
                raise ValueError(f"Failed to parse value '{value}' as NUMERIC")

        raise ValueError(f"Unsupported field type: {field_type}")
