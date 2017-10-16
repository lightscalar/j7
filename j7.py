import os
import sys
sys.path.append('../mathtools')
from mathtools.utils import Vessel
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.recycleview import RecycleView
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.properties import ObjectProperty, ListProperty
from sixer import *
from solid_db import SolidDB
from time import sleep
from kivy.config import Config
from watchdog import Watchdog
import signal
from generate_summaries import *


# Configure the default window size.
Config.set('graphics', 'width', 1400)
Config.set('graphics', 'height', 1700)

# Create an instance of the database.
db = SolidDB('data/db.json')


class PatientList(RecycleView):

    def __init__(self, **kwargs):
        super(PatientList, self).__init__(**kwargs)
        self.refresh()

    def refresh(self):
        data = db.all('patients')
        data = sorted(data, key=lambda x: x['createdAt'], reverse=True)
        self.data = data


class ScanList(RecycleView):

    def __init__(self, **kwargs):
        super(ScanList, self).__init__(**kwargs)

    def refresh(self, patient_id):
        data = db.find_where('scans', 'patient_id', patient_id)
        data = sorted(data, key=lambda x: x['createdAt'], reverse=True)
        self.data = data


class J7App(App):
    patient_hid = StringProperty('NO ACTIVE PATIENT')
    patient_age = StringProperty('')
    patient_gender = StringProperty('')
    patient_description = StringProperty('')
    patient = ObjectProperty(None)
    patients = ListProperty([])
    scan = ObjectProperty(None)
    scan_id = StringProperty('')
    scans = ListProperty([])
    scan_status = StringProperty('START SCAN')
    
    # Result properties...
    scan_time = StringProperty('')
    scan_notes = StringProperty('')
    scan_gcs = NumericProperty('')
    
    left_latency = NumericProperty(0)
    right_latency = NumericProperty(0)
    
    left_starting_diameter = NumericProperty(0)
    right_starting_diameter = NumericProperty(0)
    
    left_minimum_diameter = NumericProperty(0)
    right_minimum_diameter = NumericProperty(0)

    left_absolute_diameter_change = NumericProperty(0)
    right_absolute_diameter_change = NumericProperty(0)

    left_relative_diameter_change = NumericProperty(0)
    right_relative_diameter_change = NumericProperty(0)

    left_average_speed = NumericProperty(0)
    right_average_speed = NumericProperty(0)

    left_recovery_time = NumericProperty(0)
    right_recovery_time = NumericProperty(0)

    def delete_patient(self, patient_id):
        # Delete a patient.
        db.delete(patient_id)
        self.root.home.patients.refresh()
        self.patients = db.all('patients')

    def create_patient(self):
        # Create a new patient. Set as current patient.
        print('Creating a patient.')
        patient = {'hid': sixer()}
        patient['description'] = ''
        patient['age'] = ''
        patient['gender'] = ''
        self.patient = db.insert('patient', patient)
        self.root.home.patients.refresh()
        self.patient_hid = self.patient['hid']
        self.patients = db.all('patients')

    def set_patient(self, patient_id):
        # Set current patient.
        self.patient = db.find_by_id(patient_id)
        print(self.patient)
        self.patient_hid = self.patient['hid']
        self.patient_age = self.patient['age']
        self.patient_gender = self.patient['gender']
        self.patient_description = self.patient['description']
        self.refresh_scans()
        self.root.current = 'patient_screen'

    def update_patient(self, description, gender, age):
        # Update the patient.
        pkg = {'description': description, 'age': age, 'gender': gender}
        print('Attempting to update patient {}'.format(self.patient_hid))
        if self.patient:
            print('Actually Updating the patient.')
            print(self.patient['_id'])
            db.update(pkg, self.patient['_id'])

    def set_scan(self, scan_id):
        # Set the current scan.
        self.scan = db.find_by_id(scan_id)
        self.scan_id = self.scan['_id']
        self.assign_scan()

    def assign_scan(self):
        # Assign variables.
        try:
            self.left_latency = self.scan['left_eye']['latency'] * 1000
        except:
            self.left_latency = -1
            
        try:
            self.right_latency = self.scan['right_eye']['latency'] * 1000
        except:
            pass

        try:
            self.left_starting_diameter = self.scan['left_eye']['starting_diameter']
        except:
            pass

        try:
            self.right_starting_diameter = self.scan['right_eye']['starting_diameter']
        except:
            pass

        try:
            self.left_minimum_diameter = self.scan['left_eye']['minimum_diameter']
        except:
            pass

        try:
            self.right_minimum_diameter = self.scan['right_eye']['minimum_diameter']
        except:
            pass

        try:
            self.left_absolute_diameter_change = \
                   self.scan['left_eye']['absolute_diameter_change']
        except:
            pass

        try:
            self.right_absolute_diameter_change =\
                   self.scan['right_eye']['absolute_diameter_change']
        except:
            pass

        try:
            self.left_relative_diameter_change = \
                   self.scan['left_eye']['relative_diameter_change']
        except:
            pass

        try:
            self.right_relative_diameter_change =\
                   self.scan['right_eye']['relative_diameter_change']
        except:
            pass

        try:
            self.left_average_speed = self.scan['left_eye']['average_speed']
        except:
            pass

        try:
            self.right_average_speed = self.scan['right_eye']['average_speed']
        except:
            pass

        try:
            self.left_recovery_time = self.scan['left_eye']['recovery_time']
        except:
            pass

        try:
            self.right_recovery_time = self.scan['right_eye']['recovery_time']
        except:
            pass
        
        try:
            self.scan_time = self.scan['createdAt']
        except:
            pass
            

    def update_scan(self, notes, gcs):
        pkg = {'notes': notes, 'gcs': gcs}
        if self.scan:
            self.scan = db.update(pkg, self.scan['_id'])

    def delete_scan(self, scan_id):
        # Delete the requested scan.
        scan = db.find_by_id(scan_id)
        patient_id = scan['patient_id']
        db.delete(scan_id)
        self.refresh_scans()
        self.root.patient.scans.refresh(patient_id)

    def refresh_scans(self):
        # Refresh scan list of current patient.
        patient_id = self.patient['_id']
        self.root.patient.scans.refresh(patient_id)
        self.scans = db.find_where('scans', 'patient_id', patient_id)

    def create_scan(self):
        # Create a new scan.
        patient_id = self.patient['_id']
        scan = {'patient_id': patient_id, 'gcs': '', 'notes': ''}
        scan['is_complete'] = False
        self.scan = db.insert('scan', scan)
        self.scan_id = self.scan['_id']
        self.root.current='scan_screen'
        self.patients = db.all('patients')

    def start_scan(self):
        # Initiate scan by saving an oracle request.
        if self.scan:
            print('Requesting scan from oracle.')
            request = Vessel('request.oracle')
            request.scan = self.scan
            request.save()

    def visit_summary(self):
        # Visit the summary screen.
        self.root.current = 'summary_screen'

    def update_status(self, target_file):
        # Oracle has updated status. Let's report it!
        failed_attempts = 0
        while failed_attempts < 25:
            try:
                v = Vessel(target_file)
                self.scan_status = v.message
                if v.data_processing_complete:
                    print('DATA PROCESSING COMPLETE!')
                    self.scan = db.find_by_id(self.scan['_id'])
                    self.set_scan(self.scan['_id'])
                    self.root.scan.scan_button.disabled=False
                    os.remove('status.oracle')
                    break
                break
            except:
                sleep(0.1)
                failed_attempts += 1
                print('Could not access Oracle status.')

    def kill_threads(self, signal, frame):
        self.watchdog.kill()

    def save_data(self, patient_id):
        # Export data to the desktop.
        generate_summaries(patient_id)

    def build(self):
        # Build this app!
        try:
            os.remove('status.oracle') # remove oracle status file...
        except:
            pass
        self.patients = db.all('patients')
        self.watchdog = Watchdog(['status.oracle'])
        self.watchdog.events.on_change += self.update_status
        signal.signal(signal.SIGINT, self.kill_threads)


if __name__ == '__main__':
    J7App().run()
