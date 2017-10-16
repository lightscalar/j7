import os
import sys
sys.path.append('../mathtools')
from mathtools.utils import Vessel
from events import Events
from threading import Thread
from watchdog import Watchdog
from gazepoint import GazePoint
from time import sleep
from solid_db import SolidDB

db = SolidDB('data/db.json')


class Oracle(object):

    def __init__(self):

        # Connect to the Gazepoint tracker.
        self.gp = GazePoint()

        # Establish an event bus.
        self.events = Events()

        # Set up the watchdog...
        try:
            os.remove('request.oracle')
        except:
            pass
        target_files = ['request.oracle']
        self.watchdog = Watchdog(target_files)
        self.watchdog.events.on_change += self.scan

    def scan(self, target_file):

        # Load oracle request.
        scan = Vessel(target_file).scan

        # Start the scan.
        scan = self.gp.collect(scan)
        os.remove('request.oracle')
        try:
            db.update(scan)
        except:
            print('Cannot save to database.')

    def kill():
        self.watchdog.kill()
        self.gp.kill()


if __name__ == '__main__':

    # Instantiate the oracle.
    oracle = Oracle()

    try:
        while True:
            print('Oracle Alive')
            sleep(5)
    except KeyboardInterrupt:
        oracle.kill()
