#!/usr/bin/python
# -*- coding: UTF-8 -*-
# Author:Shengqiao  Time: 2022/3/8

from fusion_database import ActiveTestApi, TestData
import re
import time
import datetime
import pandas as pd
import os
from tkinter.filedialog import askopenfilename
import tkinter
from tkinter.simpledialog import askstring
from datetime import datetime


fusion_a = ActiveTestApi()
fusion_t = TestData()

# data = fusion_a.get_socket_info('57016334ACG-T0202')
# print(data)

# data = fusion_a.check_user('shengqw', '11111')
# print(data)

# PN = '1837240002'
# subpn= fusion_a.get_subpn_by_toppn(PN)

'''
# 获取SubPN
# PN = '1832212702'
info = fusion_a.qry_zhu_bomtree(subpn)
useful_value = ()
for idx, row in info.iterrows():
    print(row)
    print(row['OCP_COMPONENT_TYPE'])
    if row['OCP_COMPONENT_TYPE'] in ['TESTSP']:
        useful_value = (row['OPLK_COMPONENT_ITEM'], row['OCP_COMPONENT_ITEM'],
                        row['OCP_COMPONENT_ITEM_DESC'], row['OCP_COMPONENT_ITEM_REV'])
        break
print(useful_value)
subpn = useful_value[0]
print(subpn)
'''
'''
# 获取MCU FW PN, Ver 和 bootloader PN, Ver
# subpn = '1832212689'
'''

'''
data = fusion_a.qry_zhu_bomtree(subpn)
mcu_fw_pn = ''
mcu_fw_ver = ''
bootloader_fw_pn = ''
bootloader_fw_ver = ''
for idx, row in data.iterrows():
    ocp_comp_type = row.get('OCP_COMPONENT_TYPE')
    if ocp_comp_type is None:   # transfer Nonetype to str
        ocp_comp_type = ''
    ocp_comp_desc = row.get('OCP_COMPONENT_ITEM_DESC')
    if ocp_comp_desc is None:
        ocp_comp_desc = ''   
    if (ocp_comp_type.find('FRMWRE') != -1) and (ocp_comp_desc.find('Application'.upper()) != -1):
        mcu_fw_pn = row.get('OPLK_COMPONENT_ITEM', '')
        mcu_fw_ver = row.get('DOC_REV', '')        
    if ('FRMWRE' in ocp_comp_type) and ('BOOTLOADER' in ocp_comp_desc):
        bootloader_fw_pn = row.get('OPLK_COMPONENT_ITEM', '')
        bootloader_fw_ver = row.get('DOC_REV', '')  
print('MCU FW PN info is:', mcu_fw_pn)
print('MCU FW Version is:', mcu_fw_ver)
print('BootLoader FW PN info is:', bootloader_fw_pn)
print('BootLoader FW Version is:', bootloader_fw_ver)
'''

# 验证BOMTree 返回数据
# subpn = '1832212641'
'''
subpn = '1832212689'
data = fusion_a.qry_zhu_bomtree(subpn)
print(data)
'''


'''
test_result = []
testresult_id = []
for tenvid in ['RT', 'LT', 'HT']:
    data = fusion_t.get_test_records_by_para(WO='847119291', process='ACPD_TRX_TestData', tenv=tenvid, paraName='SerialNo', paraValue='Z22030S3P')
    if len(data) > 0:
        # last_row = len(data) - 1
        print(data[-1])
        if data[-1]['PassorFail'] == 'P':
            test_result.append(True)
        else:
            test_result.append(False)
        testresult_id.append(int(data[-1]['TestResult_ID']))
print(test_result)
print(testresult_id)
if len(test_result) == 3:
    if (False not in test_result) and (testresult_id[0] < testresult_id[1]) and (testresult_id[0] < testresult_id[2]):
        print(True)
    else:
        print(False)
else:
    print(False)
'''

'''
import gui_ui_qa_verify
action = gui_ui_qa_verify.QA_Verify()
data = action.get_productinfo('00000221700464')
print(action.productinfo)
'''

# usecount = fusion_a.get_socket_info('57016334AC-T0202')
# print(usecount)


# check the test result
test_result = []
testresult_id = []
test_date = []
# data_list = fusion_t.get_mfg_record('Z220804H9', 'ACPD_Coherent_TestData')
# data_list = fusion_t.get_mfg_record('Z22140H42', 'ACPD_Coherent_OSNRData')
data_list = fusion_t.get_mfg_record('Z22120BUK', 'ACPD_Coherent_TestData')
# data_list = fusion_t.get_mfg_record('Z22290EZF', 'ACPD_Coherent_AssemblyData')
print(len(data_list))
for i in range(len(data_list)):
    print(data_list[i]['TestResultDtBySnProcess'])

