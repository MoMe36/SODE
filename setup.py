
from setuptools import setup, find_packages

setup(
    name = 'sode', 
    version = '0.1',
    packages = find_packages(), 
    install_requires = [
    'pandas', 
	'networkx', 
	'numpy', 
	'scipy', 
	'google.generativeai', 
	'astor', 
	'tabulate', 
	'matplotlib'
    ], 
)
