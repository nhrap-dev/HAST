
#Python file to start the source code so that we can push the updates and avoid issues on FEMA machines
from subprocess import call
import os
call('CALL conda.bat activate hazus_env & start /min python ./Python/HAST_run.py', shell=True)
# if os.path.exists("HAST.bat"):
#     os.remove("HAST.bat")
# else:
#     exit(0)