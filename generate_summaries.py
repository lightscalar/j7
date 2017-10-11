import os
import pandas as pd
from solid_db import SolidDB
from zipfile import ZipFile

db = SolidDB('data/db.json')


def generate_summaries(patient_id):
    # Create a .zip file of summary data.

    # Patient Summary
    patient = db.find_by_id(patient_id)
    pat_pckg = {}
    pat_pckg['age'] = patient['age']
    pat_pckg['notes'] = patient['notes']
    pat_pckg['gender'] = patient['gender']
    pat_pckg['gcs'] = patient['gcs']
    pat_pckg['createdAt'] = patient['createdAt']
    pat_pckg['hid'] = patient['hid']
    pat_frame = pd.DataFrame([pat_pckg])

    # Scan Summaries
    scans = db.find_where('scans', 'patient_id', patient_id)
    scan_set = []
    for scan in scans:
        pckg = {}
        pckg['GCS'] = scan['gcs']
        pckg['createdAt'] = scan['createdAt']
        for eye in ['left', 'right']:
            if eye in scan:
                for key,val in scan[eye].items():
                    pckg['{}_{}'.format(eye, key)] = val
        scan_set.append(pckg)
    scan_frame = pd.DataFrame(scan_set)

    # Now Save as CSV Files.
    pat_file = 'tmp/{}_patient_info.csv'.format(patient['hid'])
    scn_file = 'tmp/{}_scan_info.csv'.format(patient['hid'])
    pat_frame.to_csv(pat_file, index=False)
    scan_frame.to_csv(scn_file, index=False)

    # Now Zip them up.
    files = [scn_file, pat_file]
    zipfile_location = '../dist/static/downloads/{}.zip'.format(patient['hid'])
    with ZipFile(zipfile_location, 'w') as f:
        for filename in files:
            f.write(filename)
            os.remove(filename)

    file_url = '../static/downloads/{}.zip'.format(patient['hid'])
    return file_url



    


