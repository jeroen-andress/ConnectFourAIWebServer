#!/usr/bin/env python

from setuptools import setup
from setuptools.command.install import install
import shutil, os

class ConnectFourWebserverInstallCommand(install):
    def run(self):
         print 'copy ConnectFourWebserver'
         shutil.copy('src/ConnectFourWebserver', '/etc/init.d')
         print 'install ConnectFourWebserver daemon'
         os.system('update-rc.d ConnectFourWebserver defaults')
         install.run(self)

setup(name = 'ConnectFourAIWebserver',
      version = '1.0',
      url = 'https://github.com/jeroen-andress',
      author = 'Jeroen Andress',
      license = 'GNU GENERAL PUBLIC LICENSE',
      install_requires = ['torndo'],
      packages = ['ConnectFourAIWebserver'],
      package_dir = {'ConnectFourAIWebserver': 'src'},
      package_data = {'ConnectFourAIWebserver' : ['src/Static/*'] },
      include_package_data=True,
      cmdclass = {'install': ConnectFourWebserverInstallCommand}
) 

