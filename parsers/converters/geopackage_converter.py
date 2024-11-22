from osgeo import ogr, osr
import logging
from typing import Dict, Any, List
from .base_converter import BaseConverter
import os

logger = logging.getLogger(__name__)

class GeoPackageConverter(BaseConverter):
    def __init__(self) -> None:
        super().__init__()
        self.gpkg_driver = ogr.GetDriverByName("GPKG")
        if self.gpkg_driver is None:
            raise RuntimeError("Failed to load GPKG driver")

    def convert(self, data: Dict[str, Dict[str, Any]], output_path: str) -> None:
        """Implements abstract method from BaseConverter"""
        self.convert_to_gpkg(data, output_path)

    def _get_ogr_geometry_type(self, geom_type: str) -> int:
        """Converts GeoJSON geometry type to OGR geometry type"""
        type_map = {
            "Point": ogr.wkbPoint,
            "LineString": ogr.wkbLineString,
            "Polygon": ogr.wkbPolygon,
            "MultiPoint": ogr.wkbMultiPoint,
            "MultiLineString": ogr.wkbMultiLineString,
            "MultiPolygon": ogr.wkbMultiPolygon
        }
        return type_map.get(geom_type, ogr.wkbUnknown)

    def _add_feature(self, layer: ogr.Layer, feature_data: Dict[str, Any]) -> None:
        """Adds GeoJSON feature to OGR layer"""
        feature_def = layer.GetLayerDefn()
        feature = ogr.Feature(feature_def)
        
        # Set properties
        properties = feature_data.get("properties", {})
        for i in range(feature_def.GetFieldCount()):
            field_defn = feature_def.GetFieldDefn(i)
            field_name = field_defn.GetName()
            if field_name in properties:
                feature.SetField(i, str(properties[field_name]))
        
        # Set geometry
        geom_json = feature_data.get("geometry", {})
        if not geom_json:
            logger.warning("Skipping feature without geometry")
            return

        wkt = ogr.CreateGeometryFromJson(str(geom_json))
        if wkt is None:
            logger.error(f"Failed to convert geometry: {geom_json}")
            return

        feature.SetGeometry(wkt)
        if layer.CreateFeature(feature) != 0:
            logger.error("Failed to create feature")

    def convert_to_gpkg(self, geojson_data: Dict[str, Dict[str, Any]], output_path: str) -> None:
        """Converts GeoJSON data to GeoPackage"""
        # Remove existing file if exists
        if os.path.exists(output_path):
            os.remove(output_path)
        
        ds = self.gpkg_driver.CreateDataSource(output_path)
        if ds is None:
            raise RuntimeError(f"Cannot create GeoPackage file: {output_path}")

        try:
            for layer_name, feature_collection in geojson_data.items():
                if not feature_collection.get("features"):
                    logger.warning(f"Skipping empty layer: {layer_name}")
                    continue

                # Check geometry type from first feature
                first_feature = feature_collection["features"][0]
                geom_type = first_feature.get("geometry", {}).get("type")
                ogr_geom_type = self._get_ogr_geometry_type(geom_type)

                # Create layer
                srs = osr.SpatialReference()
                srs.ImportFromEPSG(5186)
                
                # Remove special characters from layer name
                safe_layer_name = ''.join(c for c in layer_name if c.isalnum() or c in ('_',))
                layer = ds.CreateLayer(safe_layer_name, srs, ogr_geom_type)
                
                if layer is None:
                    logger.error(f"Failed to create layer: {layer_name}")
                    continue

                # Create fields
                properties = first_feature.get("properties", {})
                for field_name, value in properties.items():
                    field_def = ogr.FieldDefn(field_name, ogr.OFTString)
                    field_def.SetWidth(254)
                    layer.CreateField(field_def)

                # Add features
                for feature in feature_collection["features"]:
                    self._add_feature(layer, feature)

                logger.info(f"Layer created successfully: {safe_layer_name}")

        finally:
            ds = None
                    