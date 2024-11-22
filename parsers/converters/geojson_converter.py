from .base_converter import BaseConverter
from typing import Dict, Any
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class GeoJSONConverter(BaseConverter):
    def __init__(self) -> None:
        super().__init__()

    def convert(self, data: Dict[str, Dict[str, Any]], output_path: str) -> None:
        """Implements abstract method from BaseConverter"""
        merged_layers = self.merge_data(data, {})  # Pass empty dict when no NDA data
        self.save_geojson(merged_layers, output_path)

    def merge_data(self, ngi_data: Dict[str, Dict[str, Any]], nda_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Merge NGI and NDA data by layer"""
        merged_layers: Dict[str, Dict[str, Any]] = {}
        
        # Process each layer
        for layer_name in ngi_data.keys():
            features = []
            
            # Process each record in the layer
            for record_id, geometry in ngi_data[layer_name].items():
                properties = {}
                
                # Try to find properties in NDA data
                if layer_name in nda_data and record_id in nda_data[layer_name]:
                    properties = nda_data[layer_name][record_id]
                    logger.debug(f"Found properties for layer {layer_name}, record {record_id}")
                
                # Add record_id to properties
                properties['record_id'] = record_id
                
                feature = {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": properties
                }
                features.append(feature)
            
            # Create FeatureCollection for the layer
            merged_layers[layer_name] = {
                "type": "FeatureCollection",
                "features": features
            }
            
            logger.info(f"Layer {layer_name}: {len(features)} features created")
        
        return merged_layers

    def save_geojson(self, geojson_layers: Dict[str, Dict[str, Any]], output_base_path: str) -> None:
        """Save GeoJSON data to separate files by layer"""
        output_dir = Path(output_base_path).parent
        output_base = Path(output_base_path).stem
        
        # Ensure output directory exists
        self._ensure_output_dir(output_dir)
        
        for layer_name, layer_data in geojson_layers.items():
            # Skip empty layers
            if not layer_data["features"]:
                self.logger.warning(f"Skipping empty layer: {layer_name}")
                continue
                
            # Create safe filename from layer name
            safe_layer_name = "".join(c for c in layer_name if c.isalnum() or c in (' ', '-', '_')).strip()
            output_path = output_dir / f"{output_base}_{safe_layer_name}.geojson"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(layer_data, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Layer '{layer_name}' saved to {output_path}")