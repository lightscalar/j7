'''Launch all servers, etc., for Johnny-Seven!'''
from subprocess import Popen
from time import sleep

# Main control loop for handling process launch, restarting failed servers...

# Serve the static site.
oracle = Popen(['python', 'oracle.py'])

# Launch the UI's socket server!
gui = Popen(['python', 'j7.py'])

# Monitor processes; shut down on keyboard break.
try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    oracle.kill()
    gui.kill()

