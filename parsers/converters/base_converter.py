from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path
import logging

class BaseConverter(ABC):
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def convert(self, data: Dict[str, Dict[str, Any]], output_path: str) -> None:
        """Convert data to target format"""
        pass

    def _ensure_output_dir(self, output_path: Path) -> None:
        """Ensure output directory exists"""
        output_path.parent.mkdir(parents=True, exist_ok=True)