from setuptools import setup, find_packages


requirements = []

with open('requirements.txt') as f:
  requirements = f.read().splitlines()

packages = [
    'distee'
]

setup(name='distee.py',
      author='Teekeks',
      license='MIT',
      version='0.0.1',
      description='A Discord API wrapper',
      install_requires=requirements,
      python_requires='>=3.9.0',
      packages=find_packages())
