from setuptools import setup, find_packages

setup(
    name='nits',
    version="1.0.0",
    description="Non Intrusive Test SMTPserver",
    author="Jean Schurger",
    author_email='jean@schurger.org',
    url='https://github.com/jeansch/nits',
    packages=find_packages(),
    install_requires=['Twisted'],
    extras_require={
        'dev': [
            'build',
            'twine',
        ],
    },
    entry_points={
        'console_scripts': [
            'nits = nits:main',
            'nits-test = nits:test',
        ],
    },
    license='GPLv3',
    python_requires='>=3.8',
)
