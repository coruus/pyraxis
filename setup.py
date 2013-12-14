from setuptools import setup, find_packages
setup(
    name='pyraxis',
    version='0.0.3',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'raxis_to_tiff = pyraxis.raxis_to_tiff:main_func'
        ],
    },
    author='David Leon Gil',
    author_email='coruus@gmail.com',
    description='Python module and script to read RAXIS detector images as ndarrays and convert them to TIFFs',
    license='GPLv3',
    keywords='RAXIS rigaku',
    url='https://github.com/coruus/pyraxis',
    install_requires=open('requirements.txt').read()
)
