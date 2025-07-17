from zeep import Client, helpers
import json
import time
import pandas as pd
import os
from lxml.html import etree
import re
from datetime import datetime
import xmltodict
import urllib.request
import ssl
import requests


class ActiveTestApi:
    def __init__(self):
        t1 = time.time()
        url = 'http://zh-amtsdb-srv.oplink.com.cn/ActiveTestApi/Sys_QuaryAPI.asmx?WSDL'
        self.client = Client(url)
        # print(self.client)
        print('It costs ' + '{:.2f}'.format(time.time() - t1) + 's to connect Fusion ActiveTestApi DataBase')

    def connect_status_check(self):
        pass

    def check_user(self, username, password):
        info = self.client.service.CheckUser(username, password)
        useful_value = info['CheckUserResult']['_value_1']['_value_1'][0]['CheckUserData']
        access_id = useful_value['access_id']
        error = info['error']
        return access_id

    def get_socket_info(self, evb_sn):
        info = self.client.service.GetSocketInfo(evb_sn)
        if len(info['GetSocketInfoResult']['_value_1']) > 0:
            useful_value = info['GetSocketInfoResult']['_value_1']['_value_1'][0]['GetSocketInfoData']
            usecount = int(useful_value['UseCount'])
            # print(useful_value)
        else:
            usecount = 1000
        return usecount

    def update_socket_count(self, evb_sn, count):
        self.client.service.UpdateSocketCount(serialNo=evb_sn, value=count)

    def qry_zhu_bomtree(self, partno):
        info = self.client.service.qry_ZHU_BOMTree(partno)
        data = info['qry_ZHU_BOMTreeResult']['_value_1']['_value_1']
        data_list = [helpers.serialize_object(val['ORDER']) for val in data]
        return pd.DataFrame(data_list)

    def get_bom_info(self, pn, component_type):
        # component_type can be in ('TSPAQL', 'TESTSP', 'EEPROM', 'FRMWRE', 'SUBASY')
        useful_value = ()
        info = self.qry_zhu_bomtree(pn)
        for idx, row in info.iterrows():
            if row['OCP_COMPONENT_TYPE'] == component_type:
                useful_value = (row['OPLK_COMPONENT_ITEM'], row['OCP_COMPONENT_ITEM'],
                                row['OCP_COMPONENT_ITEM_DESC'], row['OCP_COMPONENT_ITEM_REV'])
                break
        return useful_value

    def get_subpn_by_toppn(self, toppn):
        subpn = self.get_bom_info(toppn, 'SUBASY')
        return subpn[0]

    def get_spec_file_bomtree(self, bom_df):
        file_type_all = {'CS': 'EEPROM', 'FW': 'FRMWRE', 'TS': 'TESTSP'}
        file_base_path = {'CS': 'Q:\OCP Released Code Specifications', 'FW': 'Q:\OCP Released Firmware\Hex Files',
                          'TS': 'Q:\Automation Test Specifications\oplink'}
        file_all = {}
        pn_all = {}
        for key, value in file_type_all.items():
            for idx, row in bom_df.iterrows():
                if row['OCP_COMPONENT_TYPE'] == value:
                    if key == 'CS':  # cs file was defined by PN and version info
                        cs_path = file_base_path['CS'] + '\\' + row['OPLK_COMPONENT_ITEM'] + '\\' + row[
                            'OPLK_COMPONENT_ITEM'] + '_ver' + row['OCP_COMPONENT_ITEM_REV'] + '.txt'
                        if os.path.exists(cs_path):
                            file_all.update({key: cs_path})
                            pn_all.update({key: row['OPLK_COMPONENT_ITEM']})
                            break
                    elif key == 'FW':  # fw and ts file were defined  only by PN
                        fw_dir = file_base_path['FW'] + '\\' + row['OPLK_COMPONENT_ITEM']
                        fw_path = fw_dir + '\\' + os.listdir(fw_dir)[0]
                        if os.path.exists(fw_path):
                            ocp_discription = row['OCP_COMPONENT_ITEM_DESC'].lower()
                            if ocp_discription.find('application') >= 0:
                                file_all.update({'MCU_Application': fw_path})
                                pn_all.update({'MCU_Application': row['OPLK_COMPONENT_ITEM']})
                            elif ocp_discription.find('bootloader') >= 0:
                                file_all.update({'MCU_Bootloader': fw_path})
                                pn_all.update({'MCU_Bootloader': row['OPLK_COMPONENT_ITEM']})
                            elif ocp_discription.find('DSP') >= 0:
                                file_all.update({'DSP_FW': fw_path})
                                pn_all.update({'DSP_FW': row['OPLK_COMPONENT_ITEM']})
                            else:  # for comman use
                                file_all.update({key: fw_path})
                                pn_all.update({key: row['OPLK_COMPONENT_ITEM']})
                    elif key == 'TS':
                        ts_path = file_base_path['TS'] + '\\' + row['OPLK_COMPONENT_ITEM'] + '_ver' + row[
                            'OCP_COMPONENT_ITEM_REV'] + '.xlsx'
                        if os.path.exists(ts_path):
                            file_all.update({key: ts_path})
                            pn_all.update({key: row['OPLK_COMPONENT_ITEM']})
                            break
        return file_all, pn_all

    def get_barcode_info(self, barcode, pn):
        barcode_info = {'SN': ['', 0], 'Datecode': ['', 0]}
        # for item in ['SN', 'Datecode', 'WES serial number']:
        for item in ['SN', 'Datecode']:
            info = self.client.service.GetTDBarcodeInfo(barcode, pn, item, False)
            valid_data = info['GetTDBarcodeInfoResult']['_value_1']['_value_1'][0]['GetTDBarcodeInfoData']['TypeValue']
            ErrorID = info['GetTDBarcodeInfoResult']['_value_1']['_value_1'][0]['GetTDBarcodeInfoData']['ErrorID']
            barcode_info.update({item: [valid_data, ErrorID]})
        return barcode_info

    def qry_ZHU_ItemInfo(self, pn):
        info = self.client.service.qry_ZHU_ItemInfo(pn)
        data = xmltodict.parse(etree.tostring(info).decode())
        return json.loads(json.dumps(data))['ROOT']['RESULT']['ITEMINFO']

    def get_wo_info(self, wo):
        info = self.client.service.GetWorkOrderReleaseDate(wo)
        data = info['GetWorkOrderReleaseDateResult']['_value_1']
        if len(data) > 0:
            result = data['_value_1'][0]['GetWorkOrderReleaseDateData']['IsSampleOrder']
        else:
            result = 0
        return result

    def get_last_sub_eeprom_record(self, subsn, datatype):
        max_id = 0
        max_listno = 0
        info = self.client.service.GetEproomData(subsn, datatype)
        data = info['GetEproomDataResult']['_value_1']
        if len(data) > 0:                  # 返回该sn的所有sub eepromload 记录。
            value_data = data['_value_1']
            max_DateCreated = value_data[0]['GetEproomData']['DateCreated']
            for i in range(len(value_data)):
                if max_DateCreated < value_data[i]['GetEproomData']['DateCreated']:
                    max_DateCreated = value_data[i]['GetEproomData']['DateCreated']
                    max_listno = i
            result = value_data[max_listno]['GetEproomData']
        else:
            result = None
        return result

    def get_productinfo(self, topsn):
        context = ssl._create_unverified_context()  # 创建取消服务器证书验证的context参数(当前请求代码影响)
        url = 'https://zuhaip.molex.com:9607/api/v2/container/query/getProductInfo?container=' + topsn
        response = urllib.request.urlopen(url, context=context)
        json_data = response.read()
        productinfo = {}
        if len(json_data) > 0:
            productinfo = json.loads(json_data)
            return True, productinfo
        else:
            return False, productinfo

    def opc_move_in(self, subsn, workflowId, employeeId, wo=None):
        if wo not in ['GRR', 'DJ', 'VERIFY']:           # wo为这3个项目时就不进行这个操作
            heads = {'Content-Type': 'application/json'}
            body = '{"Container": "' + subsn + '", "Resource": "' + workflowId + '", "employeeId": "' + employeeId + '"}'
            rep = requests.post(url="https://zuhaip.molex.com:9607/api/v2/container/process/moveIn", headers=heads,
                                data=body, verify=False)
            text = rep.text
            if text == '':
                return True
            else:
                print(json.loads(text)['message'])
                return False
        else:
            return True

    def opc_trigger_data(self, subsn, employeeId, wo=None):      # opc trigger data 需要使用Subsn, move in&out 均可使用subsn or topsn
        if wo not in ['GRR', 'DJ', 'VERIFY']:
            heads = {'Content-Type': 'application/json'}
            body = '{"Container": "' + subsn + '", "DataCollectionDef": "MlxTestResultForTMS", "employeeId": "' + employeeId + '", "mlxTestResult": "1"}'
            rep = requests.post(url="https://zuhaip.molex.com:9607/api/v2/container/process/triggerDataCollection",
                                headers=heads, data=body, verify=False)
            text = rep.text
            if text == '':
                return True
            else:
                print(json.loads(text)['message'])
                return False
        else:
            return True

    def opc_move_out(self, subsn, workflowId, employeeId, wo=None):
        if wo not in ['GRR', 'DJ', 'VERIFY']:
            heads = {'Content-Type': 'application/json'}
            body = '{"Container": "' + subsn + '", "Resource": "' + workflowId + '", "employeeId": "' + employeeId + '"}'
            rep = requests.post(url="https://zuhaip.molex.com:9607/api/v2/container/process/moveStd", headers=heads,
                                data=body, verify=False)
            text = rep.text
            if text == '':
                return True
            else:
                print(json.loads(text)['message'])
                return False
        else:
            return True

    def upload_eeprom_record(self, testdata, xml_str):
        filename = testdata['PartNumber'] + '_' + testdata['NewSerialNumber'] + '_' + testdata['DataType']
        date_time = testdata['DateCreated']
        result = self.client.service.UploadEproomRecord(filename, xml_str, date_time)
        return result['UploadEproomRecordResult']

    '''
    # 原来的上传EEPROM的方法
    def upload_eeprom_record(self, date_time, xml_file):
        filename = os.path.split(xml_file)[1].split('.xml')[0]
        with open(xml_file, 'r') as fin:
            context = fin.read()
        info = self.client.service.UploadEproomRecord(filename, context, date_time)
    '''


