from setuptools import setup


requirements = []

with open('requirements.txt') as f:
  requirements = f.read().splitlines()

packages = [
    'distee'
]

setup(name='distee.py',
      author='Teekeks',
      licanse='MIT',
      description='A Discord API wrapper',
      install_requirements=requirements,
      python_requires='>=3.9.0')
