#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import os
import argparse
import zipfile

response_template_success = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<ns2:response xmlns:ns2="http://umms.fms.gov.ru/hotel/hotel-response" xmlns="http://www.w3.org/2000/09/xmldsig#" schemaVersion="1.0">
    <ns2:requestId>{request_id}</ns2:requestId>
    <ns2:entityType>MigCase</ns2:entityType>
    <ns2:success>
        <ns2:externalSystemId>{supplier_info}</ns2:externalSystemId>
        <ns2:externalCaseId>{uid}</ns2:externalCaseId>
        <ns2:ummsId>{employee_id}</ns2:ummsId>
    </ns2:success>
</ns2:response>
'''

response_template_error = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<response xmlns="http://umms.fms.gov.ru/hotel/hotel-response" schemaVersion="1.0">
    <requestId>{request_id}</requestId>
    <entityType>MigCase</entityType>
    <error>
        <externalSystemId>{supplier_info}</externalSystemId>
        <externalCaseId>{uid}</externalCaseId>
        <errorMsg>Error text: {employee_id}</errorMsg>
    </error>
</response>
'''

def get_data_from_file(s: str, filename: str):
    root = ET.fromstring(s)

    ns = {'mig': 'http://umms.fms.gov.ru/replication/migration',
          'core':'http://umms.fms.gov.ru/replication/core'}

    request_id = root.find("core:requestId", ns).text

    uid = root.find('core:uid', ns).text

    reg_case_uid = root.find('mig:regCaseUid', ns)
    if reg_case_uid is not None:
        reg_case_uid = reg_case_uid.text

    date = root.find('core:date', ns).text

    return (date, request_id, reg_case_uid, uid, filename)

def is_arrival(filename: str):
    return ("MigCase_" in filename) or (('Form5_' in filename) and ('Unreg' not in filename))

def is_departure(filename: str):
    return 'Unreg' in filename

def process_file(path):
    arrival_data = None
    departure_data = None
    with zipfile.ZipFile(path) as rep_archive:
        for file in rep_archive.filelist:
            if file.filename.lower().endswith(".xml"):
                if 'response' in file.filename:
                    continue
                file_data = rep_archive.read(file.filename)

                if is_arrival(file.filename):
                    data = get_data_from_file(file_data, os.path.basename(file.filename))
                    print(str(data))
                    if arrival_data is None or arrival_data[0] < data[0]:
                        arrival_data = data

                if is_departure(file.filename):
                    data = get_data_from_file(file_data, os.path.basename(file.filename))
                    print(str(data))
                    if departure_data is None or departure_data[0] < data[0]:
                        departure_data = data

    if arrival_data is None:
        print('There is no arrival in the archive')
        return 0
    
    if departure_data is None:
        print('There is no departure in the archive')
        return 0

    if arrival_data[1] == departure_data[1]:
        print('request_id are the same in arrival and departure')
        return -1
    if arrival_data[3] != departure_data[2]:
        print('uids are different in arrival and departure')
        return -1

    print("Arrival and departure has the same uids")

def main():
    parser = argparse.ArgumentParser(description='Find and check last arrival and departure in the given archive')
    parser.add_argument('--filename', action='store', required=True)
    args = parser.parse_args()
    return process_file(args.filename)

if __name__ == '__main__':
    exit(main())