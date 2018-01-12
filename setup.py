from setuptools import find_packages, setup

setup(
    name='acoustid-priv-tools',
    version='0.1',
    packages=find_packages('acoustid_priv_tools'),
    license='MIT',
    author='Lukas Lalinsky',
    author_email='lukas@acoustid.biz',
    url='https://github.com/acoustid/acoustid-priv-tools',
    description='Command line tools for api.acoustid.biz',
    install_requires=['mediafile', 'requests'],
    entry_points={
        'console_scripts': ['acoustid-priv-sync=acoustid_priv_tools.sync:main'],
    },
)