class TestData:
    def __init__(self):
        t1 = time.time()
        url = 'http://zh-amtsdb-srv.oplink.com.cn/TestData/ReceiveTestData.asmx?WSDL'
        self.client = Client(url)
        print('It costs ' + '{:.2f}'.format(time.time() - t1) + 's to connect Fusion TestData DataBase')

    def upload_test_record(self, xml_file):
        testdate = str(datetime.now())[0:19]
        # print(testdate)
        # print(xml_file)
        filename = os.path.split(xml_file)[1].split('.xml')[0]
        # print(filename)
        with open(xml_file, 'r') as fin:
            context = fin.read()
        info = self.client.service.UploadTestRecord(filename, context, testdate)

    def get_test_records_by_para(self, WO, process, tenv, paraName, paraValue):
        test_id_list = []
        result_list = []
        t1 = time.time()
        info = self.client.service.LoadTestDataAllForDataSetByPara(WO, process, tenv, paraName, paraValue)
        data = info['_value_1']
        if len(data) > 0:  # 检查返回数据是否为空
            record = data['_value_1']
        else:
            record = []
        for i in range(len(record)):
            test_id = record[i]['GetAllTestDataForActiveDataByPara']['TestResult_ID']
            if test_id not in test_id_list:
                test_id_list.append(test_id)
        for i in range(len(test_id_list)):
            useful_dict = {'TestResult_ID': test_id_list[i]}
            for j in range(len(record)):
                if test_id_list[i] == record[j]['GetAllTestDataForActiveDataByPara']['TestResult_ID']:
                    para_name = record[j]['GetAllTestDataForActiveDataByPara']['Para_Name']
                    para_value = record[j]['GetAllTestDataForActiveDataByPara']['Value']
                    useful_dict[para_name] = para_value
            result_list.append(useful_dict)
        return result_list

    def get_mfg_record(self, sn, process):
        valid_data = []
        info = self.client.service.GetDataFromTestResultBySnProcess(sn, process)
        data = info['GetDataFromTestResultBySnProcessResult']['_value_1']
        if len(data) > 0:
            valid_data = data['_value_1']
        return valid_data

    def LoadTestDataAllForDataSet(self, sn, process, testtype):
        info = self.client.service.LoadTestDataAllForDataSet(sn, process, testtype)
        print(info)

    def LoadTestDataAllForDataSetBySn(self, sn, process):
        info = self.client.service.LoadTestDataAllForDataSetBySn(sn, process)
        # print(info)
        data = info['LoadTestDataAllForDataSetBySnResult']['_value_1']['_value_1']
        # print(data)
        data_list = [helpers.serialize_object(val['GetAllTestDataForActiveDataBySn']) for val in data]
        df = pd.DataFrame(data_list)
        df_new = df.sort_values(by='TestDate', ascending=False)
        return df_new


