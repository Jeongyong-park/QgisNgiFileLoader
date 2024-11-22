from parsers.converters.geojson_converter import GeoJSONConverter
from parsers.converters.geopackage_converter import GeoPackageConverter
from parsers.nda_parser import NDAParser
from parsers.ngi_parser import NGIParser
from qgis.core import (QgsProcessingAlgorithm,
                      QgsProcessingParameterFile,
                      QgsProcessingParameterFileDestination,
                      QgsVectorLayer,
                      QgsProject,
                      QgsCoordinateReferenceSystem)
from qgis.PyQt.QtCore import QCoreApplication
from pathlib import Path

class NGIProcessingAlgorithm(QgsProcessingAlgorithm):
    INPUT_NGI = 'INPUT_NGI'
    OUTPUT_GPKG = 'OUTPUT_GPKG'

    def __init__(self):
        super().__init__()

    def name(self):
        return 'ngiconverter'

    def displayName(self):
        return self.tr('NGI/NDA Converter')

    def createInstance(self):
        return NGIProcessingAlgorithm()

    def shortHelpString(self):
        return self.tr('Converts NGI/NDA files to GeoPackage format')

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('NGIProcessingAlgorithm', string)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_NGI,
                self.tr('NGI File'),
                extension='ngi'
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_GPKG,
                self.tr('Output GeoPackage File'),
                fileFilter='GeoPackage files (*.gpkg)'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """Converts NGI/NDA files to GeoPackage and adds layers to map"""
        try:
            # Set input/output file paths
            ngi_path = Path(self.parameterAsFile(parameters, self.INPUT_NGI, context))
            output_path = Path(self.parameterAsFileOutput(parameters, self.OUTPUT_GPKG, context))
            nda_path = ngi_path.with_suffix('.nda')

            # Check input files existence
            if not ngi_path.exists():
                feedback.reportError(f'NGI file not found: {ngi_path}')
                return {self.OUTPUT_GPKG: None}
            if not nda_path.exists():
                feedback.reportError(f'NDA file not found: {nda_path}')
                return {self.OUTPUT_GPKG: None}

            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert files and verify data structure
            feedback.pushInfo('Starting file conversion...')
            
            ngi_parser = NGIParser()
            nda_parser = NDAParser()
            geojson_converter = GeoJSONConverter()
            gpkg_converter = GeoPackageConverter()

            feedback.pushInfo('Parsing NGI file...')
            ngi_parsed = ngi_parser.parse_file(str(ngi_path))
            feedback.pushInfo(f'NGI parsing result: {len(ngi_parsed)} layers')
            
            feedback.pushInfo('Parsing NDA file...')
            nda_parsed = nda_parser.parse_file(str(nda_path))
            feedback.pushInfo(f'NDA parsing result: {len(nda_parsed)} layers')

            feedback.pushInfo('Merging data...')
            geojson_data = geojson_converter.merge_data(ngi_parsed, nda_parsed)
            
            # Verify GeoJSON data structure
            for layer_name, features in geojson_data.items():
                feedback.pushInfo(f'Layer: {layer_name}, Feature count: {len(features)}')
                if features:
                    first_feature = next(iter(features.values()))
                    feedback.pushInfo(f'Sample feature: {first_feature}')

            feedback.pushInfo('Creating GeoPackage...')
            gpkg_converter.convert_to_gpkg(geojson_data, str(output_path))

            # Check GeoPackage layers
            feedback.pushInfo('Adding layers to map...')
            
            # Create layer group name from input filename
            input_file = self.parameterAsFile(parameters, self.INPUT_NGI, context)
            group_name = Path(input_file).stem
            
            # Create layer group
            root = QgsProject.instance().layerTreeRoot()
            group = root.insertGroup(0, group_name)
            
            # Get layer list from GeoPackage file
            vector_layer = QgsVectorLayer(str(output_path), "", "ogr")
            if not vector_layer.isValid():
                feedback.reportError(f"Cannot open GeoPackage file: {output_path}")
                return {self.OUTPUT_GPKG: None}
            
            sublayers = vector_layer.dataProvider().subLayers()
            feedback.pushInfo(f"Found sublayers: {len(sublayers)}")
            
            loaded_layers = []
            for sublayer in sublayers:
                layer_name = sublayer.split('!!::!!')[1] if '!!::!!' in sublayer else sublayer
                layer_uri = f"{output_path}|layername={layer_name}"
                new_layer = QgsVectorLayer(layer_uri, layer_name, "ogr")
                
                if new_layer.isValid():
                    new_layer.setCrs(QgsCoordinateReferenceSystem('EPSG:5186'))
                    if new_layer.featureCount() > 0:
                        QgsProject.instance().addMapLayer(new_layer, False)
                        group.addLayer(new_layer)
                        loaded_layers.append(new_layer)
                        feedback.pushInfo(f'Layer added: {layer_name} (Features: {new_layer.featureCount()})')
                    else:
                        feedback.pushInfo(f'Empty layer: {layer_name}')
                else:
                    feedback.reportError(f'Cannot load layer: {layer_name}')

            if loaded_layers:
                feedback.pushInfo(f'Total {len(loaded_layers)} layers loaded')
            else:
                feedback.reportError('No layers loaded')

            return {self.OUTPUT_GPKG: str(output_path)}

        except Exception as e:
            feedback.reportError(f'Error occurred: {str(e)}')
            import traceback
            feedback.reportError(traceback.format_exc())
            return {self.OUTPUT_GPKG: None}