TestDate = data_list[0]['TestResultDtBySnProcess']['TestDate']
#print(type(TestDate))
print(TestDate)
date = TestDate.date()
print(date)
time = TestDate.time()
print(time)
dt1 = datetime.combine(date, time)
print(dt1)


'''
dt = datetime.strptime('2017-04-23 01:12:00', '%Y-%m-%d %H:%M:%S')
print(dt)
'''

#testdate1 = datetime(1, 1, 1, tzinfo=datetime.tzinfo())
#print(testdate1)

'''
if TestDate > TestData1:
    print(True)
else:
    print(False)
'''


'''
for tenvid in ['RT', 'LT', 'HT']:
    tenvid_datalist = []
    # 获取同一温度下所有测试记录
    for i in range(len(data_list)):    
        mfg_record = data_list[i]['TestResultDtBySnProcess']
        if tenvid == mfg_record['Test_Area']:
            tenvid_datalist.append(mfg_record)
    # 获取同一温度下所有测试记录的最新记录
    if tenvid_datalist:  # 检查 tenvid_datalist 不为空
        max_testid = 0
        max_listno = 0
        for j in range(len(tenvid_datalist)):
            if max_testid <= tenvid_datalist[j]['ID']:
                max_testid = tenvid_datalist[j]['ID']
                max_listno = j
        if tenvid_datalist[max_listno]['Test_Result'] == 'P':
            test_result.append(True)
        else:
            test_result.append(False)
        testresult_id.append(tenvid_datalist[max_listno]['ID'])
        test_date.append(tenvid_datalist[max_listno]['TestDate'])
print(test_result)
print(testresult_id)
print(test_date)
print(test_date[0])
print(type(test_date[0]))
if test_date[0] <= test_date[1]:
    print(True)
else:
    print(False)
'''

'''
access_id = 3
if access_id in [1, 2]:  # engineer authority
    pwd_gui = 'MOLEX'
else:
    pwd_gui = 'operator'
print(pwd_gui)
'''

# test the function get_wo_info
'''
data = fusion_a.get_wo_info('847514880')
print(data)
'''

'''
# test read excel file
setup_file = os.getcwd() + '\\config file\\' + '1833302427_Ver2.xlsx'
temp_spec = {'RT': False, 'LT': False, 'HT': False}
for key, value in temp_spec.items():
    sheet = 'OSNR_' + key
    try:
        df = pd.read_excel(setup_file, sheet_name=sheet)
    except ValueError as err:
        print(err)
    else:
        temp_spec.update({key: True})
print(temp_spec)
'''

'''
barcode_info = {'SN': ['', 0], 'Datecode': ['', 0]}
data = fusion_a.get_barcode_info('[)>0611PWOTRB92JAA25SLBFJTU2922400000221800561', 'TXPCXGJL2IFUJ60A')
# data = fusion_a.get_barcode_info('0000022180056', 'TXPCXGJL2IFUJ60A')
barcode_info.update({'SN': data['SN'], 'Datecode': data['Datecode']})
print(barcode_info)
'''

'''
result, productinfo = fusion_a.get_productinfo('00000221700464')
print('result is', result)
print('product = ', productinfo)
for key, value in productinfo.items():
    print(key, value)
'''

'''
result = fusion_a.opc_move_in('Z22261A5U', 'N-P-400GEPRM-01', 'fhu11')
print(result)
'''

'''
result = fusion_a.opc_trigger_data('OPCN2214SFP0008', 'fhu11')
print(result)
'''

'''
result = fusion_a.opc_move_out('OPCN2214SFP0008', 'N-P-EPRM-03', 'fhu11')
print(result)
'''

'''
result = fusion_a.get_last_sub_eeprom_record('Z22140H50', 'EEPROM')
print('last_eeprom_record:', result)
'''

