from setuptools import setup, find_packages


commands = """
[console_scripts]
nits = nits:main
nits-test = nits:test
"""

setup(name='nits',
      version="0.3.1",
      description="Non Intrusive Test SMTPserver",
      author="Jean Schurger",
      author_email='jean@schurger.org',
      url='https://github.com/jeansch/nits',
      packages=find_packages(),
      install_requires=['Twisted'],
      entry_points=commands,
      license='GPLv3')
