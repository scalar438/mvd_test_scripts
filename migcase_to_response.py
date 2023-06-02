#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import os
import argparse
import zipfile
import enum

response_template_success_migcase = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
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

response_template_error_migcase = '''
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

response_template_error_unregcase = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<ns2:response xmlns:ns2="http://umms.fms.gov.ru/hotel/hotel-response" xmlns="http://www.w3.org/2000/09/xmldsig#" xmlns:ns3="http://umms.fms.gov.ru/replication/core" schemaVersion="1.0">
	<ns2:requestId>{request_id}</ns2:requestId>
	<ns2:entityType>UnregMigCase</ns2:entityType>
	<ns2:error>
		<ns2:externalSystemId>{supplier_info}</ns2:externalSystemId>
		<ns2:externalCaseId>{uid}</ns2:externalCaseId>
		<ns2:errorMsg>ru.gov.fms.umms.services.core.BusinessException: Сохранение невозможно. В базе данных обнаружен полный дубликат:{employee_id}</ns2:errorMsg>
	</ns2:error>
</ns2:response>
'''

response_template_success_unregcase = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<ns2:response xmlns:ns2="http://umms.fms.gov.ru/hotel/hotel-response" xmlns="http://www.w3.org/2000/09/xmldsig#" xmlns:ns3="http://umms.fms.gov.ru/replication/core" schemaVersion="1.0">
	<ns2:requestId>{request_id}</ns2:requestId>
	<ns2:entityType>UnregMigCase</ns2:entityType>
	<ns2:success>
		<ns2:notificationNumber>02/440-001/19/000177</ns2:notificationNumber>
		<ns2:externalSystemId>{supplier_info}</ns2:externalSystemId>
		<ns2:externalCaseId>{uid}</ns2:externalCaseId>
		<ns2:ummsId>{employee_id}</ns2:ummsId>
	</ns2:success>
</ns2:response>
'''

response_template_success_form5 = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<ns2:response xmlns:ns2="http://umms.fms.gov.ru/hotel/hotel-response" 
              xmlns="http://www.w3.org/2000/09/xmldsig#" 
              xmlns:ns3="http://umms.fms.gov.ru/replication/core" 
              schemaVersion="1.0">
    <ns2:requestId>{request_id}</ns2:requestId>
    <ns2:entityType>RegCase</ns2:entityType>
    <ns2:success>
        <ns2:externalSystemId>{supplier_info}</ns2:externalSystemId>
        <ns2:externalCaseId>{uid}</ns2:externalCaseId>
        <ns2:ummsId>{employee_id}</ns2:ummsId>
    </ns2:success>
    <ns2:ummsVersion>
        <ns3:app>2021.5.0.37</ns3:app>
        <ns3:db>21.10.01</ns3:db>
        <ns3:dict>21.10.01</ns3:dict>
        <ns3:fias>16.04.2021</ns3:fias>
        <ns3:gid>91</ns3:gid>
        <ns3:domain>domain1</ns3:domain>
    </ns2:ummsVersion>
</ns2:response>
'''

response_template_error_form5 = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<ns2:response xmlns:ns2="http://umms.fms.gov.ru/hotel/hotel-response" 
              xmlns="http://www.w3.org/2000/09/xmldsig#" 
              xmlns:ns3="http://umms.fms.gov.ru/replication/core" schemaVersion="1.0">
    <ns2:requestId>{request_id}</ns2:requestId>
    <ns2:entityType>RegCase</ns2:entityType>
    <ns2:error>
        <ns2:externalSystemId>{supplier_info}</ns2:externalSystemId>
        <ns2:externalCaseId>{uid}</ns2:externalCaseId>
        <ns2:errorMsg>Для категории поставщика («Гостиницы») загрузка данных указанного типа не допустима. {employee_id}</ns2:errorMsg>
    </ns2:error>
    <ns2:ummsVersion>
        <ns3:app>2021.5.0.31</ns3:app>
        <ns3:db>21.10.01</ns3:db>
        <ns3:dict>21.10.01</ns3:dict>
        <ns3:fias>16.04.2021</ns3:fias>
        <ns3:gid>91</ns3:gid>
        <ns3:domain>domain1</ns3:domain>
    </ns2:ummsVersion>
