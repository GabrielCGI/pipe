import os
import sys
import subprocess

#os.add_dll_directory(r'R:\pipeline\networkInstall\arnold\SDK\Arnold-7.1.4.2-windows\bin')
sys.path.append(r"R:\pipeline\networkInstall\arnold\SDK\Arnold-7.2.2.1-windows\python")
from arnold import *


AiBegin()
license_used = AiLicenseIsAvailable()
AiEnd()

if not license_used:
	sys.exit("No License")
