import os
import sys

# check if test is running
is_test = 'unittest' in sys.modules

if not is_test:
    from .converters.geopackage_converter import GeoPackageConverter
    
# remaining imports
from .ngi_parser import NGIParser
from .nda_parser import NDAParser
from .field_parser import FieldParser

__all__ = ['NGIParser', 'NDAParser', 'GeoJSONConverter', 'GeoPackageConverter']