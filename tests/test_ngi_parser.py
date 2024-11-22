import unittest
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parsers.ngi_parser import NGIParser
from parsers.types import GeometryType

class TestNGIParser(unittest.TestCase):
    def setUp(self):
        self.parser = NGIParser()
        self.test_data_dir = Path(__file__).parent / "test_data"
        
    def test_parse_coordinates(self):
        test_lines = [
            "4",  # 점 개수
            "100.0 200.0",
            "200.0 300.0",
            "300.0 200.0",
            "100.0 200.0"
        ]
        coords, next_idx = self.parser.parse_coordinates(test_lines, 0)
        
        self.assertEqual(len(coords), 4)
        self.assertEqual(coords[0], [100.0, 200.0])
        self.assertEqual(next_idx, 5)
        
    def test_parse_geometry_type(self):
        test_lines = [
            "$GEOMETRIC_METADATA",
            "MASK(POLYGON,LINESTRING)"
        ]
        geom_type, next_idx = self.parser.parse_geometry_type(test_lines, 0)
        
        self.assertEqual(geom_type, GeometryType.MULTIPOLYGON)
        self.assertEqual(next_idx, 2)
        
        # 단일 지오메트리 타입 테스트
        test_cases = [
            ("POINT", GeometryType.POINT),
            ("LINESTRING", GeometryType.LINESTRING),
            ("POLYGON", GeometryType.POLYGON)
        ]
        
        for type_str, expected_type in test_cases:
            geom_type, _ = self.parser.parse_geometry_type([
                "$GEOMETRIC_METADATA",
                f"MASK({type_str})"
            ], 0)
            self.assertEqual(geom_type, expected_type)
        
    def test_parse_bounds(self):
        test_lines = [
            "BOUND(100.0, 200.0, 300.0, 400.0)"
        ]
        bounds, next_idx = self.parser.parse_bounds(test_lines, 0)
        
        self.assertEqual(bounds, [100.0, 200.0, 300.0, 400.0])
        self.assertEqual(next_idx, 1)
        
    def test_parse_geometry_type_invalid(self):
        invalid_inputs = [
            ["$GEOMETRIC_METADATA", "MASK(INVALID)"],
            ["$GEOMETRIC_METADATA", "MASK()"],
            ["$GEOMETRIC_METADATA", "INVALID"],
        ]
        
        for invalid_input in invalid_inputs:
            with self.assertRaises(ValueError):
                self.parser.parse_geometry_type(invalid_input, 0)