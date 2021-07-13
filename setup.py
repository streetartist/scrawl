from setuptools import setup
from os import path
DIR = path.dirname(path.abspath(__file__))
INSTALL_PACKAGES = open(path.join(DIR, 'requirements.txt')).read().splitlines()
with open(path.join(DIR, 'README.md')) as f:
 README = f.read()
setup(
 name='scrawl_engine',
 packages=['scrawl'],
 description="Write game like Scratch",
 long_description=README,
 long_description_content_type='text/markdown',
 install_requires=INSTALL_PACKAGES,
 version='0.0.1',
 url='http://github.com/streetartist/scrawl',
 author='Streetartist',
 author_email='15252635839@163.com',
 keywords=['game', 'engine'],
 tests_require=[
 'pytest',
 'pytest-cov',
 'pytest-sugar'
 ],
 python_requires='>=3'
)
