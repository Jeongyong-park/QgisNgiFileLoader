from typing import TypedDict, List, Literal
from enum import Enum

__all__ = ["GeometryType", "FieldDefinition", "LayerDefinition", "GeoFeature"]


class GeometryType(Enum):
    POINT = "Point"
    LINESTRING = "LineString"
    POLYGON = "Polygon"
    MULTIPOINT = "MultiPoint"
    MULTILINESTRING = "MultiLineString"
    MULTIPOLYGON = "MultiPolygon"
    TEXT = "Text"
    NETWORKCHAIN = "NetworkChain"
    UNKNOWN = "Unknown"


class FieldDefinition(TypedDict):
    name: str
    type: Literal["STRING", "INTEGER", "FLOAT", "DOUBLE", "DATE"]
    width: int
    precision: int
    nullable: bool


class LayerDefinition(TypedDict):
    name: str
    fields: List[FieldDefinition]
    geometry_type: GeometryType


class GeoFeature(TypedDict):
    geometry: dict
    properties: dict
