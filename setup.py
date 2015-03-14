from setuptools import setup, find_packages
setup(
  name          = 'diffout',
  author        = 'David Maranhao',
  author_email  = 'david.maranhao@gmail.com',
  license       = 'MIT',
  description   = 'Runs a command on a list of input files, then compares the resulting outputs with copies stored from a previous run.',
  packages      = ['diffout'], # this must be the same as the name above
  version       = '0.1.0',
  url           = 'https://github.com/davem2/diffout', # use the URL to the github repo
  download_url  = 'https://github.com/davem2/diffout/tarball/0.1.0', # I'll explain this in a second
  keywords      = ['text', 'processing', 'developer'], # arbitrary keywords
  entry_points = {
      'console_scripts': [
          'diffout = diffout.diffout:main',
      ],
  },
  install_requires = [
    'docopt >= 0.6.1',
    'colorama >= 0.3.3',
  ],
  classifiers = [
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Topic :: Software Development :: Testing",
    "Topic :: Text Processing",
  ],
)

