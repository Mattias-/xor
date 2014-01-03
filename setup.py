from setuptools import setup
import multiprocessing

setup(name="Xor",
      version="0.1",
      description="Run things as a service",
      url="https://github.com/Mattias-/xor",
      author="Mattias Appelgren",
      author_email="mattias@ppelgren.se",
      classifiers = [
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Unix',
          'Operating System :: POSIX',
          "Programming Language :: Python :: 2.7"],
      license="MIT",
      packages=["xor","tests"],
      test_suite='nose.collector',
      tests_require=['nose', 'coverage'],
      install_requires=['Flask>=0.10.1'],
      )
