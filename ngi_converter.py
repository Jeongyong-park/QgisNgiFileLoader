from qgis.core import QgsApplication  # type: ignore
from .ngi_processing_provider import NGIProcessingProvider


class NGIConverterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initGui(self):
        self.provider = NGIProcessingProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
