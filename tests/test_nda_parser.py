import unittest
import os
import sys
from parsers.nda_parser import NDAParser

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestNDAParser(unittest.TestCase):
    def setUp(self):
        self.parser = NDAParser()

    def test_parse_csv_line(self):
        test_line = '"field1","field2,with,comma","field3"'
        values = self.parser._parse_csv_line(test_line)

        self.assertEqual(len(values), 3)
        self.assertEqual(values[0], "field1")
        self.assertEqual(values[1], "field2,with,comma")
        self.assertEqual(values[2], "field3")

    def test_parse_field_value(self):
        # 숫자형 테스트
        self.assertEqual(self.parser._parse_field_value("123", "NUMERIC"), 123)
        self.assertEqual(self.parser._parse_field_value("123.45", "NUMERIC"), 123.45)
        self.assertEqual(self.parser._parse_field_value("-123.45", "NUMERIC"), -123.45)

        # 문자열 테스트
        self.assertEqual(self.parser._parse_field_value('"test"', "STRING"), "test")
        self.assertEqual(self.parser._parse_field_value("test", "STRING"), "test")

        # 빈 값 테스트
        self.assertIsNone(self.parser._parse_field_value('""', "STRING"))
        self.assertIsNone(self.parser._parse_field_value("", "STRING"))
        self.assertIsNone(self.parser._parse_field_value("", "NUMERIC"))
