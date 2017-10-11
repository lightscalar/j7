from events import Events
import os
from threading import Thread
from time import sleep

class Watchdog(Thread):

    def __init__(self, target_files):
        '''Identify the files we want to monitor.'''
        Thread.__init__(self)
        self._cached_stamps = [0] * len(target_files)
        self.target_files = target_files
        self.events = Events()
        self.go = True
        self.start()

    def run(self):
        '''Main thread loop.'''
        while self.go:
            sleep(0.01)
            for itr, target_file in enumerate(self.target_files):
                try:
                    stamp = os.stat(target_file).st_mtime
                except:
                    stamp = self._cached_stamps[itr]
                if stamp != self._cached_stamps[itr]:
                    self._cached_stamps[itr] = stamp
                    self.events.on_change(target_file)

    def kill(self):
        '''Kill watchdog thread.'''
        self.go = False
