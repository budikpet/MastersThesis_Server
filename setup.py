from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = ''.join(f.readlines())

setup(
    name='masters_thesis_server',
    version='0.0.0.1',
    description="""A Python web server created for my Master's thesis.""",
    long_description=long_description,
    keywords="ghia,budikpet, web, cli",
    setup_requires=['pytest-runner'],
    install_requires=['fastapi>=0.63.0', 'requests>=2.25.1', 'beautifulsoup4>=4.9.3', 'apscheduler>=3.7.0', 'levenshtein>==0.12.0', 'rq>=1.7.0'],
    tests_require=['pytest==5.0.1', 'betamax', 'flexmock'],
    
    # Can then by installed by 'pip install .[dev]'
    extras_require={
        'dev':  ['sphinx', 'jupyter']
    },
    python_requires='>=3.7',
    author='Petr Budík',
    author_email='budikpet@fit.cvut.cz',
    license='Public Domain',
    url='https://github.com/budikpet/MastersThesis_Server',
    zip_safe=False,
	package_dir={'': 'src'},
    packages=find_packages(),
    # entry_points={
    #     'console_scripts': [
    #         'ghia = ghia:ghia',
    #     ],
    # },
    # package_data={
    #     'ghia': ['templates/*.html', 'static/*.css']
    #     },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries',
        'Framework :: FastAPI',
        'Environment :: Web Environment'
        ],
)