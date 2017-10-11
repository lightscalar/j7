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
        print(data)
        self.data = data


class J7App(App):
    patient_hid = StringProperty('NO ACTIVE PATIENT')
    patient = ObjectProperty(None)
    patients = ListProperty([])
    scan = ObjectProperty(None)
    scan_status = StringProperty('START SCAN')

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
        # self.scans = db.find_where('scans', 'patient_id', self.patient['_id'])
        # self.root.patient.scans.patient_id = self.patient['_id']
        # self.root.patient.scans.refresh()
        # self.root.current = 'patient_screen'

    def set_patient(self, patient_id):
        # Set current patient.
        self.patient = db.find_by_id(patient_id)
        self.patient_hid = self.patient['hid']
        # self.root.current = 'patient_screen'
        # self.root.patient.scans.patient_id = self.patient['_id']
        # self.root.patient.scans.refresh()
        # self.scans = db.find_where('scans', 'patient_id', self.patient['_id'])

    def update_patient(self, description, gender, age):
        # Update the patient.
        pkg = {'description': description, 'age': age, 'gender': gender}
        if self.patient:
            db.update(pkg, self.patient['_id'])

    def update_scan(self, notes, gcs):
        pkg = {'notes': notes, 'gcs': gcs}
        if self.scan:
            self.scan = db.update(pkg, self.scan['_id'])

    def create_scan(self):
        # Create a new scan.
        patient_id = self.patient['_id']
        scan = {'patient_id': patient_id, 'gcs': '', 'notes': ''}
        self.scan = db.insert('scan', scan)
        self.root.current='scan_screen'
        # self.root.patient.scans.refresh()
        self.patients = db.all('patients')
        # self.scans = db.find_where('scans', 'patient_id', self.patient['_id'])

    def start_scan(self):
        # Initiate scan by saving an oracle request.
        if self.scan:
            print('Requesting scan from oracle.')
            request = Vessel('request.oracle')
            request.scan = self.scan
            request.save()

    def update_status(self, target_file):
        # Oracle has updated status. Let's report it!
        try:
            v = Vessel(target_file)
            self.scan_status = v.message
            if v.data_processing_complete:
                self.scan = db.find_by_id(self.scan['_id'])
                self.root.current = 'summary_screen'
            print(v.message)
        except:
            print('Could not access Oracle status.')

    def kill_threads(self, signal, frame):
        self.watchdog.kill()

    def build(self):
        # Build this app!
        os.remove('status.oracle') # remove oracle status file...
        self.patients = db.all('patients')
        self.watchdog = Watchdog(['status.oracle'])
        self.watchdog.events.on_change += self.update_status
        signal.signal(signal.SIGINT, self.kill_threads)


if __name__ == '__main__':
    J7App().run()
