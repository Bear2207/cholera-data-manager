import ssl
import importlib
print('python', __import__('sys').version)
print('default verify paths', ssl.get_default_verify_paths())
try:
    certifi = importlib.import_module('certifi')
    print('certifi path', certifi.where())
except Exception as e:
    print('certifi missing', type(e).__name__, e)
