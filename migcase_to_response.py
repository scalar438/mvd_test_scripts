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

    supplier_info = root.find("core:supplierInfo", ns)
    if supplier_info is None:
        supplier_info = 0
    else:
        supplier_info = supplier_info.text

    employee_id = root.find("core:employee/core:ummsId", ns)
    if employee_id is None:
        employee_id = 0
    else:
        employee_id = employee_id.text
        
    uid = root.find('core:uid', ns).text
    date = root.find('core:date', ns).text

    return (date, request_id, supplier_info, uid, employee_id, filename)

def is_arrival(filename: str):
    return ("MigCase_" in filename) or (('Form' in filename) and ('Unreg' not in filename))

def is_departure(filename: str):
    return 'Unreg' in filename

def process_file(path, options: argparse.Namespace):
    arrival_data = None
    departure_data = None
    with zipfile.ZipFile(path) as rep_archive:
        for file in rep_archive.filelist:
            print(file.filename.encode("cp437").decode("cp866"))

            if file.filename.lower().endswith(".xml"):
                if 'response' in file.filename:
                    continue

                file_data = rep_archive.read(file.filename)

                if is_arrival(file.filename) and options.parse_arrival:
                    data = get_data_from_file(file_data, os.path.basename(file.filename))
                    if arrival_data is None or arrival_data[0] < data[0]:
                        arrival_data = data

                if is_departure(file.filename) and options.parse_departure:
                    data = get_data_from_file(file_data, os.path.basename(file.filename))                    
                    if departure_data is None or departure_data[0] < data[0]:
                            departure_data = data
    if options.gen_success:
        prefix = 'response_success_'
        response_template = response_template_success
    else:
        prefix = 'response_error_'
        response_template = response_template_error

    for data in [arrival_data, departure_data]:
        if data is not None:
            with open(prefix + data[-1], 'wt') as f:
                f.write(response_template.format(request_id = data[1],
                    supplier_info=data[2],
                    uid=data[3],
                    employee_id=data[4]))
    
    print('Answers has been generated')

def main():
    parser = argparse.ArgumentParser(description='Parse the archive and generate answers for the reports')
    parser.add_argument('--parse_arrival', required=False, help='Try to find a parse an arrival file in the archive', action='store_true')
    parser.add_argument('--parse_departure', required=False, help='Try to find a parse an arrival file in the archive', action='store_true')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--gen_success', action='store_true')
    group.add_argument('--gen_fail', action='store_true')

    parser.add_argument('--filename', action='store', required=True)

    args = parser.parse_args()

    process_file(args.filename, args)

if __name__ == '__main__':
    main()