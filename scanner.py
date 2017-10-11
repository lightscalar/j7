import sys
sys.path.append('../mathtools/')
from numpy import *
from tbi_parser import *
import socket
import serial
import time
from ipdb import set_trace as debug
from library_of_scans import *
from mathtools.utils import Vessel
from analysis import *


class Scanner(object):

    def __init__(self, cfg=None):

        # Because Python.
        if not cfg:
            cfg = {}

        cfg.setdefault('port_id', 'COM4')
        cfg.setdefault('baudrate', 9600)
        cfg.setdefault('timeout', 2.0)
        cfg.setdefault('gaze_host', '127.0.0.1')
        cfg.setdefault('gaze_port', 4242)
        cfg.setdefault('gaze_address', (cfg['gaze_host'], cfg['gaze_port']))
        self.cfg = cfg


    def gazepoint_connect(self):

        # Attempt to connect to the Gazepoint server.
        try:
            print('> Establishing socket connection with Gazepoint server.')
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.cfg['gaze_address'])
            print('> Gazepoint connection established')
            s.send(str.encode('<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'))
            s.send(str.encode('<SET ID="ENABLE_SEND_EYE_LEFT" STATE="1" />\r\n'))
            s.send(str.encode('<SET ID="ENABLE_SEND_EYE_RIGHT" STATE="1" />\r\n'))
            s.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))
            return s
        except:
            print('> Cannot establish connection with Gazepoint.')
            return None


    def run(self, command):
        assert command in ['standard', 'periodic', 'nystagmus'], \
                'Command not recognized.'

        # OPEN THE PORTAL!!
        with serial.Serial(self.cfg['port_id'], self.cfg['baudrate'],
                timeout=self.cfg['timeout']) as arduino:

            # Wait while we initialize the microcontroller before attempting
            # communications.
            print('> Initializing the microcontroller.')
            time.sleep(2.0);
            print('> Microcontroller initialization is complete.')

            # Collect 'dem fine ambient light intensity measurements.
            arduino.write(b"8")
            light_level = arduino.readline()
            light_level = light_level.decode(encoding='UTF-8')
            self.light_level = float(light_level)/1000.0 # convert to mW/cm^2.

            # Connect to the Gazepoint device.
            gazepoint = self.gazepoint_connect()
            if not gazepoint:
                return {'errors':\
                        'Cannot establish connection with Gazepoint server.'}

            # Now collect the requested data.
            if (command == 'standard'): # Collect single flash data.
                scanner_data = standard_scan(gazepoint, arduino)

            elif (command == 'periodic'):
                scanner_data = periodic_scan(gazepoint, arduino)

            elif (command == 'nystagmus'):
                scanner_data = nystagmus_scan(gazepoint, arduino)

            # Close socket connection to the Gazepoint.
            gazepoint.close()

            # Package the data.
            obs = parse_data(scanner_data)
            data = generate_time_series(obs)
            data['ambient_light_level'] = self.light_level

            return data


if __name__ == '__main__':
    from vanity import *

    s = Scanner()
    out = s.run('standard')

    process_raw_data(out, 'quirky')


    if False:

        t = array(data['time'])
        rd = array(data['right']['diameter'])
        ld = array(data['left']['diameter'])
        ridx = (t>=0) * (rd>0)
        lidx = (t>=0) * (ld>0)

        tr = t[ridx] - min(t[ridx])
        tl = t[lidx] - min(t[lidx])
        right_pupil = rd[ridx] * 1000
        left_pupil = ld[lidx] * 1000

        left_summary = analyze_standard_scan(tl, left_pupil, filename='left.png')
        right_summary = analyze_standard_scan(tr, right_pupil, filename='right.png')

        v = Vessel('scan.dat')
        v.t = td
        v.rd = right_pupil
        v.ld = left_pupil
        v.save()











