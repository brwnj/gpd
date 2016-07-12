from setuptools import setup


setup(
    name='gpd',
    version='1.0.1',
    url='http://github.com/brwnj/gpd',
    license='MIT',
    author='Joe Brown',
    author_email='brwnjm@gmail.com',
    description='Simplies XML downloading from JGI Genome Portal',
    long_description="",
    py_modules=['gpd'],
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        gpd=gpd:gpd
    '''
)
