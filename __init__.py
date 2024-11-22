import os
import sys

# Add plugin directory to Python path
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

def classFactory(iface):
    from .ngi_converter import NGIConverterPlugin
    return NGIConverterPlugin(iface)