'''
verify_result = {'S1': '', 'S2': '', 'S3': '',
                              'S4': '', 'S5': '', 'S6': '', 'S7': '', 'S8': '', 'S9': '', 'S10': '', 'S11': '',
                              'S12': '', 'S13': '', 'S14': '', 'S15': '', 'S16': '', 'S17': '', 'S18': '', 'S19': '',
                              'S20': '', 'S21': '', 'S22': '', 'S23': '', 'S24': '', 'S25': '', 'S26': '', 'S27': '',
                              'S28': '', 'S29': '', 'S30': ''}
page_list = (
            "LP_00H", "UP_00H", "UP_01H", "UP_02H", "UP_03H", "UP_04H", "UP_13H", "UP_28H", "UP_29H", "UP_2AH",
            "UP_2BH", "UP_30H", "UP_41H", "UP_C0H", "UP_C1H", "UP_C2H", "UP_C3H", "UP_C4H", "UP_C5H")
data_dut = []
a = 0
for page in page_list:
    # data_dut.append(page)
    list_item = 'S' + f'{a + 1}'
    verify_result[list_item] = page        # data_dut[a]
    a += 1
print(verify_result)
print('\n')
for a in range(1, 20):
    k = 'S' + f'{a}'
    print(verify_result.get(k))
'''

'''
list1 = [24, 65, 0, 6, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 232]
str1 = ''
for i in range(len(list1)):
    element = '{:02x}'.format(list1[i]).upper()
    print(element)
    str1 += element
    str1 += '-'
print(str1)
print(list1)
data = ','.join('{:02x}'.format(list1).upper())
print(data)
'''

'''
result = fusion_t.LoadTestDataAllForDataSet('Z22140H4P', 'ACPD_Coherent_SimpleData', 'SimpleData')
print(result)
result = fusion_t.LoadTestDataAllForDataSetBySn('Z22140H4P', 'ACPD_Coherent_SimpleData')
print(result)
'''

