from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging
from pathlib import Path
from .types import LayerDefinition, GeoFeature


class BaseParser(ABC):
    def __init__(self, encoding: str = "cp949") -> None:
        self.encoding = encoding
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def parse_file(self, file_path: str) -> Dict[str, Dict[str, Any]]:
        """Parse file and return layer data"""
        pass

    @abstractmethod
    def get_layer_definition(self, layer_name: str) -> LayerDefinition:
        """Get layer metadata including field definitions"""
        pass

    def _read_file_lines(self, file_path: Path) -> List[str]:
        """safely read file"""
        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                return [line.strip() for line in f]
        except UnicodeDecodeError:
            self.logger.error(f"file encoding error: {file_path}")
            raise
        except Exception as e:
            self.logger.error(f"file read error: {file_path}, {str(e)}")
            raise

    def _validate_feature(self, feature: GeoFeature) -> bool:
        """feature data validation"""
        if not isinstance(feature, dict):
            return False
        if "type" not in feature or feature["type"] != "Feature":
            return False
        if "geometry" not in feature or "properties" not in feature:
            return False
        return True