class TestResult:
    def __init__(self, report_file, lot_record, export_dest):
        self.report_file = report_file
        self.from_header_config()
        self.parse_header()
        self.lot_record = lot_record
        self.export_dest = export_dest

    def from_header_config(self):
        default_header_path = 'header.json'
        with open(default_header_path, 'r') as header_config_file:
            header_config = json.load(header_config_file)
        self.header_rows = header_config['header_length']

    def parse_header(self):
        self.report_header = pd.read_csv(
            self.report_file,
            header=None,
            names=['index', 'value'],
            nrows=self.header_rows,
            delimiter=',',
            usecols=[0, 1],
            index_col=0
        ).to_dict()['value']

    def parse_test_file(self):
        self.from_header_config()
        report_data = pd.read_csv(self.report_file, skiprows=self.header_rows, delimiter=',', header=0,
                                  keep_default_na=False, dtype=str)
        test_result_df = report_data.where(~report_data.isna(), None)
        group_df = test_result_df.groupby('CON1')  # group test data by freq
        test_data_freq = []
        for con1 in group_df.size().keys():
            test_data_freq.append(group_df.get_group(con1).reset_index(drop=True))
        return test_data_freq

    def doc_record(self, parent, data):
        child = etree.SubElement(parent, 'DOC_RECOD')
        for key, value in data.items():
            child.set(key, value)

    def para(self, parent, data):
        tag = etree.SubElement(parent, 'PARA')
        for key, value in data.items():
            tag.set(key, value)

    def build_docrev_record(self, parent):
        tag = etree.SubElement(parent, 'DOCREV_RECORD')
        attrib_list = [{'NAME': 'Prod_PN', 'VALUE': self.lot_record.get('part_num')},
                       {'NAME': 'Prod_Process', 'VALUE': self.lot_record.get('wo_id')}]
        for data in attrib_list:
            self.doc_record(tag, data)
        return tag

    def build_recipe_record(self, parent):
        tag = etree.SubElement(parent, 'RECIPE_RECORD')
        name_list = ['Recipe_CRC', 'Prod_SN', 'Prod_Process', 'FW_PN', 'FW_VER', 'FW_Author', 'FW_Date', 'FW_Status',
                     'TS_PN', 'TS_VER', 'TS_Author', 'TS_Date', 'TS_Status', 'CS_PN', 'CS_VER', 'CS_Author', 'CS_Date',
                     'CS_Status', 'TP_PN', 'TP_VER', 'TP_Author', 'TP_Date', 'TP_Status', 'TT_PN', 'TT_VER',
                     'TT_Author', 'TT_Date', 'TT_Status', 'Workflow_Name', 'Operation_Name']
        attrib_dict = {key: '' for key in name_list}
        attrib_dict['Recipe_CRC'] = 'NA'
        attrib_dict['Prod_SN'] = self.report_header.get('SerialNumber')
        attrib_dict['Prod_Process'] = self.lot_record.get('wo_id')
        attrib_dict['FW_PN'] = self.report_header.get('MCU_FW_PN')
        attrib_dict['FW_VER'] = self.report_header.get('MCU_FW_Ver')
        # attrib_dict['Workflow_Name'] = self.lot_record.get('program')
        for key, value in attrib_dict.items():
            data = {'DESC': '', 'NAME': key, 'VALUE': value}
            self.para(tag, data)
        return tag

    def build_mfg_record(self, parent):
        tag = etree.SubElement(parent, 'MFG_RECORD')
        name_list = ['WO_NUM', 'Prod_SN', 'Operator', 'Test_Station', 'Move_In', 'Move_Out', 'Failure_Code',
                     'Test_Type', 'Test_Result', 'Prod_Process', 'Refer_File', 'Perms_Level', 'Test_Area', 'Tester_ID',
                     'ATE_Code', 'GRR_Status', 'GDS_Status', 'ESD_Status']
        attrib_dict = {key: '' for key in name_list}
        attrib_dict['WO_NUM'] = self.lot_record.get('wo_id')
        attrib_dict['Prod_SN'] = self.report_header['SerialNumber']
        attrib_dict['Operator'] = self.lot_record.get('operator')
        attrib_dict['Test_Station'] = self.lot_record.get('tester_id')
        attrib_dict['Move_In'] = self.report_header['Start Time']
        attrib_dict['Move_Out'] = self.report_header['End Time']
        attrib_dict['Failure_Code'] = 'NA'
        attrib_dict['Test_Type'] = 'TestData'
        if self.report_header['Test Result'] == 'PASS':
            attrib_dict['Test_Result'] = 'P'
        else:
            attrib_dict['Test_Result'] = 'F'
        attrib_dict['Prod_Process'] = self.lot_record.get('wo_id')
        for key, value in attrib_dict.items():
            data = {'DESC': '', 'NAME': key, 'VALUE': value}
            self.para(tag, data)
        return tag

    def build_cond_id(self, parent):
        for data in self.parse_test_file():
            tag = etree.SubElement(parent, 'COND_ID', VALUE=data['CON1'][0])  # attribute VALUE is the freq value
            for index, row in data.iterrows():
                if row['RESULT'] == '1':
                    result = 'P'
                else:
                    result = 'F'
                name_list = ['ACTIVE', 'DESC', 'FILENAME', 'FREE_MAX', 'FREE_MIN', 'MAX', 'MIN', 'NAME', 'PASSFAIL',
                             'SCALE', 'TEST_DATE', 'UNITS', 'VALUE']
                attrib_dict = {key: '' for key in name_list}
                attrib_dict['MAX'] = row['HIGH_LIMIT']
                attrib_dict['MIN'] = row['LOW_LIMIT']
                attrib_dict['NAME'] = row['TNAME']
                attrib_dict['UNITS'] = row['UNIT']
                attrib_dict['VALUE'] = row['VALUE']
                attrib_dict['PASSFAIL'] = result
                self.para(tag, attrib_dict)

    def build_test_record(self, parent):
        test_record = etree.SubElement(parent, 'TEST_RECORD')
        tenv_id = etree.SubElement(test_record, 'TENV_ID', VALUE=self.report_header['Test Temp'])
        object = etree.SubElement(tenv_id, 'OBJECT', NAME='TRX')
        port = etree.SubElement(object, 'PORT', NAME='0', VALUE='0')
        self.build_cond_id(port)
        return test_record

    def build_misc_record(self, parent):
        misc_record = etree.SubElement(parent, 'MISC_RECORD')
        crc32 = etree.SubElement(parent, 'CRC32')
        crc32.text = 'DD448CB8'
        misc_record.append(crc32)
        self.build_object_id(misc_record)

    def build_object_id(self, parent):
        tag = etree.SubElement(parent, 'OBJECT_ID')
        self.para(tag, {'DESC': '', 'NAME': 'SoftwareName', 'VALUE': self.lot_record['program']})
        self.para(tag, {'DESC': '', 'NAME': 'Version', 'VALUE': self.lot_record['program_rev']})

    def create_tree(self):
        root = etree.Element('MEAS_RECORD', CRC32='')
        self.build_docrev_record(root)
        self.build_recipe_record(root)
        self.build_mfg_record(root)
        self.build_test_record(root)
        self.build_misc_record(root)
        tree = etree.ElementTree(root)
        file_name = '{pn}_{sn}_{start_time}_{program}_{test_temp}.xml'.format(
            pn=self.lot_record['part_num'],
            sn=self.report_header["SerialNumber"],
            start_time=re.sub(r'[:\s-]', '_', str(self.report_header["Start Time"])[0:19]),
            program=self.lot_record['program'],
            test_temp=self.report_header["Test Temp"],
        )
        self.xml_file = os.path.join(self.export_dest, file_name)
        print('Export xml file: ' + str(self.xml_file))
        tree.write(self.xml_file, encoding='gb2312')