'''
start_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
start_time = time.time()
time.sleep(3.1)
end_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
run_time = '{:.2f}'.format(time.time() - start_time)

page_list = ("LP_00H", "UP_00H", "UP_01H", "UP_02H", "UP_03H", "UP_04H", "UP_13H", "UP_28H", "UP_29H", "UP_2AH",
             "UP_2BH", "UP_30H", "UP_41H", "UP_C0H", "UP_C1H", "UP_C2H", "UP_C3H", "UP_C4H", "UP_C5H")
testdata = {'DateCreated': '', 'PartDescription': '', 'PartNumber': '', 'WorkOrder': '',
                              'OldSerialNumber': '', 'NewSerialNumber': 'NK2319V0002', 'MagicCode': '', 'A0Checksum1': '',
                              'A0Checksum2': '', 'Operator': '', 'Trace_Rev': '', 'CodeSpec': '', 'Firmware': '',
                              'StationID': 'MT32', 'Rev': '', 'Reult': 'P', 'Debug': '',
            'S1': '18410006FF00000041AA0000000018217D860000182100000000400000000000000000000001000103000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002113E81010D3E2155FF0000000000000000000000000000000000000000000000000000000000000000E8',
            'S2': '184D4F4C4558202020202020202020202000093A3138333732343030313820202020202031304E4B3233313956303030322020202020323330353039202020202020202020202020E04C0007000000000000FE00050000000000000000006C00334845313635363441425241303120204E4F4B2020494E554941565648414191',
            'S3': '010301018C000000000078EA0005640F7980460000009D1900F077CD0707060306091C67FF1F80785A00000000000000010F0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000BA',
            'S4': '5000FA004B00FD00908875308CA0772400000000000000005500F6005000FB000000000000000000000000000000000018A501F50F8D027600000000000000009B8200FB4DF0018E0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000057',
            'S5': '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
            'S6': 'FC800000000000000000FF7000F0FFB80078FFDC003CFFEE001EFFCA005AFFB80078000000000000000000000000000000000000000000000000000000000001E89017708000FA88FC7C0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F8',
            'S7': '0D1083FAFF000100FF00010000000F000000000000000000000000000000000000000000000000000000000000000000001E050000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
            'S8': '666599995998A6665500F6005000FB000960000008E80000007800000072000055F000004E20000000230000001E00000A0000F00A0001040A0000000A0000000BB8F44807D0F830FFFF0000FFFF000000500000003200009BE800009B200000FF38FAECFE70FB500258F9C0012CFA880190F8F800C8FA244BE8000033E80000',
            'S9': 'E146051EDC280F5C7BE800006BE800004BE8000033E80000005F0000005A00005000FA004B00FD0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
            'S10': '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
            'S11': '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
            'S12': '00000000000000000000000000000000030000000000000000000000000000009B849ABC9CB09C4C03000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
            'S13': '030000000258012CF9C0F7040258012CFA88F7CC019000C8F9C0F704019000C8FA88F7CC0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
            'S14': '00001011C3D5D3D4100000AA00000000408BB797C2E80C6F00000000FAE701443F1B2BADC4B02B1B40977624C48DCEC14074102AC2ABBA6E00000000314E6669B7AC6B323D548C07C26CF99646C720890000000000000000000000000000000039AD85A03B404EAC3AD19EA53BB6B8A00000082A071706B807CA004E00000201',
            'S15': '324C000000000000000000000000000000008D9A7DD494CE75399938AC0F8B43806A8A868136B044945D000000000000000000000000000000000000515C49C8495C51515C49C8495C51515C49C8495C51515C49C8495C51010203040506000017AE166600000100009E004E00000000150F003CFC680000005AF90000000000',
            'S16': '7340A0A07340A0A07340A0A07340A0A00000000000000000000000000000000000000000000000007AE17D707AE18000000000990000FF7C0002FFFC070A070A070A070A051E051E051E051E00000000AD0E000088B40000849B0000B020000055000000AA000000000000000000000000000000000000000000000000000000',
            'S17': '0000000000000000000000000000006A00540041003600280029001F001F0021001E001B0016000B000C000D000E001300100012000600040001FFFDFFFB00000006000400040007000400000001000200020009000A000A0011000D000700070009000E0011000F0010000F00170018020102020202020131EE00EF00000000',
            'S18': '0BFF0C380C680C9A0CD00D040D370D690D9C0DCE0E020E360E6B0E9C0ED00F0007130720073B07560770078907A207B707D107E507FB080C081F082F083F084F30DACC1CB73DB3523CF0701DC20C461D46784F480000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
            'S19': '3F3C7EB13F281D7A3F3BEBE23F27C0C7BF2B8AB2BF0888AD3F7EA2CA3F635DF73F7EA0783F636AE7BF674F9ABF38D7280000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000310006A4322B000000000000000000000000000000000000000000000000',
                              'S20': '', 'S21': '', 'S22': '', 'S23': '', 'S24': '', 'S25': '', 'S26': '', 'S27': '',
                              'S28': '', 'S29': '', 'S30': '', 'ChannelNum': '0', 'DataType': 'QAVERIFY',
                              'Failure_Code': '', 'Failure_Reason': '', 'User_Name': ''}
xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
xml_str += '<LOT_RECORD>\n'
xml_str += '    <MODE>Production</MODE>\n'
xml_str += '    <LOT_ID>L00001</LOT_ID>\n'
xml_str += '    <PART_NUM>PN222</PART_NUM>\n'
xml_str += '    <PART_REV>01</PART_REV>\n'
xml_str += '    <TEST_CODE>TEST</TEST_CODE>\n'
xml_str += '    <PROGRAM>QA Verify GUI</PROGRAM>\n'
xml_str += '    <PROGRAM_REV>1.0.0.3</PROGRAM_REV>\n'
xml_str += '    <START_DATE>%s</START_DATE>\n' % start_date
xml_str += '    <END_DATE>%s</END_DATE>\n' % end_date
xml_str += '    <TESTER_ID>MT-002</TESTER_ID>\n'
xml_str += '    <PART_RECORD>\n'
xml_str += '        <PART_ID>SN0002</PART_ID>\n'
xml_str += '        <PART_RESULT>1</PART_RESULT>\n'
xml_str += '        <TEST_TIME>%s</TEST_TIME>\n' % run_time
if testdata['Reult'] == 'P':
    record_result = 'PASS'
else:
    record_result = 'FAIL'
a = 1
for page in page_list:
    xml_str += '        <TEST_RECORD>\n'
    xml_str += '            <TNAME>%s</TNAME>\n' % page
    xml_str += '            <RESULT>%s</RESULT>\n' % record_result
    k = 'S' + f'{a}'
    xml_str += '            <VECT_RESULT>%s</VECT_RESULT>\n' % testdata[k]
    xml_str += '            <VECT_TYPE>hex</VECT_TYPE>\n'
    xml_str += '            <VECT_ADDR>0080</VECT_ADDR>\n'
    xml_str += '        </TEST_RECORD>\n'
    a += 1
xml_str += '    </PART_RECORD>\n'
xml_str += '</LOT_RECORD>\n'

try:
    # filepath = '\\\\zh-mfs-srv\\Active\\ACPDU\\' + testdata['StationID'] + '\\guad_xml\\'
    filepath = os.getcwd() + '\\xml_Results\\'
    if not os.path.exists(filepath):
        os.mkdir(filepath)
    filename = filepath + testdata['NewSerialNumber'] + '_' + re.sub(r'[:\s-]', '_', str(datetime.now())[0:19]) + '.xml'
    file = open(filename, 'wt')
    file.write(xml_str)
    file.close()
except:
    print('Save xml file fail')
'''

'''
list1 = [1]
if list1:
    print('true')
else:
    print('false')
'''
i=5
print('Removing Handler %s' % i)
