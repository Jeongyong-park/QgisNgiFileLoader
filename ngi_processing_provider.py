from qgis.core import QgsProcessingProvider  # type: ignore
from qgis.PyQt.QtGui import QIcon  # type: ignore
import os

from .ngi_processing_algorithm import NGIProcessingAlgorithm


class NGIProcessingProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(NGIProcessingAlgorithm())

    def id(self):
        return "ngi_converter"

    def name(self):
        return "NGI Converter"

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))