class EEPROM:
    def para(self, parent, data):
        tag = etree.SubElement(parent, 'PARA')
        for key, value in data.items():
            tag.set(key, value)

    def create_tree(self, item, xml_folder_path):
        # item = {key: '' for key in ['DateCreated', 'PartDescription', 'PartNumber', 'WorkOrder', 'OldSerialNumber','NewSerialNumber', 'MagicCode', 'A0Checksum1', 'A0Checksum2', 'Trace_Rev', 'CodeSpec', 'Firmware', 'StationID', 'Rev', 'Result', 'Debug', 'ChannelNum', 'DataType', 'Operator','Failure_Code', 'Failure_Reason', 'User_Name']}
        # item.update({'S' + str(key + 1): '' for key in range(30)})
        # for key, value in item_input.items(): #update item value if it specify by gui
        #     item[key] = value
        root = etree.Element('TEST_RECORD')
        for key, value in item.items():
            data = {'NAME': key, 'VALUE': value}
            self.para(root, data)
        tree = etree.ElementTree(root)
        file_name = '{pn}_{sn}_{start_time}_{data_type}.xml'.format(pn=item['PartNumber'], sn=item["NewSerialNumber"],
                                                                    start_time=re.sub(r'[:\s-]', '_',
                                                                                      str(datetime.now())[0:19]),
                                                                    data_type=item['DataType'], )
        self.xml_file = os.path.join(xml_folder_path, file_name)
        print('Export xml file: ' + str(self.xml_file))
        tree.write(self.xml_file, encoding='gb2312')


if __name__ == '__main__':
    mydb = ActiveTestApi()
    # info = mydb.qry_zhu_bomtree('1832212093')
    info = mydb.qry_zhu_bomtree('1832212641')
    # print(info)
    file_all, pn_all = mydb.get_spec_file_bomtree(info)
    print(file_all)
