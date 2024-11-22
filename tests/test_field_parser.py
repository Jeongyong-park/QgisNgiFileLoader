import unittest
import os
import sys
from parsers.field_parser import FieldParser

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestFieldParser(unittest.TestCase):
    def test_parse_value(self):
        # numeric test
        self.assertEqual(FieldParser.parse_value("123", "NUMERIC"), 123)
        self.assertEqual(FieldParser.parse_value("123.45", "NUMERIC"), 123.45)
        self.assertEqual(FieldParser.parse_value("-123", "NUMERIC"), -123)
        self.assertEqual(FieldParser.parse_value("-123.45", "NUMERIC"), -123.45)

        # string test
        self.assertEqual(FieldParser.parse_value('"test"', "STRING"), "test")
        self.assertEqual(FieldParser.parse_value("test", "STRING"), "test")
        self.assertEqual(FieldParser.parse_value("123", "STRING"), "123")

        # korean test
        self.assertEqual(FieldParser.parse_value("테스트", "STRING"), "테스트")
        self.assertEqual(FieldParser.parse_value('"테스트"', "STRING"), "테스트")

        # empty value test
        self.assertIsNone(FieldParser.parse_value('""', "STRING"))
        self.assertIsNone(FieldParser.parse_value("", "STRING"))
        self.assertIsNone(FieldParser.parse_value("", "NUMERIC"))

        # exception test
        with self.assertRaises(ValueError):
            FieldParser.parse_value("abc", "NUMERIC")
        with self.assertRaises(ValueError):
            FieldParser.parse_value("123.45.67", "NUMERIC")

    def test_parse_value_edge_cases(self):
        # boundary value test
        self.assertEqual(FieldParser.parse_value("0", "NUMERIC"), 0)
        self.assertEqual(FieldParser.parse_value("9999999999", "NUMERIC"), 9999999999)

        # special character test
        self.assertEqual(FieldParser.parse_value("test!@#$", "STRING"), "test!@#$")

        # whitespace test
        self.assertEqual(FieldParser.parse_value("  test  ", "STRING"), "test")
