from typing import TypedDict, Dict, List, Union, Any
from dataclasses import dataclass
from enum import Enum

class GeometryType(Enum):
    UNKNOWN = 0
    POINT = 1
    LINESTRING = 2
    POLYGON = 3
    MULTIPOINT = 4
    MULTILINESTRING = 5
    MULTIPOLYGON = 6
    TEXT = 7
    NETWORKCHAIN = 8

class FieldDefinition(TypedDict):
    name: str
    type: str
    width: int
    precision: int
    nullable: bool

@dataclass
class LayerDefinition:
    name: str
    fields: List[FieldDefinition]
    geometry_type: GeometryType

class GeoProperties(TypedDict):
    record_id: str
    layer_name: str
    attributes: Dict[str, Any]

class GeoFeature(TypedDict):
    type: str
    geometry: Dict[str, Any]
    properties: GeoProperties

class FeatureCollection(TypedDict):
    type: str
    features: List[GeoFeature]