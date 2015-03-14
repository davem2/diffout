from setuptools import setup, find_packages
setup(
  name          = 'diffout',
  author        = 'David Maranhao',
  author_email  = 'david.maranhao@gmail.com',
  license       = 'MIT',
  description   = 'Translates pgdp.org formatted text files into ppgen syntax.',
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
  ],
  classifiers = [
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Text Processing",
  ],
)

