from setuptools import setup

setup(
    name='project',
    packages=['app'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)