</ns2:response>
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

    filename = os.path.splitext(filename)[0]

    return (date, request_id, supplier_info, uid, employee_id, filename)

class FileType(enum.Enum):
    ForeignerArrival = 1
    ForeignerDeparture = 2
    CitizenArrival = 3
    CitizenDeparture = 4

def type_by_name(filename: str):
    if ("MigCase_" in filename):
        return FileType.ForeignerArrival
    if ('Form' in filename) and ('Unreg' not in filename):
        return FileType.CitizenArrival
    if 'Case' in filename and 'Unreg' in filename:
        return FileType.ForeignerDeparture
    return FileType.CitizenDeparture

def process_file(path, options: argparse.Namespace):
    arrival_data = None
    departure_data = None
    with zipfile.ZipFile(path) as rep_archive:
        for file in rep_archive.filelist:
            print("Current file: " + file.filename.encode("cp437").decode("cp866"))

            if file.filename.lower().endswith(".xml"):
                if 'response' in file.filename:
                    continue

                file_data = rep_archive.read(file.filename)

                cur_type = type_by_name(file.filename)

                data = get_data_from_file(file_data, os.path.basename(file.filename))

                if options.parse_arrival and (cur_type == FileType.CitizenArrival or cur_type == FileType.ForeignerArrival):
                    if arrival_data is None or arrival_data[0] < data[0]:
                        arrival_data = data
                    
                    if cur_type == FileType.CitizenArrival:
                        if options.gen_success:
                            response_template = response_template_success_form5
                        else:
                            response_template = response_template_error_form5
                    else:
                        if options.gen_success:
                            response_template = response_template_success_migcase
                        else:
                            response_template = response_template_error_migcase

                elif options.parse_departure and (cur_type == FileType.CitizenDeparture or cur_type == FileType.ForeignerDeparture):
                    if departure_data is None or departure_data[0] < data[0]:
                        departure_data = data
                    if cur_type == FileType.CitizenDeparture:
                        if options.gen_success:
                            response_template = response_template_success_form5
                        else:
                            response_template = response_template_error_form5
                    else:
                        if options.gen_success:
                            response_template = response_template_success_unregcase
                        else:
                            response_template = response_template_error_unregcase
    if options.gen_success:
        prefix = 'response_success_'
        response_template = response_template_success_migcase
    else:
        prefix = 'response_error_'
        response_template = response_template_error_migcase

    print('Arrival data: ' + str(arrival_data))
    print('Departure data: ' + str(departure_data))
    
    base_path = os.path.curdir
    try:
        if options.out_dir:
            os.makedirs(options.out_dir)
            base_path = options.out_dir
    except:
        print('Can\'t create directories for path {0}. Using a current directory for a path'.format(options.out_dir))

    for data in [arrival_data, departure_data]:
        if data is not None:
            template_body = response_template.format(request_id = data[1],
                    supplier_info=data[2],
                    uid=data[3],
                    employee_id=data[4])
            
            base_filename = os.path.join(base_path, prefix + data[-1])

            if options.pack_zip:
                with zipfile.ZipFile(base_filename + '.zip', "w") as zip_response:
                    zip_response.writestr('response_' + data[-1] + '.xml', template_body)
            else:
                with open(base_filename + '.xml', 'wt') as file_response:
                    file_response.write(template_body)
    
    print('Answers has been generated')

def main():
    parser = argparse.ArgumentParser(description='Parse the archive and generate answers for the reports')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--parse_arrival', action='store_true')
    group.add_argument('--parse_departure', action='store_true')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--gen_success', action='store_true')
    group.add_argument('--gen_fail', action='store_true')

    parser.add_argument('--filename', action='store', required=True)
    parser.add_argument('--out_dir', action='store', required=False)
    parser.add_argument('--pack_zip', action='store_true', required=False)

    args = parser.parse_args()

    process_file(args.filename, args)

if __name__ == '__main__':
    main()