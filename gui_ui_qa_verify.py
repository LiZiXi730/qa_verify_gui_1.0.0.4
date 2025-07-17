import tkinter
from tkinter import scrolledtext
from tkinter.filedialog import askopenfilename
import time
import os
from datetime import datetime
import re
import struct
from fusion_database import ActiveTestApi, TestData
import pandas as pd
import gui_popup
from tkinter.simpledialog import askstring
import tkinter.messagebox as msg
import tkinter.font as tkFont
import sys
from RunCard import RunCard
from DataCardDB import DataCard


class QA_Verify:
    def __init__(self):
        self.fusion_t = None
        self.qa_spec_access = False
        self.mcu_fw_ver_spec_access = False
        self.mcu_spec_reason = ''
        self.init_verify_result()
        self.barcode_info = {'SN': ['', 0], 'Datecode': ['', 0]}

    def init_verify_result(self):
        self.module_data = None
        self.mcu_fw_ver = ''
        self.mcu_fw_pn = ''
        self.bootloader_fw_ver = ''
        self.bootloader_fw_pn = ''
        self.fail_code = []            # ZH fail code list
        self.code_list = []            # GUAD fail code list
        self.fail_reason = ''
        self.start_date = ''
        self.end_date = ''
        self.run_time = ''
        self.verify_result = {'DateCreated': '', 'PartDescription': '', 'PartNumber': '', 'WorkOrder': '',
                              'OldSerialNumber': '', 'NewSerialNumber': '', 'MagicCode': '', 'A0Checksum1': '',
                              'A0Checksum2': '', 'Operator': '', 'Trace_Rev': '', 'CodeSpec': '', 'Firmware': '',
                              'StationID': '', 'Rev': '', 'Reult': 'F', 'Debug': '', 'S1': '', 'S2': '', 'S3': '',
                              'S4': '', 'S5': '', 'S6': '', 'S7': '', 'S8': '', 'S9': '', 'S10': '', 'S11': '',
                              'S12': '', 'S13': '', 'S14': '', 'S15': '', 'S16': '', 'S17': '', 'S18': '', 'S19': '',
                              'S20': '', 'S21': '', 'S22': '', 'S23': '', 'S24': '', 'S25': '', 'S26': '', 'S27': '',
                              'S28': '', 'S29': '', 'S30': '', 'ChannelNum': '0', 'DataType': 'QAVERIFY',
                              'Failure_Code': '', 'Failure_Reason': '', 'User_Name': ''}

    def on_create(self, frame, data, dut, root):
        self.frame = frame
        self.data = data
        self.dut = dut
        self.root = root
        self.fusion_a = data.fusion_a
        pro_info_frame = tkinter.LabelFrame(self.frame, text='Production_Info', fg='blue')
        pro_info_frame.grid(row=0, column=0, columnspan=12,  sticky=tkinter.W)

        '''
        tkinter.Button(self.frame, text='Save log to file', command=self.save_log, width=15).grid(row=6, column=1, sticky=tkinter.W,
                                                                                                  padx=5, pady=5, columnspan=3)
        tkinter.Label(self.frame, text='result').grid(row=6, column=8, ipady=2)
        self.result = tkinter.StringVar()
        self.result_entry = tkinter.Entry(self.frame, textvariable=self.result, state='readonly', width=10)
        self.result_entry.grid(row=6, column=9, sticky=tkinter.E, ipady=2)
        self.result.set('')
        if self.data.pro_info_zh['site'] == 'ZH':
        '''

        # line 0 of prod_Info
        row = 0
        tkinter.Label(pro_info_frame, text="PN").grid(column=0, row=row, sticky=tkinter.W)
        self.pn = tkinter.StringVar()
        if (self.data.pro_info_zh['site'] == 'GUAD') and (self.data.pro_info_zh['operator'] != 'admin'):
            pn_status = 'readonly'
        else:
            pn_status = 'normal'
        self.eny_pn = tkinter.Entry(pro_info_frame, width=28, textvariable=self.pn, state=pn_status)
        self.eny_pn.grid(column=1, row=row, sticky=tkinter.W, columnspan=5, padx=2, pady=2, ipady=2)
        if self.data.pro_info_zh['site'] == 'ZH':
            self.eny_pn.bind('<Return>', self.update_pn_trigger)
            self.eny_pn.config(validate='focusout', validatecommand=self.update_pn)

        tkinter.Label(pro_info_frame, text="WO").grid(column=6, row=row, sticky=tkinter.W)
        self.wo = tkinter.StringVar()
        if (self.data.pro_info_zh['site'] == 'GUAD') and (self.data.pro_info_zh['operator'] != 'admin'):
            wo_status = 'readonly'
        else:
            wo_status = 'normal'
        self.eny_wo = tkinter.Entry(pro_info_frame, width=28, textvariable=self.wo, state=wo_status)
        self.eny_wo.grid(column=7, row=row, sticky=tkinter.W, columnspan=5, padx=2, pady=2, ipady=2)
        if self.data.pro_info_zh['site'] == 'ZH':
            self.eny_wo.bind('<FocusOut>', self.wo_check)
            # self.eny_wo.bind('<Return>', self.wo_check_trigger)

        # line 1 of prod_Info
        row = 1
        tkinter.Label(pro_info_frame, text='SN').grid(column=0, row=row, sticky=tkinter.W)
        self.sn = tkinter.StringVar()
        self.eny_sn = tkinter.Entry(pro_info_frame, width=28, textvariable=self.sn)
        self.eny_sn.grid(column=1, row=row, sticky=tkinter.W, columnspan=5, padx=2, ipady=2, pady=2)
        if self.data.pro_info_zh['site'] == 'GUAD':
            self.eny_sn.focus_set()
            self.eny_sn.bind('<Return>', self.GUAD_parse_barcode)
        else:
            self.eny_sn.bind('<Return>', self.update_sn)

        tkinter.Label(pro_info_frame, text='Sub SN').grid(column=6, row=row, sticky=tkinter.W)
        self.subsn_var = tkinter.StringVar()
        eny_subsn = tkinter.Entry(pro_info_frame, width=28, textvariable=self.subsn_var, state='readonly')
        eny_subsn.grid(column=7, row=row, sticky=tkinter.W, columnspan=5, padx=2, pady=2, ipady=2)

        # line 2 of prod_Info
        row = 2
        tkinter.Label(pro_info_frame, text='Station').grid(column=0, row=row, sticky=tkinter.W)
        self.station = tkinter.StringVar()
        tkinter.Entry(pro_info_frame, width=28, textvariable=self.station, state='readonly') \
            .grid(column=1, row=row, sticky=tkinter.W, columnspan=5, padx=2, pady=2, ipady=2)
        self.station.set(self.data.pro_info_zh['station'].upper())
        tkinter.Label(pro_info_frame, text="Resource").grid(column=6, row=row, sticky=tkinter.W)
        self.resource = tkinter.StringVar()
        tkinter.Entry(pro_info_frame, width=28, textvariable=self.resource, state='readonly') \
            .grid(column=7, row=row, sticky=tkinter.W, columnspan=5, padx=2, pady=2, ipady=2)
        self.resource.set(self.data.pro_info_zh['resource'])

        # line 3 of prod_Info
        row = 3
        tkinter.Label(pro_info_frame, text="Operator").grid(column=0, row=row, sticky=tkinter.W)
        self.operator = tkinter.StringVar()
        tkinter.Entry(pro_info_frame, width=28, textvariable=self.operator, state='readonly') \
            .grid(column=1, row=row, sticky=tkinter.W, columnspan=5, padx=2, pady=2, ipady=2)
        self.operator.set(self.data.pro_info_zh['operator'])
        tkinter.Label(pro_info_frame, text="GUI access").grid(column=6, row=row, sticky=tkinter.W)
        self.guiaccess = tkinter.StringVar()
        tkinter.Entry(pro_info_frame, width=28, textvariable=self.guiaccess, state='readonly') \
            .grid(column=7, row=row, sticky=tkinter.W, columnspan=5, padx=2, pady=2, ipady=2)
        self.guiaccess.set(self.data.pwd_gui)

        # line 4 of prod_Info
        row = 4
        tkinter.Label(pro_info_frame, text="EVB SN").grid(column=0, row=row, sticky=tkinter.W)
        self.evb_sn = tkinter.StringVar()
        if self.data.pro_info_zh['site'] == 'GUAD':
            evb_status = 'readonly'
        else:
            evb_status = 'normal'
        self.eny_evb_sn = tkinter.Entry(pro_info_frame, width=28, textvariable=self.evb_sn, state=evb_status)
        self.eny_evb_sn.config(validate='focusout', validatecommand=self.get_socket_count)
        self.eny_evb_sn.grid(column=1, row=row, sticky=tkinter.W, columnspan=5, padx=2, pady=2, ipady=2)
        self.eny_evb_sn.bind('<Return>', self.get_socket_count_trigger)
        # self.eny_evb_sn.bind('<FocusOut>', self.get_socket_count)

        tkinter.Label(pro_info_frame, text="EVB Count").grid(column=6, row=row, sticky=tkinter.W)
        self.evb_count = tkinter.StringVar()
        eny_count = tkinter.Entry(pro_info_frame, width=28, textvariable=self.evb_count, state='readonly')
        eny_count.grid(column=7, row=row, columnspan=5, sticky=tkinter.W, padx=2, pady=2, ipady=2)

        # line 5 of prod_info
        row = 5
        tkinter.Label(pro_info_frame, text="code_spec_file").grid(column=0, row=row, sticky=tkinter.W)
        self.code_spec_file = tkinter.StringVar()
        eny_cs = tkinter.Entry(pro_info_frame, width=58, textvariable=self.code_spec_file, state='readonly')
        eny_cs.grid(column=1, row=row, sticky=tkinter.W, ipady=2, padx=2, pady=2, columnspan=8)
        self.cs_load_btn = tkinter.Button(pro_info_frame, text='Load', command=self.sel_code_spec, width=9,
                                       state='disable')
        self.cs_load_btn.grid(row=row, column=9, padx=2, sticky=tkinter.E)
        if self.data.pwd_gui == 'MOLEX':
            self.cs_load_btn.config(state='normal')

        # line 6 of prod_info
        row = 6
        tkinter.Label(pro_info_frame, text="test_spec_file").grid(column=0, row=row, sticky=tkinter.W)
        self.test_spec_file = tkinter.StringVar()
        eny_cs = tkinter.Entry(pro_info_frame, width=58, textvariable=self.test_spec_file, state='readonly')
        eny_cs.grid(column=1, row=row, sticky=tkinter.W, ipady=2, padx=2, pady=2, columnspan=8)
        self.ts_load_btn = tkinter.Button(pro_info_frame, text='Load', command=self.sel_test_spec, width=9,
                                       state='disable')
        self.ts_load_btn.grid(row=row, column=9, padx=2, sticky=tkinter.E)
        if self.data.pwd_gui == 'MOLEX':
            self.ts_load_btn.config(state='normal')

        # line 7
        row = 7
        ft = tkFont.Font(family='Arial', size=12, weight=tkFont.BOLD)
        self.btn_qa_verify = tkinter.Button(self.frame, text='QA Verify', font=ft, height=1, width=10)
        self.btn_qa_verify.grid(row=row, column=0, sticky=tkinter.W, padx=5, pady=5)
        self.btn_qa_verify.config(command=self.qa_verify)
        self.btn_qa_verify.bind('<Return>', self.qa_verify)
        
        if self.data.pro_info_zh['site'] == 'ZH':
            self.is_sampleorder = tkinter.BooleanVar()
            self.check_wo_option = tkinter.Checkbutton(self.frame, text="Sample Order", variable=self.is_sampleorder,
                                                       onvalue=True, offvalue=False, state='disable')
            self.check_wo_option.grid(column=1, row=row, columnspan=1, sticky=tkinter.W)
            self.is_sampleorder.set(False)

        tkinter.Label(self.frame, text="Failure Code").grid(column=2, row=row, sticky=tkinter.W)
        self.show_fail_code = tkinter.StringVar()
        eny_failcode = tkinter.Entry(self.frame, width=30, textvariable=self.show_fail_code, state='readonly')
        eny_failcode.grid(column=3, row=row, sticky=tkinter.W, ipady=2, pady=2, columnspan=8)

        # line 8
        self.text_frame = tkinter.LabelFrame(self.frame, text='QA_Info', fg='blue')
        self.text_frame.grid(row=8, column=0, columnspan=12, sticky=tkinter.W)
        self.text_info = scrolledtext.ScrolledText(self.text_frame, width=71, height=22)
        self.text_info.grid(row=0, column=0, sticky=tkinter.N, pady=3)

        # ######Module Info frame#########
        module_frame = tkinter.LabelFrame(self.frame, text='Module Info', fg='blue')
        module_frame.grid(row=0, column=13, rowspan=10, columnspan=2, padx=5, sticky=tkinter.NW)
        tkinter.Button(module_frame, text='Get Module Info', command=self.show_module_info).grid(row=0, column=0)
        self.module_info = tkinter.Text(module_frame, width=30, height=11)
        self.module_info.grid(row=1, column=0, pady=5, padx=5, sticky=tkinter.W)
        Label_rev = tkinter.Label(self.frame, text='Rev: ' + self.data.version, fg='blue')
        Label_rev.grid(row=8, column=14, pady=1, padx=5, sticky=tkinter.NE)

        if self.data.pro_info_zh['site'] == 'ZH':
            self.is_automove = tkinter.BooleanVar()
            self.check_automove = tkinter.Checkbutton(self.frame, text="Auto Move OPC", variable=self.is_automove,
                                                      onvalue=True, offvalue=False, state='disable')
            self.check_automove.grid(row=8, column=13, sticky=tkinter.NW)
            if data.com_config['dut']['auto_move'] == '1':
                self.is_automove.set(True)
            else:
                self.is_automove.set(False)

        if self.data.pro_info_zh['site'] == '$$$':             # 屏蔽QA Engineer特殊权限按钮的显示
            tkinter.Button(self.frame, text='QA Engineer', command=self.qaverify_engineer).grid(row=8, column=14, pady=2, padx=2, sticky=tkinter.SE)
            self.qa_engineer = tkinter.StringVar()
            self.eny_engineer = tkinter.Entry(self.frame, textvariable=self.qa_engineer, width=12, state='readonly')
            self.eny_engineer.grid(column=13, row=8, sticky=tkinter.SE, ipady=2, pady=2, padx=2)
            self.eny_engineer.grid_remove()                    # 让eny_engineer输入框隐藏

    def qaverify_engineer(self):
        inputDialog = gui_popup.MyDialog()
        self.root.wait_window(inputDialog)                            # 这一句很重要！！！
        userinfo = inputDialog.userinfo
        try:
            access_id = self.data.fusion_a.check_user(userinfo[0], userinfo[1])
        except:
            access_id = None
        if access_id == 5:                                           # 预留给工程师的特殊权限
            self.cs_load_btn.config(state='normal')
            self.ts_load_btn.config(state='normal')
            self.fail_reason = userinfo[0] + ' login special access: '
            self.qa_engineer.set(userinfo[0])
            self.eny_engineer.grid()                          # 让eny_engineer输入框显示
            self.qa_spec_access = True

    def connect_dut(self):
        if self.data.dut_obj is None:          # connect the dut via usb-hid port if dut_obj isn't connected.
            self.dut.connect_dut()
            time.sleep(1)

    def show_module_info(self):
        test_status =self.dut.label_result['text']
        if test_status != 'Testing...':
            try:
                self.connect_dut()
            except:
                msg.showwarning(title='show warning', message='连接测试座失败/test socket connection failure')
                print('连接测试座失败/test socket connection failure')
                return False
            if not self.unlock():
                return False
            self.read_module_info()
        else:
            print('The module is Testing...')

    def read_module_info(self):
        self.module_info.delete(0.0, tkinter.END)
        data = self.data.dut_obj.get_module_info()
        self.module_data = data
        info = [item + ':' + data[item] for item in ['vendor_pn', 'vendor_name', 'vendor_sn', 'datecode']]
        fw_info = self.data.dut_obj.get_fw_pn_info()
        fw_version = '.'.join(char for char in [fw_info[1][0], fw_info[1][2], fw_info[1][4]]) + fw_info[1][6:]
        info.append('MCU FW Ver: ' + fw_version)
        ddm_info = self.data.dut_obj.get_ddm_module()
        info.append('DDM Temp:  ' + '{:.2f}'.format(ddm_info['temp_ddm']) + 'C')
        info.append('DDM Vcc:' + '{:.2f}'.format(ddm_info['vcc_ddm']) + 'v')
        ddm_info = self.data.dut_obj.get_ddm_lane()[0]
        info = info + [item + ':' + '{:.2f}'.format(ddm_info[item]) + 'dBm' for item in
                       ['Tx_pwr_dbm', 'Rx_pwr_dbm']]
        self.module_info.insert(0.0, '\r\n'.join(info))
        return info

    def module_sn_check(self):
        result = []
        self.read_module_info()
        module_sn = self.module_data.get('vendor_sn')
        input_sn = self.sn.get()
        if module_sn == input_sn:
            self.text_info.insert(tkinter.END, 'Pass: Module SN check passed. \n')
        else:
            self.text_info.insert(tkinter.END, 'Fail: Module SN check failed. \n')
            self.fail_code.append('QA77')
            result.append(False)

        if self.data.pro_info_zh['site'] == 'ZH':                       # site为ZH是，增加检查Datacode.
            module_datecode = '20' + self.module_data.get('datecode')
            fusion_datecode = self.barcode_info['Datecode'][0]
            fusion_datecode_errID = self.barcode_info['Datecode'][1]    # 返回错误代码为0或者1
            if fusion_datecode_errID == 0:                              # fusion系统返回有datacode时，比较系统和模块的两个datecode值相同
                if module_datecode == fusion_datecode:
                    self.text_info.insert(tkinter.END, 'Pass: DateCode check passed. \n')
                else:
                    self.text_info.insert(tkinter.END, 'Fail: DateCode check failed. \n')
                    self.fail_code.append('QA11')
                    result.append(False)
            else:                                                      # 条码为一维码时，只检查模块的datacode为数字
                if module_datecode.isdecimal():
                    self.text_info.insert(tkinter.END, 'Pass: DateCode check passed. \n')
                else:
                    self.text_info.insert(tkinter.END, 'Fail: DateCode check failed. \n')
                    self.fail_code.append('QA11')
                    result.append(False)
        self.text_frame.update()
        if False not in result:
            return True
        else:
            return False

    def sn_wo_pn_matching(self):
        # 依据输入检查有没有产品信息，如果没有，直接返回False终止测试。
        # 如果有产品信息，检查WO,PN 是否与输入正确， 如果不正确，返回False终止测试。
        # 如果WO为DJ, Verify,GRR, 则不检查WO。
        result = []
        product_bool, self.productinfo = self.fusion_a.get_productinfo(self.sn.get())
        if product_bool:
            self.subSN = self.productinfo['Container']
            self.subsn_var.set(self.subSN)
            if self.wo.get() not in ['DJ', 'VERIFY', 'GRR']:  # wo为这3个项目时就不进行pn,sn匹配，以及检查工序这些操作
                if self.productinfo['MfgOrder'] != self.wo.get():
                    print('SN 与 WO 匹配失败')
                    msg.showwarning('Warning', 'SN 与 WO 匹配失败')
                    # self.fail_code.append('QA05')
                    result.append(False)
                if self.productinfo['Product'] != self.pn.get():
                    print('Warning', 'SN 与 PN 匹配失败')
                    msg.showwarning('Warning', 'SN 与 PN 匹配失败')
                    # self.fail_code.append('QA05')
                    result.append(False)
                if 'QA Verify' not in self.productinfo['Spec']:
                    msg.showwarning('Warning', '工序错误, 当前工序为 QA Verify\r\n系统工序为\r\n' + self.productinfo['Spec'])
                    print('工序错误, 当前工序为 QA Verify, 系统工序为 ' + self.productinfo['Spec'])
                    result.append(False)
        else:
            print('从OPC获取产品信息失败，有可能是SN输入错误')
            msg.showwarning('show warning', '从OPC获取产品信息失败，有可能是SN输入错误')
            result.append(False)
        if False not in result:
            return True
        else:
            return False

    def string_format(self, data):
        if data is not None:
            return data.strip(' ' + '\n' + '\t' + '\r')

    def read_barcode_info(self):
        self.sn.set(self.string_format(self.sn.get()))
        if (self.sn.get() == '') or (self.pn.get() == ''):
            print('Input SN or PN is empty.')
            return
        info = self.fusion_a.get_barcode_info(self.sn.get(), self.pn.get())
        self.barcode_info.update({'SN': info['SN'], 'Datecode': info['Datecode']})
        self.sn.set(self.barcode_info['SN'][0])

    def update_sn(self, event=None):
        self.read_barcode_info()
        self.btn_qa_verify.focus_set()

    def update_pn_trigger(self, event=None):
        self.eny_wo.focus_set()         # 把焦点转移到另外一个控件，使PN控件触发validate事件

    def get_socket_count_trigger(self, event=None):
        self.eny_sn.focus_set()         # 把焦点转移到另外一个控件，使EVBSN控件触发focusout事件

    # def wo_check_trigger(self, event=None):
    #    self.eny_evb_sn.focus_set()

    def wo_check(self, event=None):
        wo = self.string_format(self.wo.get())
        self.wo.set(wo.upper())
        if self.wo.get() == '':
            print('Input WO is empty')
            return
        if self.fusion_a.get_wo_info(self.wo.get()) == 1:
            self.is_sampleorder.set(True)
        else:
            self.is_sampleorder.set(False)

    def update_pn(self, event=None):
        self.code_spec_file.set('')
        self.test_spec_file.set('')
        self.pn.set(self.string_format(self.pn.get()))  # 消除输入的回车符号, 并赋值给toppn
        if self.pn.get() == '':
            return False
        try:
            info = self.fusion_a.get_bom_info(pn=self.pn.get(), component_type='EEPROM')
        except:
            msg.showerror(title='show error', message='PN is wrong')
            return False
        self.verify_result['CodeSpec'] = 'ver' + info[3]  # update the codepspec in the verify_result
        if info is not None:
            cs_filename = 'Q:\\OCP Released Code Specifications\\' + info[0] + '\\' + info[1] + '_ver' + info[
                3] + '.txt'
            # print(cs_filename)
            if os.path.exists(cs_filename):
                self.code_spec_file.set(cs_filename)
            else:
                print('CodeSpec file is not exist in the Q disk directory')
        else:
            print("Can't Get BOM EEPROM Infomation with the PN")
        self.subpn = self.fusion_a.get_subpn_by_toppn(self.pn.get())
        info = self.fusion_a.get_bom_info(pn=self.subpn, component_type='TESTSP')
        if len(info) > 0:
            ts_filename = 'Q:\\Automation Test Specifications\\oplink\\' + info[1] + '_Ver' + info[3] + '.xlsx'
            if os.path.exists(ts_filename):
                self.test_spec_file.set(ts_filename)
            else:
                print('TestSpec file is not exist in the Q disk directory')
        else:
            print("Can't Get BOM TESTSP Infomation with the PN")
        return True

    def get_socket_count(self, event=None):
        self.evb_sn.set(self.string_format(self.evb_sn.get()))
        evb_sn = self.evb_sn.get()
        if evb_sn != '':
            usecount = self.fusion_a.get_socket_info(evb_sn)
            if usecount >= 1000:
                msg.showwarning(title='Warning', message='EVB board 使用次数 >= 1000, 请替换.')
                self.evb_count.set('')
                return False
            else:
                self.evb_count.set(usecount)
                return True
        else:
            self.evb_count.set('')
            return False

    def evb_count_check(self):
        evb_sn = self.evb_sn.get()
        if evb_sn != '':
            usecount = self.fusion_a.get_socket_info(evb_sn)
            if usecount >= 1000:
                msg.showwarning(title='Warning', message='EVB board 使用次数 >= 1000, 请替换.')
                return False
            else:
                self.fusion_a.update_socket_count(evb_sn, usecount + 1)
                self.evb_count.set(usecount + 1)
                return True
        else:
            print('EVB SN is blank, Please input EVB SN.')
            return False

    def sel_code_spec(self):
        if self.data.pro_info_zh['site'] == 'GUAD':
            self.code_spec_file.set(askopenfilename())
        else:                                       # manual load code spec in ZH
            data = self.string_format(askstring('', 'Please input reason for loading code spec manually'))
            if data != '' and data is not None:
                self.code_spec_file.set(askopenfilename())
                self.load_cs_manually_reason = 'Load CS manually reason: ' + data + '. '

    def sel_test_spec(self):
        if self.data.pro_info_zh['site'] == 'GUAD':
            pass
        else:                                      # manual load test spec in ZH
            data = self.string_format(askstring('', 'Please input reason for loading test spec manually'))
            if data != '' and data is not None:
                self.test_spec_file.set(askopenfilename())
                self.load_ts_manually_reason = 'Load TS manually reason: ' + data + '. '

    def get_cs_filename(self):
        filename = ''
        fileexist = False
        entry_cs_file = self.code_spec_file.get().strip()
        if entry_cs_file == '':
            pass
        else:
            filename = entry_cs_file
            if os.path.exists(filename):
                fileexist = True
            else:
                print('CodeSpec file is not exist')
        return filename, fileexist

    def check_input_info(self):
        if '' in [self.pn.get(), self.sn.get(), self.wo.get(), self.code_spec_file.get()]:
            self.text_info.insert(tkinter.END, 'Fail: Check pn/sn/wo/CS input is blank.\n')
            return False
        if (self.data.pro_info_zh['site'] == 'ZH') and (self.evb_sn.get() == ''):
            self.text_info.insert(tkinter.END, 'Fail: Check evbSN input is blank.\n')
            return False
        return True

    def get_data_from_cs_file(self, filename):
        # file = open(self.code_spec_file.get(), 'rt')     # change the file source
        file = open(filename, 'rt')
        data_cs = []
        i = 0
        table_data = []
        while True:
            # if i % 8 == 0:
            #    table_data = []
            #    count = 1
            line = file.readline()
            if not line:
                break
            for val in line.strip('\n').split(' '):
                if val not in [' ', '']:
                    table_data.append(val)
            if (i + 1) % 8 == 0:
                data_cs.append(table_data)
                table_data = []
            i += 1
            # count += 1
        file.close()
        return data_cs

    def eeprom_check(self):
        page_list = (
            "LP_00H", "UP_00H", "UP_01H", "UP_02H", "UP_03H", "UP_04H", "UP_13H", "UP_28H", "UP_29H", "UP_2AH",
            "UP_2BH",
            "UP_30H", "UP_41H", "UP_C0H", "UP_C1H", "UP_C2H", "UP_C3H", "UP_C4H", "UP_C5H")
        data_dut = []
        a = 0
        for page in page_list:
            if page == "LP_00H":
                data_dut.append(self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0, 128))
            else:
                self.data.dut_obj.page_select(int(page[3:5], 16))    # 将page_list的字符串的3，4，5的16进制数转换成16位int
                data_dut.append(self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x80, 128))
            list_item = 'S' + f'{a+1}'                               # 将寄存器数据保存至数据表的S1~S19
            str1 = ''
            for i in range(len(data_dut[a])):
                element = '{:02x}'.format(data_dut[a][i]).upper()
                str1 += element
            self.verify_result[list_item] = str1
            a += 1
        filename, fileexist = self.get_cs_filename()
        data_cs = []
        if fileexist:
            data_cs = self.get_data_from_cs_file(filename)
        result = []
        for page, dut, cs in zip(page_list, data_dut, data_cs):
            idx = 0
            for val_cs, val_dut in zip(cs, dut):
                if val_cs == '--':
                    result.append(True)
                else:
                    if int(val_cs, 16) == val_dut:
                        result.append(True)
                    else:
                        result.append(False)
                        if page == "LP_00H":
                            addr = str(idx)
                        else:
                            addr = str(128 + idx)
                        self.text_info.insert(tkinter.END,
                                              'Fail: EEprom data check failed.' + page + ':' + addr + ', cs value is 0x' + val_cs + ', dut value is 0x' + '{:02x}'.format(
                                                  val_dut).upper() + '\n')
                        self.text_frame.update()
                idx += 1
        if False not in result:
            self.text_info.insert(tkinter.END, 'Pass: EEprom data check passed.\n')
            self.text_frame.update()
            return True
        else:
            self.code_list.append('01')
            self.fail_code.append('QA06')
            return False

    def checksum_check(self):
        result = []
        self.data.dut_obj.page_select(0x00)
        data = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x80, 128)
        if data[94] == sum(data[0:94]) & 0xFF:  # UP00h byte DEh, Page Checksum of bytes 128-221
            result.append(True)
        else:
            result.append(False)
            self.text_info.insert(tkinter.END, 'Fail: Page:UP00H checksum failed.\n')
            self.text_frame.update()
        self.data.dut_obj.page_select(0x01)
        data = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x80, 128)
        if data[127] == sum(data[2:127]) & 0xFF:  # UP01h byte FFh, Page Checksum of bytes 130-254
            result.append(True)
        else:
            result.append(False)
            self.text_info.insert(tkinter.END, 'Fail: Page:UP01H checksum failed.\n')
            self.text_frame.update()
        self.data.dut_obj.page_select(0x02)
        data = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x80, 128)
        if data[127] == sum(data[0:127]) & 0xFF:  # UP02h byte FFh, Page Checksum of bytes 128-254
            result.append(True)
        else:
            result.append(False)
            self.text_info.insert(tkinter.END, 'Fail: Page:UP02H checksum failed.\n')
            self.text_frame.update()
        self.data.dut_obj.page_select(0x04)
        data = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x80, 128)
        if data[127] == sum(data[0:127]) & 0xFF:  # UP04h byte FFh, Page Checksum of bytes 128-254
            result.append(True)
        else:
            result.append(False)
            self.text_info.insert(tkinter.END, 'Fail: Page:UP04H checksum failed.\n')
            self.text_frame.update()
        if False not in result:
            self.text_info.insert(tkinter.END, 'Pass: Checksum check passed.\n')
            self.text_frame.update()
            return True
        else:
            self.code_list.append('02')
            self.fail_code.append('QA06')
            return False

    def page_eeprom_info_check(self):
        self.data.dut_obj.page_select(0x28)
        table_28 = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(128, 128)
        self.data.dut_obj.page_select(0x29)
        table_29 = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(128, 128)
        if (table_28 != [0] * 128) and (table_29 != [0] * 128):
            self.text_info.insert(tkinter.END, 'Pass: Table 0x28/0x29 EEprom data check passed. \n')
            self.text_frame.update()
            return True
        else:
            if table_28 == [0] * 128:
                self.text_info.insert(tkinter.END, 'Fail: Table 0x28 EEprom data check failed. \n')
            if table_29 == [0] * 128:
                self.text_info.insert(tkinter.END, 'Fail: Table 0x29 EEprom data check failed. \n')
            self.text_frame.update()
            self.code_list.append('03')
            self.fail_code.append('QA29')
            return False

    def loop_check(self):
        loop_status = self.data.dut_obj.get_loop_status()
        if loop_status['TX_VG'] == 'ON' and loop_status['RX_OA'] == 'ON':
            self.text_info.insert(tkinter.END, 'Pass: Tx VG/ Rx OA Loop status check passed.\n')
            self.text_frame.update()
            return True
        else:
            if loop_status['TX_VG'] == 'OFF':
                self.text_info.insert(tkinter.END, 'Fail: Tx VG loop check failed.\n')
            # if loop_status['TX_VOA'] == 'OFF':
            #     self.text_info.insert(tkinter.END, 'Tx VOA loop check failed.\n')
            if loop_status['RX_OA'] == 'OFF':
                self.text_info.insert(tkinter.END, 'Fail: Rx OA loop check failed.\n')
            self.text_frame.update()
            self.code_list.append('04')
            self.fail_code.append('QA112')
            return False

    def rx_los_check_flag_check(self):
        rx_los_check_flag = self.data.dut_obj.get_rx_los_check_flag()
        if rx_los_check_flag == 0x00:
            self.text_info.insert(tkinter.END, 'Pass: Rx los check flag check passed.\n')
            self.text_frame.update()
            return True
        else:
            self.text_info.insert(tkinter.END, 'Fail: Rx los check flag check failed.\n')
            # self.text_info.insert(tkinter.END,
            #                      'Rx los check flag is 0x' + '{:02x}'.format(rx_los_check_flag).upper() + '.\n')
            print('Rx los check flag is 0x' + '{:02x}'.format(rx_los_check_flag).upper())
            self.text_frame.update()
            self.code_list.append('05')
            self.fail_code.append('QA93')
            return False

    def dsp_mode_check(self):
        if self.data.dut_obj.get_module_mission_mode() == 0x00:
            self.text_info.insert(tkinter.END, 'Pass: Check dsp mode passed. \n')
            self.text_frame.update()
            return True
        else:
            # print('DSP mode is: ', self.data.dut_obj.get_module_mission_mode())
            self.text_info.insert(tkinter.END, 'Fail: Check dsp mode failed. \n')
            self.text_frame.update()
            self.code_list.append('06')
            self.fail_code.append('QA104')
            return False

    def abc_check(self):
        result = []
        self.data.dut_obj.page_select(0xC1)
        data = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x92, 24)
        if data == [0xFF] * 24 or data == [0] * 24:
            self.text_info.insert(tkinter.END, 'Fail: ABC operation point check failed.\n')
            self.text_frame.update()
            result.append(False)
        else:
            result.append(True)
        self.data.dut_obj.page_select(0xC5)
        data = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x80, 48)
        ratio_list = []
        ratio_result = []
        for i in range(0, 48, 4):
            t_ratio = struct.unpack('<f', bytearray([data[i + 3], data[i + 2], data[i + 1], data[i]]))
            ratio_list.append(t_ratio[0])
            if - 10 <= float(t_ratio[0]) <= 10:
                ratio_result.append(True)
            else:
                ratio_result.append(False)
        if False in ratio_result:
            self.text_info.insert(tkinter.END, 'Fail: ABC realtime ratio check failed.\n')
            # self.text_info.insert('ABC realtime ratio value is:' + '_'.join(ratio_list) + '\n')
            print('ABC realtime ratio value is:' + '_'.join(ratio_list))
            self.text_frame.update()
            result.append(False)
        else:
            result.append(True)
        if self.data.dut_obj.get_abc_mode() == 'Normal':
            result.append(True)
        else:
            self.text_info.insert(tkinter.END, 'Fail: ABC mode check failed.\n')
            self.text_frame.update()
            result.append(False)
        if False not in result:
            self.text_info.insert(tkinter.END, 'Pass: ABC realtime ratio / op point / mode check passed.\n')
            self.text_frame.update()
            return True
        else:
            self.code_list.append('07')
            self.fail_code.append('QA110')
            return False

    def alarm_warning_check(self):
        result = []
        # clear all latch register
        self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x09, 1)  # temp/vcc alarm/warning flag
        self.data.dut_obj.page_select(0x11)
        self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(135, 18)  # Lane-Specific Tx/Rx Flags
        self.data.dut_obj.page_select(0x2C)
        self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x80, 1)  # VDM1/VDM2 alarm/warning flags
        time.sleep(2)
        # check alarm/ warning flag
        val = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x09, 1)[0]
        if val != 0:
            self.text_info.insert(tkinter.END, 'Fail: Temp/Vcc alarm/warning check failed.\n')
            self.text_frame.update()
            result.append(False)
        self.data.dut_obj.page_select(0x11)
        tx_item = ['Fault', 'Los', 'CDR LOL', 'Adaptive Input Eq', 'output power High Alarm', 'output power Low alarm',
                   'output power High warning', 'output power Low warning']
        for val, item in zip(self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(135, 8), tx_item):
            if item in ['Los', 'CDR LOL']:
                # check_data = 0x01
                continue  # skip checking tx los and CDR LOL
            else:
                check_data = 0x00
            if val & 0x01 != check_data:
                self.text_info.insert(tkinter.END, 'Tx ' + item + ' check failed.\n')
                self.text_frame.update()
                result.append(False)
            else:
                result.append(True)
        rx_item = ['LOS', 'CDR LOL', 'input power Low alarm', 'input power Low warning']
        data = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(147, 6)
        for val, item in zip([data[0], data[1], data[3], data[5]], rx_item):
            if (val & 0x01) != 1:
                self.text_info.insert(tkinter.END, 'Fail: Rx ' + item + ' check failed.\n')
                self.text_frame.update()
                result.append(False)
            else:
                result.append(True)
        self.data.dut_obj.page_select(0x2C)
        val = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x80, 1)[0]
        if (val & 0x0F) != 0x00:
            self.text_info.insert(tkinter.END, 'Fail: VDM1 TEC current alarm/warning check failed.\n')
            self.text_frame.update()
            result.append(False)
        else:
            result.append(True)
        if (val >> 4) != 0x00:
            self.text_info.insert(tkinter.END, 'Fail: VDM2 Laser temp alarm/warning check failed.\n')
            self.text_frame.update()
            result.append(False)
        else:
            result.append(True)
        if False not in result:
            self.text_info.insert(tkinter.END, 'Pass: Module alarm/warning check passed.\n')
            self.text_frame.update()
            return True
        else:
            self.code_list.append('08')
            self.fail_code.append('QA08')
            return False

    def osnr_tuning_check(self):
        self.data.dut_obj.page_select(0xC0)
        if self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x8B, 1)[0] == 0xAA:
            self.text_info.insert(tkinter.END, 'Pass: OSNR calibration flag check passed.\n')
            self.text_frame.update()
            return True
        else:
            self.text_info.insert(tkinter.END, 'Fail: OSNR calibration flag check failed.\n')
            self.text_frame.update()
            self.code_list.append('09')
            self.fail_code.append('QA111')
            return False

    def tx_maximum_power_check(self):
        self.data.dut_obj.page_select(0x04)
        val1 = self.data.dut_obj.my_i2c.read_bytes_maximum_58bytes(0xC8, 2)
        self.data.dut_obj.page_select(0xC1)
        val2 = self.data.dut_obj.my_i2c.read_bytes_maximum_58bytes(0xF4, 2)
        if (val1 == val2) and (val1 != [0x00, 0x00]) and (val2 != [0x00, 0x00]):
            self.text_info.insert(tkinter.END, 'Tx maximum power setting check passed. \n')
            self.text_frame.update()
            return True
        else:
            self.text_info.insert(tkinter.END, 'Tx maximum power setting check failed. \n')
            self.text_frame.update()
            return False

    def topcodespec_ver_check(self):
        self.data.dut_obj.page_select(0xC0)
        top_cs = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0xFE, 1)
        self.text_info.insert(tkinter.END, 'DUT top codespec version is: ' + str(top_cs[0]) + '\n')
        PN = self.pn.get()
        data = self.fusion_a.get_bom_info(pn=PN, component_type='EEPROM')
        cs_version = data[3]
        self.text_info.insert(tkinter.END, 'Aiges codespec version is: ' + str(top_cs[0]) + '\n')
        if str(top_cs[0]) == cs_version:
            self.text_info.insert(tkinter.END, 'Top Codespec version check passed.\n')
            return True
        else:
            self.text_info.insert(tkinter.END, 'Top Codespec version check failed.\n')
            return False

    def unlock(self):
        fail_prompt = '模块解锁失败，可能是模块没有装配合适./unlock module failure, It is maybe the insertion issue'
        try:
            if self.data.dut_obj.unlock_module('Oplink_PWD_level') == 'true':
                return True
            else:
                print(fail_prompt)
                msg.showwarning('Warning', fail_prompt)
                return False
        except:
            print(fail_prompt)
            msg.showwarning('Warning', fail_prompt)
            return False

    def get_fw_info_from_agile(self):
        toppn = self.pn.get()
        subpn = self.fusion_a.get_subpn_by_toppn(toppn)
        data = self.fusion_a.qry_zhu_bomtree(subpn)
        for idx, row in data.iterrows():
            ocp_comp_type = row.get('OCP_COMPONENT_TYPE')
            if ocp_comp_type is None:
                ocp_comp_type = ''
            ocp_comp_desc = row.get('OCP_COMPONENT_ITEM_DESC').upper()
            if ocp_comp_desc is None:
                ocp_comp_desc = ''
            if ('FRMWRE' in ocp_comp_type) and ('APPLICATION' in ocp_comp_desc):
                self.mcu_fw_pn = row.get('OPLK_COMPONENT_ITEM')
                self.mcu_fw_ver = row.get('DOC_REV')
            if ('FRMWRE' in ocp_comp_type) and ('BOOTLOADER' in ocp_comp_desc):
                self.bootloader_fw_pn = row.get('OPLK_COMPONENT_ITEM')
                self.bootloader_fw_ver = row.get('DOC_REV')

    def ask_fw_info_check_fail_reason(self):
        result = []
        if self.qa_spec_access:
            if not self.mcu_fw_ver_spec_access:
                if msg.askyesno(title='确认是否Skip此测试', message='MCU FW Version Check is fail, 需要Pass这项测试吗？'):
                    self.mcu_spec_reason = self.string_format(
                        askstring('', 'Please input reason for pass mcu fw version check manually'))
                    if (self.mcu_spec_reason != '') and (self.mcu_spec_reason is not None):
                        self.mcu_fw_ver_spec_access = True
                        self.fail_reason = self.fail_reason + 'Pass mcu fw version check reason: ' + self.mcu_spec_reason + '. '
                        self.text_info.insert(tkinter.END, 'Pass: MCU FW Version check passed.\n')
                        result.append(True)
                    else:
                        self.text_info.insert(tkinter.END, 'Fail: MCU FW Version check failed.\n')
                        result.append(False)
                else:
                    self.text_info.insert(tkinter.END, 'Fail: MCU FW Version check failed.\n')
                    result.append(False)
            else:
                self.fail_reason = self.fail_reason + 'Pass mcu fw version check reason: ' + self.mcu_spec_reason + '. '
                self.text_info.insert(tkinter.END, 'Pass: MCU FW Version check passed.\n')
                result.append(True)

    def fw_info_check(self):
        result = []
        if self.data.pro_info_zh['site'] == 'ZH':        # site is Zhuhai
            self.get_fw_info_from_agile()
            mcu_fw_server = self.mcu_fw_pn + '_' + self.mcu_fw_ver[3:]
            boot_fw_server = self.bootloader_fw_ver[3:]
        else:                                            # site is GUAD
            info_all = self.get_fw_info_GUAD()
            mcu_fw_server = info_all[0][1] + '_' + info_all[0][2]
            boot_fw_server = info_all[0][3]

        fw_info = self.data.dut_obj.get_fw_pn_info()
        fw_version = '.'.join(char for char in [fw_info[1][0], fw_info[1][2], fw_info[1][4]]) + fw_info[1][6:]
        fw_data_module = fw_info[0] + '_' + fw_version
        # dsp_fw_ver = self.data.dut_obj.get_dsp_fw_ver()
        # self.text_info.insert(tkinter.END, 'DSP FW Info:' + dsp_fw_ver + '\n')
        self.data.dut_obj.page_select(0xE8)
        rsp_int = self.data.dut_obj.my_i2c.read_bytes_maximum_128bytes(0x80, 97)
        image_a_version = '.'.join([str(val) for val in [rsp_int[11], rsp_int[10], rsp_int[9], rsp_int[8]]])
        image_a_valid_flag = rsp_int[7]
        image_b_version = '.'.join([str(val) for val in [rsp_int[23], rsp_int[22], rsp_int[21], rsp_int[20]]])
        image_b_valid_flag = rsp_int[19]
        # bootloader_version = '.'.join([str(val) for val in [rsp_int[87], rsp_int[86], rsp_int[85], rsp_int[84]]])
        bootloader_version = str(rsp_int[87]) + '.' + str(rsp_int[86]) + '.' + str(rsp_int[84])
        print('MCU FW Info from module:' + fw_data_module)
        print('MCU FW Info from server: ' + mcu_fw_server)
        if mcu_fw_server == fw_data_module:
            self.text_info.insert(tkinter.END, 'Pass: MCU FW Version check passed.\n')
            result.append(True)
        else:
            self.text_info.insert(tkinter.END, 'Fail: MCU FW Version check failed.\n')
            result.append(False)

        print('Bootloader version from module:' + bootloader_version)
        print('Bootloader version from server: ' + boot_fw_server)
        if boot_fw_server == bootloader_version:
            self.text_info.insert(tkinter.END, 'Pass: Bootloader Version check passed.\n')
            result.append(True)
        else:
            self.text_info.insert(tkinter.END, 'Fail: Bootloader Version check failed.\n')
            result.append(False)
        '''
        print('Image A version:' + image_a_version)
        print('Image A valid flag:' + '{:02x}'.format(image_a_valid_flag))
        print('Image B version:' + image_b_version)
        print('Image B valid flag:' + '{:02x}'.format(image_b_valid_flag))
        '''
        if (image_a_version == image_b_version) and (image_a_valid_flag == 0x01) and (image_b_valid_flag == 0x01):
            self.text_info.insert(tkinter.END, 'Pass: Image A/B version and valid flag check passed.\n')
            result.append(True)
        else:
            self.text_info.insert(tkinter.END, 'Fail: Image A/B version and valid flag check failed.\n')
            result.append(False)
        self.text_frame.update()
        self.verify_result['Firmware'] = fw_data_module + ', bootloader:' + bootloader_version
        if False not in result:
            return True
        else:
            self.fail_code.append('QA02')
            return False
        # if (fw_info[1] == image_a_version) and (image_a_valid_flag == 0x01) and (image_b_valid_flag == 0x00):
        #     self.text_info.insert(tkinter.END, 'Image A/B version and valid flag check passed.\n')
        #     self.text_frame.update()
        #     return True
        # elif (fw_info[1] == image_b_version) and (image_b_valid_flag == 0x01) and (image_a_valid_flag == 0x00):
        #     self.text_info.insert(tkinter.END, 'Image A/B version and valid flag check passed.\n')
        #     self.text_frame.update()
        #     return True
        # else:
        #     self.text_info.insert(tkinter.END, 'Image A/B version and valid flag check failed.\n')
        #     self.text_frame.update()
        #     return False

    def dut_state_check(self):
        if not self.data.dut_obj.check_module_ready():
            self.text_info.insert(tkinter.END, 'Fail: Check module state failed. \n')
            self.text_frame.update()
            self.fail_code.append('QA113')
            return False
        else:
            self.text_info.insert(tkinter.END, 'Pass: Check module state passed.\n')
            self.text_frame.update()
            return True

    def get_tenvid_from_ts(self, sheet_prefix):
        testspec_file = self.test_spec_file.get()
        tenv_spec = {'RT': True, 'LT': True, 'HT': True}
        for key, value in tenv_spec.items():
            sheetname = sheet_prefix + key
            try:
                df = pd.read_excel(testspec_file, sheet_name=sheetname)
            except ValueError as err:
                print(err)
                tenv_spec.update({key: False})
        return tenv_spec

    def check_3T_result(self, test_result, test_type):  # check 3T result sub function
        if test_result['RT'][0] and test_result['LT'][0] and test_result['HT'][0] and \
                (test_result['RT'][1] < test_result['LT'][1]) and (test_result['RT'][1] < test_result['HT'][1]):
            self.text_info.insert(tkinter.END, 'Pass: ' + test_type + ' 3T test result check passed. \n')
            self.text_frame.update()
            return True
        else:
            self.text_info.insert(tkinter.END, 'Fail: ' + test_type + ' 3T test result check failed. \n')
            self.text_frame.update()
            self.fail_code.append('QA03')
            if test_type == 'All Channel':
                self.code_list.append('11')                # GUAD fail code list
            if test_type == 'OSNR':
                self.code_list.append('12')
            return False

    def check_RT_LT_result(self, test_result, test_type):  # check RT&LT result
        if test_result['RT'][0] and test_result['LT'][0] and (test_result['RT'][1] < test_result['LT'][1]):
            self.text_info.insert(tkinter.END, 'Pass: ' + test_type + ' 2T test result check passed. \n')
            self.text_frame.update()
            return True
        else:
            self.text_info.insert(tkinter.END, 'Fail: ' + test_type + ' 2T test result check failed. \n')
            self.text_frame.update()
            self.fail_code.append('QA03')
            return False

    def check_RT_HT_result(self, test_result, test_type):  # check RT&LT result
        if test_result['RT'][0] and test_result['HT'][0] and (test_result['RT'][1] < test_result['HT'][1]):
            self.text_info.insert(tkinter.END, 'Pass: ' + test_type + ' 2T test result check passed. \n')
            self.text_frame.update()
            return True
        else:
            self.text_info.insert(tkinter.END, 'Fail: ' + test_type + ' 2T test result check failed. \n')
            self.text_frame.update()
            self.fail_code.append('QA03')
            return False

    def check_RT_result(self, test_result, test_type):
        if test_result['RT'][0]:
            self.text_info.insert(tkinter.END, 'Pass: ' + test_type + ' 1T test result check passed. \n')
            self.text_frame.update()
            return True
        else:
            self.text_info.insert(tkinter.END, 'Fail: ' + test_type + ' 1T test result check failed. \n')
            self.text_frame.update()
            self.fail_code.append('QA03')
            return False

    def compare_time_sub_eeprom_and_final_test(self, last_eeprom_record, data_list):
        rt_datalist = []
        result = []
        for i in range(len(data_list)):
            mfg_record = data_list[i]['TestResultDtBySnProcess']
            if mfg_record['Test_Area'] == 'RT':
                rt_datalist.append(mfg_record)
        last_listno = 0
        if len(rt_datalist) > 0:
            last_moveout_datetime = datetime.strptime(rt_datalist[0]['Move_Out'], '%Y-%m-%d %H:%M:%S')
            for j in range(len(rt_datalist)):
                moveout_datetime = datetime.strptime(rt_datalist[j]['Move_Out'], '%Y-%m-%d %H:%M:%S')
                if last_moveout_datetime < moveout_datetime:
                    last_moveout_datetime = moveout_datetime
                    last_listno = j
            if rt_datalist[last_listno]['Test_Result'] != 'P':
                result.append(False)
        else:
            result.append(False)
        if rt_datalist and (last_eeprom_record is not None):
            if (last_eeprom_record['Result'] == 'P') and (rt_datalist[last_listno]['TestDate'] > last_eeprom_record['DateCreated']):
                result.append(True)
            else:
                result.append(False)
        else:
            result.append(False)
        if False not in result:
            return True
        else:
            return False

    def mfg_record_result_check(self, test_type):
        default_datetime = datetime.strptime('2017-04-23 01:12:00', '%Y-%m-%d %H:%M:%S')     # set default datetime
        test_result = {'RT': [False, default_datetime], 'LT': [False, default_datetime], 'HT': [False, default_datetime]}  # 初始化Test_Result的Value, moveout_datetime
        result = []
        process = ''
        sheet_prefix = ''
        if test_type == 'All Channel':
            process = 'ACPD_Coherent_TestData'
            sheet_prefix = 'ALL CH_'
        elif test_type == 'OSNR':
            process = 'ACPD_Coherent_OSNRData'
            sheet_prefix = 'OSNR_'
        tenv_spec = self.get_tenvid_from_ts(sheet_prefix)              # 获取该测试类型在Test Spec 中定义的温度个数
        data_list = self.fusion_t.get_mfg_record(self.subSN, process)  # 获取该SN, 该测试类型在数据库中的所有测试记录
        last_sub_eeprom_record = self.fusion_a.get_last_sub_eeprom_record(self.subSN, 'EEPROM') # 获取该SN的sub-eeprom-load 的最新记录

        if test_type == 'All Channel':
            if last_sub_eeprom_record is not None:
                if self.compare_time_sub_eeprom_and_final_test(last_sub_eeprom_record, data_list):
                    result.append(True)
                    self.text_info.insert(tkinter.END,
                                          'Pass: Check Sub eeprom_download Record passed. \n')
                else:
                    self.text_info.insert(tkinter.END,
                                          'Fail: Check Sub eeprom_download Record failed. \n')
                    self.fail_code.append('QA90')
                    result.append(False)
            else:
                self.text_info.insert(tkinter.END,
                                      'Fail: Check Sub eeprom_download Record failed. \n')
                self.fail_code.append('QA90')
                result.append(False)

        for tenvid in ['RT', 'LT', 'HT']:
            tenvid_datalist = []
            for i in range(len(data_list)):
                mfg_record = data_list[i]['TestResultDtBySnProcess']             # 解析读取同一温度下所有测试记录
                if mfg_record['Test_Area'] == tenvid:
                    tenvid_datalist.append(mfg_record)
            if len(tenvid_datalist) > 0:                                         # 检查 tenvid_datalist 不为空
                last_listno = 0                                                  # 表示最新的记录在记录列表中的序号
                last_moveout_datetime = datetime.strptime(tenvid_datalist[0]['Move_Out'], '%Y-%m-%d %H:%M:%S') # 将时间字符串转换成时间格式
                for j in range(len(tenvid_datalist)):                   # 搜寻同一温度下所有测试记录的最新记录
                    moveout_datetime = datetime.strptime(tenvid_datalist[j]['Move_Out'], '%Y-%m-%d %H:%M:%S')
                    if last_moveout_datetime < moveout_datetime:
                        last_moveout_datetime = moveout_datetime
                        last_listno = j
                if tenvid_datalist[last_listno]['Test_Result'] == 'P':
                    test_result[tenvid][0] = True
                test_result[tenvid][1] = datetime.strptime(tenvid_datalist[last_listno]['Move_Out'], '%Y-%m-%d %H:%M:%S')
        if self.is_sampleorder.get():  # 如果是sample order, 则要强制检查3T
            result.append(self.check_3T_result(test_result, test_type=test_type))
        else:  # 如果不是Sample order, 则按test spec 所定义的几个T 检测
            if tenv_spec['RT'] and tenv_spec['LT'] and tenv_spec['HT']:    # 暂时只开放3T检测，以免Test Spec文件错误而漏检
                result.append(self.check_3T_result(test_result, test_type=test_type))
            else:
                print('The Test Spec has some issues, Please contact Engineer')
                result.append(False)
            '''
            # 以下为一温检测或者两温功能测试后的 QA verify 温度检测
            elif tenv_spec['RT'] and tenv_spec['LT'] and not tenv_spec['HT']:
                result.append(self.check_RT_LT_result(test_result, test_type=test_type))
            elif tenv_spec['RT'] and not tenv_spec['LT'] and tenv_spec['HT']:
                result.append(self.check_RT_HT_result(test_result, test_type=test_type))
            elif tenv_spec['RT'] and not tenv_spec['LT'] and not tenv_spec['HT']:
                result.append(self.check_RT_result(test_result, test_type=test_type))
            '''
        if False not in result:
            return True
        else:
            return False

    def upload_verify_result(self):
        self.verify_result['DateCreated'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.verify_result['PartDescription'] = self.verify_result['PartNumber'] = self.pn.get()
        self.verify_result['WorkOrder'] = self.wo.get()
        self.verify_result['NewSerialNumber'] = self.sn.get()
        self.verify_result['Operator'] = self.operator.get()
        self.verify_result['StationID'] = self.station.get()
        self.verify_result['Rev'] = self.data.version
        if self.qa_spec_access:                       # 如果启用了特殊权限，则将手动load cs和ts的原因记录到失败原因中
            if self.load_cs_manually_reason != '':
                self.fail_reason += self.load_cs_manually_reason
            if self.load_ts_manually_reason != '':
                self.fail_reason += self.load_ts_manually_reason

        self.verify_result['Failure_Reason'] = self.fail_reason
        # for k, v in self.verify_result.items():
        #    print(k, v)

        # 不管什么权限，都需要上传数据至fusion 系统
        xml_str = self.savexmlfile_zh()               # save xml result file and return xml_str
        upload_result = self.fusion_a.upload_eeprom_record(self.verify_result, xml_str)
        if upload_result:
            self.text_info.insert(tkinter.END, 'Pass: Save QA Verify Data passed. \n')
            self.text_frame.update()
            return True
        else:
            self.text_info.insert(tkinter.END, 'Fail: Save QA Verify Data failed. \n')
            self.text_frame.update()
            return False

    def check_all(self):
        qa_result = []
        self.start_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        t1_start = time.time()
        myRunCard = None
        opcode = None
        try:
            if not self.check_input_info():
                return False
            if self.data.pro_info_zh['site'] == 'ZH':
                if self.fusion_a is None:
                    try:
                        self.fusion_a = ActiveTestApi()
                    except:
                        msg.showwarning('Warning', 'ActiveTest 数据库系统连接失败')
                        return False
                if self.fusion_t is None:
                    try:
                        self.fusion_t = TestData()
                    except:
                        msg.showwarning('Warning', 'ReceiveTestData 数据库系统连接失败')
                        return False
                if not self.sn_wo_pn_matching():
                    return False
                if not self.evb_count_check():  # update EVB Board use count
                    return False
                if self.is_automove.get():
                    if not self.fusion_a.opc_move_in(self.subSN, workflowId=self.resource.get(),
                                                     employeeId=self.operator.get(), wo=self.wo.get()):
                        self.text_info.insert(tkinter.END, 'Fail: OPCenter Move IN is failed. \n')
                        return False                 # movein OP Center成功则正常往下运行，失败则提示Fail, 并停止任务
            else:           # site is GUAD
                if self.data.pro_info_zh['operator'] != 'admin':
                    myRunCard = RunCard()
                    if myRunCard.connect():
                        opcode = myRunCard.get_opcode(self.sn.get())
                        myRunCard.start_test(self.sn.get())

            try:
                self.connect_dut()
            except:
                msg.showwarning(title='Warning', message='测试座连接失败/test socket connection failure')
                print('测试座连接失败/test socket connection failure')
                return False
            if not self.unlock():
                return False

            qa_result.append(self.module_sn_check())
            qa_result.append(self.dut_state_check())
            qa_result.append(self.fw_info_check())
            qa_result.append(self.eeprom_check())
            qa_result.append(self.checksum_check())
            qa_result.append(self.page_eeprom_info_check())
            qa_result.append(self.loop_check())
            qa_result.append(self.rx_los_check_flag_check())
            qa_result.append(self.dsp_mode_check())
            qa_result.append(self.abc_check())
            qa_result.append(self.alarm_warning_check())
            qa_result.append(self.osnr_tuning_check())
            # qa_result.append(self.topcodespec_ver_check())               # topcodespec Version check, skip this step because checked the topcodespec image,
            if self.data.pro_info_zh['site'] == 'ZH':  # No need to check for GUAD. It is guaranteed by RunCard.
                qa_result.append(self.mfg_record_result_check('All Channel'))  # Check All Channel test result
                qa_result.append(self.mfg_record_result_check('OSNR'))         # Check OSNR test result
            else:
                qa_result.append(self.GUAD_record_result_check('All Channel'))  # Check All Channel test result in Guad DataCard
                qa_result.append((self.GUAD_record_result_check('OSNR')))      # Check OSNR test result in Guad DataCard

            # qa_result.append(self.tx_maximum_power_check())              # original disable this item

            self.end_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.run_time = '{:.2f}'.format(time.time() - t1_start)

            if False not in qa_result:
                self.verify_result['Reult'] = 'P'  # update result special field
            self.text_info.insert(tkinter.END, '---------------Verify Test Is Completed.--------------- \n')

            if self.data.pro_info_zh['site'] == 'ZH':        # zh site: show fail code,  upload result, and moveout OPC
                fail_code = ','.join(self.fail_code)
                self.show_fail_code.set(fail_code)
                self.verify_result['Failure_Code'] = fail_code
                try:
                    qa_result.append(self.upload_verify_result())  # upload verify test result, return success or fail
                except:
                    qa_result.append(False)
                    self.text_info.insert(tkinter.END, 'Fail: upload QA Verify Data failed. \n')
                if self.is_automove.get():  # auto move data out OP center
                    if False not in qa_result:
                        if not self.fusion_a.opc_trigger_data(self.subSN, self.operator.get(), self.wo.get()):
                            self.text_info.insert(tkinter.END, 'Fail: OPCenter trigger data is failed. \n')
                            self.text_frame.update()
                            qa_result.append(False)
                        else:
                            if not self.fusion_a.opc_move_out(self.subSN, workflowId=self.resource.get(),
                                                              employeeId=self.operator.get(), wo=self.wo.get()):
                                self.text_info.insert(tkinter.END, 'Fail: OPCenter move out is failed. \n')
                                self.text_frame.update()
                                qa_result.append(False)
            else:
                self.savexmlfile_guad()    # GUAD site save a xml file on the server
                if self.data.pro_info_zh['operator'] != 'admin':
                    if False not in qa_result:
                        myRunCard.pass_test(self.sn.get())
                        print('Advance to next step in RunCard.')
                    else:
                        self.code_list.append('10')
                        final_code_list = []
                        for code in self.code_list:
                            final_code_list.append(opcode + '-' + code)
                        print('Defect code list is: ', final_code_list)
                        print('Hold in RunCard.')
                        myRunCard.hold_after_test(self.sn.get(), final_code_list)
                        self.show_fail_code.set(final_code_list)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            qa_result.append(False)
        if False not in qa_result:
            return True
        else:
            return False

    def qa_verify(self, event=None):
        self.init_verify_result()
        self.show_fail_code.set('')               # 清空fail code 显示框
        self.text_info.delete(1.0, tkinter.END)    # 清空 Text_info 显示框
        self.module_info.delete(0.0, tkinter.END)     # 清空 module_info 显示框
        self.subsn_var.set('')
        self.dut.label_result.config(text='Testing...', fg='orange')
        if self.data.pro_info_zh['site'] == 'ZH':
            if self.barcode_info['SN'][0] == '':
                self.read_barcode_info()
        self.text_frame.update()
        if self.check_all():
            self.dut.label_result.config(text='PASS', fg='green')
        else:
            self.dut.label_result.config(text='FAIL', fg='red')
        self.text_frame.update()
        self.save_log()
        self.barcode_info = {'SN': ['', 0], 'Datecode': ['', 0]}
        self.sn.set('')
        if (self.data.pro_info_zh['site'] == 'GUAD') and (self.data.pro_info_zh['operator'] != 'admin'):
            self.pn.set('')
            self.wo.set('')
            self.code_spec_file.set('')

    def save_log(self):
        # filepath = os.getcwd() + '\\Test_Results\\'    # 获得应用程序的当前路径
        # filepath = os.path.join(os.environ['USERPROFILE'],  'Documents') + '\\Test_Results\\' #windows系统下默认路径
        if self.data.pro_info_zh['site'] == 'ZH':
            filepath = '\\\\zh-mfs-srv\\Active\\ACPDU\\' + self.station.get() + '\\Verify_Results\\'
        else:
            filepath = os.getcwd() + '\\Test_Results\\'    # 获得应用程序的当前路径
        if not os.path.exists(filepath):
            os.mkdir(filepath)
        filename = filepath + self.sn.get() + '_' + re.sub(r'[:\s-]', '_', str(datetime.now())[0:19]) + '_QA_Verify.txt'
        file = open(filename, 'wt')
        file.write(self.text_info.get(0.0, tkinter.END))
        file.close()

    # save xml result file and return xml_str
    def savexmlfile_zh(self):
        testdata = self.verify_result
        station = self.station.get()
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += '<TEST_RECORD>\n'
        for k, v in testdata.items():
            # xml_str += '   <PARA NAME = \"' + k + '\"  VALUE = \"' + v + '\" />' + '\n' #option for concatenate string
            xml_str += '   <PARA NAME = "%s"  VALUE = "%s" />\n' % (k, v)
        xml_str += '</TEST_RECORD>'
        try:
            filepath = '\\\\zh-mfs-srv\\Active\\ACPDU\\' + station + '\\Verify_xml\\'
            if not os.path.exists(filepath):
                os.mkdir(filepath)
            file = open(filepath + testdata['NewSerialNumber'] + '_' + re.sub(r'[:\s-]', '_', str(datetime.now())[0:19]) + '.xml', 'wt')
            file.write(xml_str)
            file.close()
        except:
            print('Save xml result file fail')
        return xml_str

    ##### GUAD RunCard Operation #####
    def savexmlfile_guad(self):
        testdata = self.verify_result
        if testdata['Reult'] == 'P':
            record_result = 'PASS'
        else:
            record_result = 'FAIL'
        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml_str += '<LOT_RECORD>\n'
        xml_str += '    <MODE>Production</MODE>\n'
        xml_str += '    <LOT_ID>%s</LOT_ID>\n' % self.wo.get()
        xml_str += '    <PART_NUM>%s</PART_NUM>\n' % self.pn.get()
        xml_str += '    <PART_REV>01</PART_REV>\n'
        xml_str += '    <TEST_CODE>QA Verify</TEST_CODE>\n'
        xml_str += '    <PROGRAM>QA Verify GUI</PROGRAM>\n'
        xml_str += '    <PROGRAM_REV>%s</PROGRAM_REV>\n' % testdata['Rev']
        xml_str += '    <START_DATE>%s</START_DATE>\n' % self.start_date
        xml_str += '    <END_DATE>%s</END_DATE>\n' % self.end_date
        xml_str += '    <TESTER_ID>%s</TESTER_ID>\n' % self.station.get()
        xml_str += '    <PART_RECORD>\n'
        xml_str += '        <PART_ID>%s</PART_ID>\n' % self.sn.get()
        xml_str += '        <PART_RESULT>%s</PART_RESULT>\n' % record_result
        xml_str += '        <TEST_TIME>%s</TEST_TIME>\n' % self.run_time
        page_list = ("LP_00H", "UP_00H", "UP_01H", "UP_02H", "UP_03H", "UP_04H", "UP_13H", "UP_28H", "UP_29H", "UP_2AH",
                     "UP_2BH", "UP_30H", "UP_41H", "UP_C0H", "UP_C1H", "UP_C2H", "UP_C3H", "UP_C4H", "UP_C5H")
        a = 1
        for page in page_list:
            k = 'S' + f'{a}'
            xml_str += '        <TEST_RECORD>\n'
            xml_str += '            <TNAME>%s</TNAME>\n' % page
            xml_str += '            <RESULT>%s</RESULT>\n' % record_result
            xml_str += '            <VECT_RESULT>%s</VECT_RESULT>\n' % testdata[k]
            xml_str += '            <VECT_TYPE>hex</VECT_TYPE>\n'
            xml_str += '        </TEST_RECORD>\n'
            a += 1
        xml_str += '    </PART_RECORD>\n'
        xml_str += '</LOT_RECORD>\n'
        # ##save xml result file at the local
        filepath = os.getcwd() + '\\XML_Results\\'
        if not os.path.exists(filepath):
            os.mkdir(filepath)
        filename = filepath + self.sn.get() + '_' + re.sub(r'[:\s-]', '_', str(datetime.now())[0:19]) + '.xml'
        try:
            file = open(filename, 'wt')
            file.write(xml_str)
            file.close()
        except:
            print('Save xml result file fail:', filename)
        # save xml file to datacard directory in guad
        if self.data.pro_info_zh['operator'] != 'admin':
            filepath = '\\\\gumfp01\\Group\\DATA\\OSG\\To_DataCard'
            filename = filepath + self.sn.get() + '_' + re.sub(r'[:\s-]', '_', str(datetime.now())[0:19]) + '.xml'
            try:
                file = open(filename, 'wt')
                file.write(xml_str)
                file.close()
            except:
                print('Save xml result file fail:', filename)

    def GUAD_parse_barcode(self, event=None):
        sn = self.string_format(self.sn.get())
        self.sn.set(sn)
        if sn == '':
            print('Input SN is empty.')
            self.btn_qa_verify.config(state='disabled')
            return False
        ################### GUAD operation ########################
        if self.data.pro_info_zh['operator'] == 'admin':  # for admin
            if len(self.sn.get()) > 12:
                msg.showerror(title="Error!", message="Only one SN can be entered. Please re-enter.")
                self.sn.set('')
            else:
                self.btn_qa_verify.focus_set()               # 正常输入情况下将焦点转到QA verify按钮
        else:                                            # for operator
            self.wo.set('')
            self.pn.set('')
            self.code_spec_file.set('')
            ##### check SN in RunCard #####
            myRunCard = RunCard()
            myRunCard.connect()
            if myRunCard.get_unit_status(sn):
                print('SN is found in RunCard')
                self.btn_qa_verify.config(state='normal')
            else:
                msg.showerror(title="Error!", message="SN is not found in RunCard. Please check.")
                self.sn.set('')
                self.wo.set('')
                self.pn.set('')
                self.code_spec_file.set('')
                self.btn_qa_verify.config(state='disabled')
                return False
            ##### check status in RunCard #####
            status = myRunCard.get_status(sn)
            if status != 'IN QUEUE':
                msg.showerror(title="Error!", message="Module needs to be IN QUEUE state. Please check.")
                self.sn.set('')
                self.wo.set('')
                self.pn.set('')
                self.code_spec_file.set('')
                self.btn_qa_verify.config(state='disabled')
                return False
            ##### check WO in RunCard #####
            wo = myRunCard.get_workorder(sn)
            if wo:
                self.wo.set(wo)
            else:
                msg.showerror(title="Error!", message="Work oder is not found in RunCard. Please check.")
                self.sn.set('')
                self.wo.set('')
                self.pn.set('')
                self.code_spec_file.set('')
                self.btn_qa_verify.config(state='disabled')
                return False
            ##### check PN in RunCard #####
            pn = myRunCard.get_partnum(sn)
            if pn:
                self.pn.set(pn)
            else:
                msg.showerror(title="Error!", message="Part number is not found in RunCard. Please check.")
                self.sn.set('')
                self.wo.set('')
                self.pn.set('')
                self.code_spec_file.set('')
                self.btn_qa_verify.config(state='disabled')
                return False
            ##### check OP_code in RunCard, select hex/bin/codespec files, and enable test button #####
            opcode = myRunCard.get_opcode(self.sn.get())
            production_file = os.getcwd() + '\\config file\\' + 'production setting qaverify.xlsx'
            df = pd.read_excel(production_file, sheet_name='RunCard flow', names=['code', 'description'], index_col=0,
                               dtype=str, keep_default_na=False, usecols=[1, 2])
            excel_test_code = df.index[df['description'] == 'QA'].tolist()[0]
            print('Test code is: ', excel_test_code)
            df2 = pd.read_excel(production_file, sheet_name='Test info', names=['item', 'description'], index_col=0,
                               dtype=str, keep_default_na=False, usecols=[0, 1])
            if opcode != excel_test_code:
                self.btn_qa_verify.config(state='disabled')
                msg.showerror(title="Error!",
                                     message="Current OP code is %s. Configuration is %s.\n"
                                             "Wrong test step! Please check module status in RunCard." % (opcode, excel_test_code))
                self.sn.set('')
                self.wo.set('')
                self.pn.set('')
                self.code_spec_file.set('')
                self.btn_qa_verify.config(state='disabled')
            else:
                top_codespec_location = df2['description']['GUAD Codespec']
                top_codespec_folder = top_codespec_location + '\\' + pn + '\\' + 'Top' + '\\'
                error, top_codespec = self.find_file(top_codespec_folder, ['.txt'])
                # in case in the future will use Excel codespec file as well
                if not error:
                    self.code_spec_file.set('')
                    self.sn.set('')
                    self.wo.set('')
                    self.pn.set('')
                    self.code_spec_file.set('')
                    return False
                else:
                    self.code_spec_file.set(top_codespec)
                    self.btn_qa_verify.config(state='normal')
                    self.btn_qa_verify.focus_set()
                    return True
            ########################################################################

    def find_file(self, folder, extension):
        files = os.listdir(folder)
        selected_file = []
        for file in files:
            for ext in extension:
                if file.endswith(ext):
                    selected_file.append(file)
        if len(selected_file) > 1 or len(selected_file) == 0:
            msg.showwarning("showerror", "File loading error. Please choose and load one manually.")
            return False, None
        else:
            final_file = folder + selected_file[0]
            return True, final_file

    def get_fw_info_GUAD(self):
        PN = self.pn.get()
        production_file = os.getcwd() + '\\config file\\' + 'production setting qaverify.xlsx'
        df1 = pd.read_excel(production_file, sheet_name='Test info', names=['item', 'description'], index_col=0,
                            dtype=str, keep_default_na=False, usecols=[0, 1])
        summary_file_location = df1['description']['GUAD summary file']
        summary_file = summary_file_location + '\\' + 'Module_FW_Bootloader_Version_Summary.xlsx'
        if os.path.exists(summary_file):
            df2 = pd.read_excel(summary_file, sheet_name='Summary',
                            names=['Part_Number', 'FW_PN', 'FW_Version', 'Bootloader_Version'],
                            dtype=str, keep_default_na=False, usecols=[0, 3, 4, 5])
            print('Summary file location is: ', summary_file)
            print(df2)
            info_all = df2.iloc[df2.index[df2['Part_Number'] == PN].tolist()].values.tolist()
        else:
            print('Summary file location is not exist: ', summary_file)
            msg.showerror(title='Error!', message='Summary file location is not exist: '+summary_file+'. Please check '
                                'GUAD summary file config in the config\\production setting qaverify.xlsx')
            info_all = [['', '', '', '']]
        return info_all

    def GUAD_record_result_check(self, test_type):
        if test_type == 'All Channel':
            opcode = 'T806'
        else:
            opcode = 'T807'
        myDataCard = DataCard(self.sn.get(), opcode)
        test_result = myDataCard.get_3T_last_record()
        result = self.check_3T_result(test_result, test_type)
        return result

