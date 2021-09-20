from setuptools import setup, find_packages


requirements = []

with open('requirements.txt') as f:
  requirements = f.read().splitlines()

packages = [
    'distee'
]

version = '0.0.1a'

try:
    import subprocess

    p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if out:
        version += out.decode('utf-8').strip()
    p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if out:
        version += '+g' + out.decode('utf-8').strip()
except Exception:
    pass

setup(name='distee.py',
      author='Teekeks',
      license='MIT',
      version=version,
      description='A Discord API wrapper',
      install_requires=requirements,
      python_requires='>=3.9.0',
      packages=find_packages())
