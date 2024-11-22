from setuptools import setup, find_packages

setup(
    name="ngi_file_loader",
    packages=find_packages(),
    install_requires=["GDAL>=3.0.0", "qgis>=3.0"],
    python_requires=">=3.7",
)
