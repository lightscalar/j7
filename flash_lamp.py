from threading import Thread
import serial
import sys
from time import sleep


class FlashLamp(Thread):

    def __init__(self):
        # Intialize connection to the Gazepoint tracker.
        Thread.__init__(self)

        # Init parameters.
        self.flash = True
        self.go = True
        self.dt = 100

        # Set the port.
        if sys.platform.startswith('win'):
            self.port = 'COM4'
        else:
            self.port = "/dev/cu.usbserial-DN01AGKS"

        # Launch the thread.
        self.start()

    def flash_lamp(self):
        # Flash the lamp.
        self.flash = True

    def run(self):
        # Main loop of the thread.
        with serial.Serial(self.port, 9600, timeout=2.0) as ser:
            while self.go:
                if self.flash:
                    ser.write(b'f')
                    self.flash = False

    def kill(self):
        # Stop the thread.
        print('Killing Arduino')
        self.go = False


if __name__ == '__main__':
    f = FlashLamp()
    f.flash_lamp()
    f.kill()
