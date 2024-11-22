import os
import sys
from unittest.mock import MagicMock

# Create detailed mock objects
mock_gdal = MagicMock()
mock_ogr = MagicMock()
mock_osr = MagicMock()
mock_gdalconst = MagicMock()

# Mock GDAL specific attributes and methods
mock_ogr.wkbPolygon = 3
mock_ogr.wkbMultiPolygon = 6
mock_ogr.wkbLineString = 2
mock_ogr.wkbPoint = 1
mock_ogr.wkbGeometryCollection = 7

mock_ogr.CreateGeometryFromWkt = MagicMock()
mock_ogr.GetDriverByName = MagicMock()

# Mock OSR specific methods
mock_osr.SpatialReference = MagicMock()

# Register all mock modules
sys.modules['osgeo'] = MagicMock()
sys.modules['osgeo.gdal'] = mock_gdal
sys.modules['osgeo.ogr'] = mock_ogr
sys.modules['osgeo.osr'] = mock_osr
sys.modules['osgeo.gdalconst'] = mock_gdalconst
sys.modules['_gdal'] = MagicMock()

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)