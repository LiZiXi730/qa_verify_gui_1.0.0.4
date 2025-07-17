# import I2c_driver_define as i2c_def
#
# if i2c_def.I2C_DRIVER_SELECT == i2c_def.DL_defs.I2C_DRV_USB_HID:
#     from usb_hid_i2c.I2C_Communicate import IIC_R_W
# else:
#     from totalphase.aardvark_my_i2c import IIC_R_W

import time
import numpy as np
import pandas as pd
from tkinter.messagebox import *
import gc
from math import log10, log
import struct
import matplotlib.pylab as plt
import sys
import os


class GDK_200:
    def __init__(self, vendor_id=0x0486, product_id=0x5750, ch=0x02, addr=0xA0, i2c_drv=1):
        self.vid = vendor_id
        self.pid = product_id
        self.ch = ch
        self.addr = addr
        self.i2c_drv = i2c_drv
        if self.i2c_drv == 1:
            from usb_hid_i2c.I2C_Communicate import IIC_R_W
            self.my_i2c = IIC_R_W(vendor_id=self.vid, product_id=self.pid, ch=self.ch, addr=self.addr)
        elif self.i2c_drv == 2:
            from totalphase.aardvark_my_i2c import IIC_R_W
            self.my_i2c = IIC_R_W(port=0, bit_rate=400, timeout=150, addr=self.addr)
        else:
            print("Current i2c driver can't be supported.")

    def page_select(self, index=0x00):
        self.my_i2c.write_bytes_maximum_55bytes(127, [index])

    # ===========================CDB Operation=========================
    def check_cdb_available(self, timeout_cdb=500):
        self.timeout_cdb = timeout_cdb
        time_start = time.perf_counter()
        # print("timeout=", self.timeout_cdb)
        while True:
            data = self.my_i2c.read_bytes_maximum_58bytes(37, 1)[0]
            # print("Available :"+str(data))
            sts_busy = (data >> 7) & 0x1
            sts_fail = (data >> 6) & 0x1
            command_result = data & 0x3F
            # print(sts_busy,sts_fail,command_result)
            if sts_busy == 0 and sts_fail == 0:
                return sts_busy, sts_fail, data
                # return sts_busy, sts_fail, command_result
            # elif (time.perf_counter() - time_start) >= self.timeout_cdb:
            #     print("CDB is buzy, byte37 value is" + hex(int(data)))
            #     return False
            elif sts_busy == 0 and sts_fail == 1:
                self.page_select(0x9F)
                buff = self.my_i2c.read_bytes_maximum_58bytes(134, 2)
                # print("LPLength:" + str(buff))
                data_str = []
                for i in buff:
                    data_str.append(int(i))
                Rllplen = data_str[0] & 0xFF
                # RLPLChkCode = data_str[1] & 0xFF
                # print(type(RLPLChkCode), type(Rllplen))
                # print("RLLplen:" + str(Rllplen))
                Rlpl_payload = self.my_i2c.read_bytes_maximum_128bytes(136, int(Rllplen))
                Rlpl_payload = [round(x) for x in Rlpl_payload]
                # True_Fail_code = self.get_payload()[2]
                Info = ""
                if command_result == 0:
                    Info = "Reserved"
                elif command_result == 1:
                    Info = "CMD Code unknown"
                elif command_result == 2:
                    Info = "Parameter range error or not supported"
                elif command_result == 3:
                    Info = "Previous CMD was not ABORTED by CMD Abort"
                elif command_result == 4:
                    Info = "Command checking time out"
                elif command_result == 5:
                    Info = "CdbCheckCode Error"
                elif command_result == 6:
                    Info = "Password error"
                elif command_result in range(7, 16):
                    Info = "Reserved for STS command checking error"
                elif command_result in range(16, 32):
                    Info = "Reserved"
                elif command_result in range(32, 48):
                    Info = "For individual STS command or task error"
                elif command_result in range(48, 64):
                    Info = "Custom"
                else:
                    pass
                # showinfo(title="CDB status failed!",
                #          message="STS_FAIL code is " + str(hex(command_result) + " " + Info))
                # del data  # reclaim memory
                # gc.collect()
                print('CDB elapse time ' + '{:.2f}'.format(
                    time.perf_counter() - time_start) + 's when CDB status is failed.')
                print('Byte37 value is 0x' + '{:02x}'.format(data))
                print('Rlpl_payload: ' + str(Rlpl_payload))
                return sts_busy, sts_fail, data, Rlpl_payload
                # return sts_busy, sts_fail, command_result, Rlpl_payload
            elif sts_busy == 1 and (time.perf_counter() - time_start) >= self.timeout_cdb:
                # print("CDB is buzy, busy status is:" + hex(int(command_result)))
                print('CDB elapse time' + '{:.2f}'.format(
                    time.perf_counter() - time_start) + 's when CDB status is buzy.')
                print('Byte37 value is 0x' + '{:02x}'.format(data))
                return sts_busy, sts_fail, data
                # return sts_busy, sts_fail, command_result
                Info = ""
                if command_result == 0:
                    Info = "Reserved"
                elif command_result == 1:
                    Info = "Command is captured but not processed"
                elif command_result == 2:
                    Info = "Command checking is in progress"
                elif command_result == 3:
                    Info = "Command execution is in progress"
                elif command_result in range(4, 48):
                    Info = "Reserved"
                elif command_result in range(48, 64):
                    Info = "Custom"
                else:
                    pass
                # showinfo(title="CDB status is reserved!",
                #          message="STS_FAIL Code is " + str(hex(command_result) + " " + Info))
            else:
                time.sleep(0.03)
            # del data  # reclaim memory
            # gc.collect()

    def send_cdb(self, cmd_id=0x8001, len_epl=0, payload=None):
        data = [0] * 8
        if not self.check_cdb_available(5)[0]:
            data[0] = cmd_id >> 8
            data[1] = cmd_id & 0xFF
            data[2] = len_epl >> 8
            data[3] = len_epl & 0xFF
            data[4] = len(payload)
            data[5] = 0
            data[6] = 0
            data[7] = 0
            # data_np = np.array(data)
            # print("data:" + str(data_np))
            # payload_np = np.array(payload)
            # print("payload:" + str(payload_np))
            # buffer = np.hstack([data_np, payload_np])
            buffer = data + payload
            # print("buffer:" + str(buffer))
            # data[5] = (buffer.sum() & 0xFF) + 1  # CDB checkcode calculate by using 1's complement.The Checkcode calculaltion is 求和取反，not 求和取反再加一.
            # buffer[5] = np.uint8(buffer.sum()) ^ 0xFF
            buffer[5] = sum(buffer) ^ 0xFF
            # print("data to be sent in send_cdb:" + str(buffer))
            # newdata = np.hstack(data)
            self.page_select(0x9F)
            self.my_i2c.write_bytes_maximum_128bytes(130, buffer[2:])
            self.my_i2c.write_bytes_maximum_55bytes(128, buffer[0:2])
        else:
            # print("CDB status is busy:"+ str(self.check_cdb_available(5)[0]))
            print('CDB status is busy before sending CDB command ID 0x' + '{:04x}'.format(cmd_id))

    def get_payload(self):
        self.page_select(0x9F)
        buff = self.my_i2c.read_bytes_maximum_58bytes(134, 2)
        # print("LPLength:" + str(buff))
        data_str = []
        for i in buff:
            data_str.append(int(i))
        Rllplen = data_str[0] & 0xFF
        RLPLChkCode = data_str[1] & 0xFF
        # print(type(RLPLChkCode), type(Rllplen))
        print("RLLplen:" + str(Rllplen))
        # print("debug", Rllplen)
        Rlpl_payload = self.my_i2c.read_bytes_maximum_128bytes(136, int(Rllplen))
        Rlpl_payload = [round(x) for x in Rlpl_payload]
        # print("RLLplen:" + str(Rllplen))
        # print("RLPLChkCode:" + str(RLPLChkCode))
        # print("Read payload value:" + str(Rlpl_payload))
        # status = Rlpl_payload[2]
        # statusinfo = ''
        # if status == 0:
        #     statusinfo = 'COMMAND_SUCCESS'
        # elif status == 2:
        #     statusinfo = 'COMMAND_INVALID'
        #     # showinfo(title="Command_invalid!", message="Unrecognized API command " )
        # elif status == 3:
        #     statusinfo = 'COMMAND_INVALID_FIELD'
        #     # showinfo(title="Command_invalid!", message="Some API command field\ncontains invalid value! ")
        # elif status == 4:
        #     statusinfo = 'COMMAND_FAILED'
        #     # showinfo(title="Command_FAILED!", message="API Command failed ")
        # elif status == 5:
        #     statusinfo = 'COMMAND_EXCEPTION'
        # else:
        #     pass
        return Rllplen, RLPLChkCode, Rlpl_payload  # statusinfo

    def get_payload_V2(self):
        Rlpl_payload = []
        self.page_select(0x9F)
        buff = self.my_i2c.read_bytes_maximum_58bytes(134, 2)
        data_str = []
        for i in buff:
            data_str.append(int(i))
        Rllplen = data_str[0] & 0xFF
        print('Rllplen:' + str(Rllplen))
        RLPLChkCode = data_str[1] & 0xFF
        if Rllplen <= 120:
            self.page_select(0x9F)
            Rlpl_payload = self.my_i2c.read_bytes_maximum_128bytes(136, Rllplen)
            Rlpl_payload = [round(x) for x in Rlpl_payload]
            print('payload :' + str(Rlpl_payload))
        elif Rllplen == 0xF0:  # Rllplen = 0xF0 + (length / 128)   length = Table9F read 0x134
            self.page_select(0xA0)
            Rlpl_payload1 = self.my_i2c.read_bytes_maximum_128bytes(128, 128)
            Rlpl_payload = [round(x) for x in Rlpl_payload1]
            print('payload :' + str(Rlpl_payload))
        elif Rllplen == 0xF1:
            self.page_select(0xA0)
            Rlpl_payload1 = self.my_i2c.read_bytes_maximum_128bytes(128, 128)
            Rlpl_payload1 = [round(x) for x in Rlpl_payload1]
            self.page_select(0xA1)
            Rlpl_payload2 = self.my_i2c.read_bytes_maximum_128bytes(128, 128)
            Rlpl_payload2 = [round(x) for x in Rlpl_payload2]
            Rlpl_payload = Rlpl_payload1 + Rlpl_payload2
            print('payload :' + str(Rlpl_payload))
        elif Rllplen == 0xF2:
            self.page_select(0xA0)
            Rlpl_payload1 = self.my_i2c.read_bytes_maximum_128bytes(128, 128)
            Rlpl_payload1 = [round(x) for x in Rlpl_payload1]
            self.page_select(0xA1)
            Rlpl_payload2 = self.my_i2c.read_bytes_maximum_128bytes(128, 128)
            Rlpl_payload2 = [round(x) for x in Rlpl_payload2]
            self.page_select(0xA2)
            Rlpl_payload3 = self.my_i2c.read_bytes_maximum_128bytes(128, 128)
            Rlpl_payload3 = [round(x) for x in Rlpl_payload3]
            print('payload :' + str(Rlpl_payload))
            Rlpl_payload = Rlpl_payload1 + Rlpl_payload2 + Rlpl_payload3
        elif Rllplen == 0xF3:
            self.page_select(0xA0)
            Rlpl_payload1 = self.my_i2c.read_bytes_maximum_128bytes(128, 128)
            Rlpl_payload1 = [round(x) for x in Rlpl_payload1]
            self.page_select(0xA1)
            Rlpl_payload2 = self.my_i2c.read_bytes_maximum_128bytes(128, 128)
            Rlpl_payload2 = [round(x) for x in Rlpl_payload2]
            self.page_select(0xA2)
            Rlpl_payload3 = self.my_i2c.read_bytes_maximum_128bytes(128, 128)
            Rlpl_payload3 = [round(x) for x in Rlpl_payload3]
            self.page_select(0xA3)
            Rlpl_payload4 = self.my_i2c.read_bytes_maximum_128bytes(128, 128)
            Rlpl_payload4 = [round(x) for x in Rlpl_payload4]
            Rlpl_payload = Rlpl_payload1 + Rlpl_payload2 + Rlpl_payload3 + Rlpl_payload4
            print('payload :' + str(Rlpl_payload))
        # if Rllplen <=  120:
        #     self.page_select(0x9F)
        #     Rlpl_payload = self.my_i2c.read_bytes_maximum_128bytes(136, int(Rllplen))
        #     Rlpl_payload = [round(x) for x in Rlpl_payload]
        # elif Rllplen > 120 and Rllplen <= 248:
        #     self.page_select(0xA0)
        #     Rlpl_payload = self.my_i2c.read_bytes_maximum_128bytes(128, int(Rllplen))
        #     Rlpl_payload = [round(x) for x in Rlpl_payload]
        # elif Rllplen > 248:
        #     self.page_select(0xA0)
        #     Rlpl_payload1 = self.my_i2c.read_bytes_maximum_128bytes(128, 128)
        #     Rlpl_payload1 = [round(x) for x in Rlpl_payload1]
        #     self.page_select(0xA1)
        #     Rlpl_payload2 = self.my_i2c.read_bytes_maximum_128bytes(128, int(Rllplen-128))
        #     Rlpl_payload2 = [round(x) for x in Rlpl_payload2]
        #     Rlpl_payload = Rlpl_payload1 + Rlpl_payload2
        return Rllplen, RLPLChkCode, Rlpl_payload  # statusinfo

    def get_Extend_payload(self):
        self.page_select(0x9F)
        buff = self.my_i2c.read_bytes_maximum_128bytes(132, 2)
        print(buff)
        EPLLen = (int(buff[0]) << 8 | int(buff[1]))
        print("EPLLen:" + str(EPLLen))
        EPL_1_payload = self.my_i2c.read_bytes_maximum_128bytes(136, 120)
        if (EPLLen - 120) % 128 != 0:
            time = (EPLLen - 120) // 128 + 1
        else:
            time = (EPLLen - 120) // 128
        print("EPLLen time is :" + str(time))
        EPL_2_payload = []
        for x in range(time):
            a = "A" + str(x)
            self.page_select(int(a, 16))
            if (EPLLen - 120) <= 128:
                Read_Num = (EPLLen - 120)
            else:
                Read_Num = 128
            EPL_2_payload = (self.my_i2c.read_bytes_maximum_128bytes(128, int(Read_Num)))

        EPL_payload = EPL_1_payload + EPL_2_payload
        print("EPL1:" + str(EPL_1_payload) + "EPL2:" + str(EPL_2_payload))

        print("Read payload value:" + str(EPLLen) + str(EPL_payload))

        status = EPL_payload[2]
        statusinfo = ''
        if status == 0:
            statusinfo = 'COMMAND_SUCCESS'
        elif status == 2:
            statusinfo = 'COMMAND_INVALID'
            showinfo(title="Command_invalid!", message="Unrecognized API command ")
        elif status == 3:
            statusinfo = 'COMMAND_INVALID_FIELD'
            showinfo(title="Command_invalid!", message="Some API command field\ncontains invalid value! ")
        elif status == 4:
            statusinfo = 'COMMAND_FAILED'
            showinfo(title="Command_FAILED!", message="API Command failed ")
        elif status == 5:
            statusinfo = 'COMMAND_EXCEPTION'
        else:
            pass
        return EPLLen, EPL_payload, statusinfo

    def send_cdb_command_DSP(self, cmd_id=0x8100, len_epl=0, payload=[]):
        # if self.check_cdb_available():
        self.send_cdb(cmd_id, len_epl, payload)
        data = self.check_cdb_available(500)
        if (data[0] == 0) and (data[1] == 0):
            return self.get_payload()
        else:
            print(' CDB status is unsuccessful before get payload info for CDB ID 0x' + '{:04x}'.format(cmd_id))
            # print("Check_CDB_available :" + str(data))
            return None
        # busy = data[0]
        # fail = data[1]
        # time.sleep(0.01)
        # # if busy == 2:
        # #     pass
        # #     #raise ("CDB status is busy!")
        # # elif fail == 3:
        # #     pass
        # #     #raise ("CDB status is failed!")
        # # else:
        # return self.get_payload()

    def send_cdb_command_DSP_V2(self, cmd_id=0x8100, len_epl=0, payload=[]):
        # if self.check_cdb_available():
        self.send_cdb(cmd_id, len_epl, payload)
        data = self.check_cdb_available(500)
        if (data[0] == 0) and (data[1] == 0):
            return self.get_payload_V2()
        else:
            print(' CDB status is unsuccessful before get payload info for CDB ID 0x' + '{:04x}'.format(cmd_id))
            # print("Check_CDB_available :" + str(data))
            return None

    def send_cdb_Extend_command_DSP(self, cmd_id=0x8100, len_epl=0, payload=[]):
        # if self.check_cdb_available():
        self.send_cdb(cmd_id, len_epl, payload)
        data = self.check_cdb_available(500)
        print("Check_CDB_available :" + str(data))
        busy = data[0]
        fail = data[1]
        if busy == 2:
            raise ("CDB status is busy!")
        elif fail == 3:
            raise ("CDB status is failed!")
        else:
            return self.get_Extend_payload()

    def signed_set(self, num, b, n):
        output_y = int((num * 2 ** n)) & (2 ** b - 1)
        return output_y

    def signed_set1(self, num, n):
        output_y = num * 2 ** n
        return output_y

    def unsigned_set(self, num, b, n):
        output_y = int(num * 2 ** n) & (2 ** b - 1)
        return output_y

    def signed_get(self, num, b, n):
        if num >> (b - 1) & 0x1 == 0:
            output_y = num / 2 ** n
        else:
            output_y = (num - 2 ** b) / 2 ** n
        return output_y

    def unsigned_get(self, num, n):
        output_y = (num / 2 ** n)
        return output_y

    def ToBytes(self, data):
        if type(data) == type('12'):
            if len(data) % 2 != 0:
                data += '0'
                print("add '0' at end,amended: ", end="")
            return bytes().fromhex(data)
        elif type(data) == type([1, ]):
            return bytes(data)
        else:
            print("only 'str' or 'list' is valid!")
            return None

    def send_cdb_lpl(self, cmd_id=0x8100, res_epl_len=0, payload=None):
        if res_epl_len:
            epl_total = []
            rest_len = res_epl_len
            offset = 0
            while True:
                if rest_len <= 512:
                    epl_total.extend(self.get_response_epl_single(cmd_id=cmd_id, offset=offset, res_epl_len=rest_len))
                    break
                else:
                    epl_total.extend(self.get_response_epl_single(cmd_id=cmd_id, offset=offset, res_epl_len=512))
                rest_len -= 512
                offset += 512
            return epl_total
        elif len(payload) <= 120:  # write lpl
            if not self.check_cdb_available(50)[0]:
                data = [0] * 8
                data[0] = cmd_id >> 8
                data[1] = cmd_id & 0xFF
                data[4] = len(payload)
                buffer = data + payload
                buffer[5] = sum(buffer) ^ 0xFF
                self.page_select(0x9F)
                self.my_i2c.write_bytes_maximum_128bytes(130, buffer[2:])
                self.my_i2c.write_bytes_maximum_55bytes(128, buffer[0:2])
            else:
                print('CDB status is busy before sending CDB command ID 0x' + '{:04x}'.format(cmd_id))
        else:
            print('LPL payload only support maximum 120bytes')

    def get_response_epl_single(self, cmd_id=0x8100, offset=0, res_epl_len=512):
        data = [0] * 8
        if not self.check_cdb_available(50)[0]:
            data[0] = cmd_id >> 8
            data[1] = cmd_id & 0xFF
            data[4] = 4
            payload = [offset >> 8, offset & 0xFF, res_epl_len >> 8, res_epl_len & 0xFF]
            buffer = data + payload
            buffer[5] = sum(buffer) ^ 0xFF
            self.page_select(0x9F)
            self.my_i2c.write_bytes_maximum_128bytes(130, buffer[2:])
            self.my_i2c.write_bytes_maximum_55bytes(128, buffer[0:2])
            data = self.check_cdb_available(50)
            if (data[0] == 0) and (data[1] == 0):
                rest_len = res_epl_len
                idx = 0
                epl_all = []
                while True:
                    if rest_len <= 128:
                        self.page_select(0xA0 + idx)
                        epl_all.extend(self.my_i2c.read_bytes_maximum_128bytes(128, rest_len))
                        break
                    else:
                        self.page_select(0xA0 + idx)
                        epl_all.extend(self.my_i2c.read_bytes_maximum_128bytes(128, 128))
                    idx += 1
                    rest_len -= 128
                return epl_all
            else:
                print('CDB status is unsuccessful before get payload info for CDB ID 0x' + '{:04x}'.format(
                    cmd_id) + ' for offset ' + '{:04x}'.format(offset))
        else:
            print('CDB status is busy before sending CDB command ID 0x' + '{:04x}'.format(
                cmd_id) + ' for offset ' + '{:04x}'.format(offset))

    # ===========================DSP Operation=========================

    def set_pattern_generator(self, state="OFF"):
        self.page_select(0x13)
        cur_value = self.my_i2c.read_bytes_maximum_58bytes(152, 1)[0]
        if state == "OFF":
            self.my_i2c.write_bytes_maximum_55bytes(152, [cur_value & 0xFE])
        elif state == "ON":
            self.my_i2c.write_bytes_maximum_55bytes(152, [cur_value | 0x01])
        else:
            print(state + "is invalid for set pattern generator operation for lane1")

    def set_pattern_checker(self, state="OFF"):
        self.page_select(0x13)
        cur_value = self.my_i2c.read_bytes_maximum_58bytes(168, 1)[0]
        if state == "OFF":
            self.my_i2c.write_bytes_maximum_55bytes(168, [cur_value & 0xFE])
        elif state == "ON":
            self.my_i2c.write_bytes_maximum_55bytes(168, [cur_value | 0x01])
        else:
            print(state + "is invalid for set pattern checker operation for lane1")

    def set_ber_time(self, time=1):
        self.page_select(0x13)
        cur_value = self.my_i2c.read_bytes_maximum_58bytes(177, 1)[0]
        if (time <= 7) and (time >= 0):
            self.my_i2c.write_bytes_maximum_55bytes(177,
                                                    [(cur_value & 0xF1) | (time << 1)])  # bit 1-3 for gate time
        else:
            print("gate time " + str(time) + " out of range")

    def select_diagnostics(self, value=1):
        self.page_select(0x14)
        self.my_i2c.write_bytes_maximum_55bytes(128, [value])  # value1 means select host/media lane1-8 ber

    def get_post_ber(self):
        self.page_select(0x14)
        cur_data = self.my_i2c.read_bytes_maximum_58bytes(208, 2)
        data_u16 = cur_data[0] << 8 | cur_data[1]  # Big Endian
        m = (data_u16 & 0x07FF)
        s = (data_u16 >> 11)
        return m * (10 ** (s - 24))

    def get_ber(self):
        time.sleep(3.5)  # current gating time is 3s fixed by FW, sleep time should be loner than this setting.
        self.page_select(0x20)
        cur_data = self.my_i2c.read_bytes_maximum_58bytes(156, 2)  # pre_ber is parameter15 defined by FW
        data_u16 = cur_data[0] << 8 | cur_data[1]  # Big Endian
        m = (data_u16 & 0x07FF)
        s = (data_u16 >> 11)
        return m * (10 ** (s - 24))

    def ber_config(self):
        self.set_pattern_generator("ON")
        self.set_pattern_checker("ON")
        self.set_ber_time(1)  # set 5s gate time
        self.select_diagnostics(1)

    def FW_internal_triggermonitor(self):
        # Here is the recommendation for reducing getting BER timing:
        # 1. Temporary disable FW internal call trigger monitor per second by writing page E4h.C1h register with 0x5A (requires module unlocked).
        # 2. Call TriggerMonitor();
        # 3. Delay 5 seconds (you may change delay what you want)
        # 4. Call TriggerMonitor();
        # 5. Read pre-fec ber, post-fec ber, etc. all required performance monitors
        self.page_select(0xE4)
        self.my_i2c.write_bytes_maximum_55bytes(0xC1, [0x5A])  # Disable write 0x5A, enable write 0

    def Enable_FW_internal_triggermonitor(self):
        self.page_select(0xE4)
        self.my_i2c.write_bytes_maximum_55bytes(0xC1, [0x00])

    # def GetPreFecBER(self, delaytime=0.5):
    #     start = time.perf_counter()
    #     self.send_cdb_command_DSP(0x8112, 0, [0])  # Set twice TriggerMonitors
    #     time.sleep(delaytime)
    #     self.send_cdb_command_DSP(0x8112, 0, [0])
    #     TM = self.send_cdb_command_DSP(0x8314, 0, [0])  # GetFawErrorStatistics
    #     print("GetFawErrorStatics TM:" + str(TM))
    #     payload_res = (TM[2])[4:]
    #     # print(payload_res)
    #     try:
    #         accumebit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
    #                 (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
    #                              (payload_res[4] << 32) & (0xFF << 32)) | (
    #                              (payload_res[5] << 40) & (0xFF << 40)) | (
    #                              (payload_res[6] << 48) & (0xFF << 48)) | (
    #                              (payload_res[7] << 56) & (0xFF << 56)))
    #         # print(accumebit)
    #         accumecount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
    #                 (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
    #                                (payload_res[12] << 32) & (0xFF << 32)) | (
    #                                (payload_res[13] << 40) & (0xFF << 40)) | (
    #                                (payload_res[14] << 48) & (0xFF << 48)) | (
    #                                (payload_res[15] << 56) & (0xFF << 56)))
    #         # print(accumecount)
    #         maxbit = ((payload_res[16] & 0xFF) | ((payload_res[17] << 8) & (0xFF << 8)) | (
    #                 (payload_res[18] << 16) & (0xFF << 16)) | ((payload_res[19] << 24) & (0xFF << 24)) | (
    #                           (payload_res[20] << 32) & (0xFF << 32)) | (
    #                           (payload_res[21] << 40) & (0xFF << 40)) | (
    #                           (payload_res[22] << 48) & (0xFF << 48)) | (
    #                           (payload_res[23] << 56) & (0xFF << 56)))
    #         # print(maxbit)
    #         maxcount = ((payload_res[24] & 0xFF) | ((payload_res[25] << 8) & (0xFF << 8)) | (
    #                 (payload_res[26] << 16) & (0xFF << 16)) | ((payload_res[27] << 24) & (0xFF << 24)) | (
    #                             (payload_res[28] << 32) & (0xFF << 32)) | (
    #                             (payload_res[29] << 40) & (0xFF << 40)) | (
    #                             (payload_res[30] << 48) & (0xFF << 48)) | (
    #                             (payload_res[31] << 56) & (0xFF << 56)))
    #         # print(maxcount)
    #         minbit = ((payload_res[32] & 0xFF) | ((payload_res[33] << 8) & (0xFF << 8)) | (
    #                 (payload_res[34] << 16) & (0xFF << 16)) | ((payload_res[35] << 24) & (0xFF << 24)) | (
    #                           (payload_res[36] << 32) & (0xFF << 32)) | (
    #                           (payload_res[37] << 40) & (0xFF << 40)) | (
    #                           (payload_res[38] << 48) & (0xFF << 48)) | (
    #                           (payload_res[39] << 56) & (0xFF << 56)))
    #         # print(minbit)
    #         mincount = ((payload_res[40] & 0xFF) | ((payload_res[41] << 8) & (0xFF << 8)) | (
    #                 (payload_res[42] << 16) & (0xFF << 16)) | ((payload_res[43] << 24) & (0xFF << 24)) | (
    #                             (payload_res[44] << 32) & (0xFF << 32)) | (
    #                             (payload_res[45] << 40) & (0xFF << 40)) | (
    #                             (payload_res[46] << 48) & (0xFF << 48)) | (
    #                             (payload_res[47] << 56) & (0xFF << 56)))
    #         # print(mincount)
    #     except IndexError:
    #         print('Index error')
    #         return ['error', 'error', 'error', 'error', 'error', 'error', 'error', 'error', 'error']
    #     else:
    #         if accumebit > 0:
    #             accumber = '{:.3E}'.format(accumecount / accumebit)
    #         else:
    #             accumber = '{:.3E}'.format(1.0)  # if bit less than or equal to 0,the BER output is 999.0
    #         if maxbit > 0:
    #             maxber = '{:.3E}'.format(maxcount / maxbit)
    #         else:
    #             maxber = '{:.3E}'.format(1.0)
    #         if minbit > 0:
    #             minber = '{:.3E}'.format(mincount / minbit)
    #         else:
    #             minber = '{:.3E}'.format(1.0)
    #         costtime = round(time.perf_counter() - start, 4)
    #         return [accumber, maxber, minber, accumebit, accumecount, maxbit, maxcount, minbit, mincount, costtime]

    def GetPreFecBER(self, delaytime=0.5):
        start = time.perf_counter()
        cycle = int(delaytime // 5)
        remaining_time = delaytime % 5
        print(cycle, remaining_time)
        accumber = 0
        maxber = 0
        minber = 0
        accumebit = 0
        accumecount = 0
        maxbit = 0
        maxcount = 0
        minbit = 0
        mincount = 0
        self.page_select(0xE4)
        TMonitors = self.my_i2c.read_bytes_maximum_58bytes(0xC1, 1)[
            0]  # Because of FW will auto send Triggermonitors per sencond,external Triggermonitors did not working properly,wirte 0x5A for TableE1 0xC1 will stop auto send.
        if TMonitors != 0x5A:
            self.my_i2c.write_bytes_maximum_55bytes(0xC1, [0x5A])
        for i in range(0, cycle, 1):
            print("Cycle = ", i + 1)
            self.send_cdb_command_DSP(0x8112, 0, [0])  # Set twice TriggerMonitors
            time.sleep(5)
            self.send_cdb_command_DSP(0x8112, 0, [0])
            TM = self.send_cdb_command_DSP(0x8314, 0, [0])  # GetFawErrorStatistics
            print("GetFawErrorStatics TM:" + str(TM))
            payload_res = (TM[2])[4:]
            # print(payload_res)
            try:
                single_accumebit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                        (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
                                            (payload_res[4] << 32) & (0xFF << 32)) | (
                                            (payload_res[5] << 40) & (0xFF << 40)) | (
                                            (payload_res[6] << 48) & (0xFF << 48)) | (
                                            (payload_res[7] << 56) & (0xFF << 56)))
                # print(single_accumebit)
                single_accumecount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
                        (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
                                              (payload_res[12] << 32) & (0xFF << 32)) | (
                                              (payload_res[13] << 40) & (0xFF << 40)) | (
                                              (payload_res[14] << 48) & (0xFF << 48)) | (
                                              (payload_res[15] << 56) & (0xFF << 56)))
                # print(single_accumecount)
                single_maxbit = ((payload_res[16] & 0xFF) | ((payload_res[17] << 8) & (0xFF << 8)) | (
                        (payload_res[18] << 16) & (0xFF << 16)) | ((payload_res[19] << 24) & (0xFF << 24)) | (
                                         (payload_res[20] << 32) & (0xFF << 32)) | (
                                         (payload_res[21] << 40) & (0xFF << 40)) | (
                                         (payload_res[22] << 48) & (0xFF << 48)) | (
                                         (payload_res[23] << 56) & (0xFF << 56)))
                # print(single_maxbit)
                single_maxcount = ((payload_res[24] & 0xFF) | ((payload_res[25] << 8) & (0xFF << 8)) | (
                        (payload_res[26] << 16) & (0xFF << 16)) | ((payload_res[27] << 24) & (0xFF << 24)) | (
                                           (payload_res[28] << 32) & (0xFF << 32)) | (
                                           (payload_res[29] << 40) & (0xFF << 40)) | (
                                           (payload_res[30] << 48) & (0xFF << 48)) | (
                                           (payload_res[31] << 56) & (0xFF << 56)))
                # print(single_maxcount)
                single_minbit = ((payload_res[32] & 0xFF) | ((payload_res[33] << 8) & (0xFF << 8)) | (
                        (payload_res[34] << 16) & (0xFF << 16)) | ((payload_res[35] << 24) & (0xFF << 24)) | (
                                         (payload_res[36] << 32) & (0xFF << 32)) | (
                                         (payload_res[37] << 40) & (0xFF << 40)) | (
                                         (payload_res[38] << 48) & (0xFF << 48)) | (
                                         (payload_res[39] << 56) & (0xFF << 56)))
                # print(single_minbit)
                single_mincount = ((payload_res[40] & 0xFF) | ((payload_res[41] << 8) & (0xFF << 8)) | (
                        (payload_res[42] << 16) & (0xFF << 16)) | ((payload_res[43] << 24) & (0xFF << 24)) | (
                                           (payload_res[44] << 32) & (0xFF << 32)) | (
                                           (payload_res[45] << 40) & (0xFF << 40)) | (
                                           (payload_res[46] << 48) & (0xFF << 48)) | (
                                           (payload_res[47] << 56) & (0xFF << 56)))
                # print(single_mincount)
            except IndexError:
                print('Index error')
                return ['error', 'error', 'error', 'error', 'error', 'error', 'error', 'error', 'error']
            else:
                if single_accumebit > 0:
                    accumecount += single_accumecount
                    accumebit += single_accumebit
                    accumber = '{:.3E}'.format(accumecount / accumebit)
                    print(accumebit, accumecount, accumber)
                else:
                    accumber = '{:.3E}'.format(1.0)  # if bit less than or equal to 0,the BER output is 999.0
                if single_maxbit > 0:
                    maxcount += single_maxcount
                    maxbit += single_maxbit
                    maxber = '{:.3E}'.format(maxcount / maxbit)
                    print(maxcount, maxbit, maxber)
                else:
                    maxber = '{:.3E}'.format(1.0)
                if single_minbit > 0:
                    mincount += single_mincount
                    minbit += single_minbit
                    minber = '{:.3E}'.format(mincount / minbit)
                    print(mincount, minbit, minber)
                else:
                    minber = '{:.3E}'.format(1.0)

        if remaining_time > 0:
            self.send_cdb_command_DSP(0x8112, 0, [0])  # Set twice TriggerMonitors
            time.sleep(5)
            self.send_cdb_command_DSP(0x8112, 0, [0])
            TM = self.send_cdb_command_DSP(0x8314, 0, [0])  # GetFawErrorStatistics
            print("GetFawErrorStatics TM:" + str(TM))
            payload_res = (TM[2])[4:]
            # print(payload_res)
            try:
                single_accumebit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                        (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
                                            (payload_res[4] << 32) & (0xFF << 32)) | (
                                            (payload_res[5] << 40) & (0xFF << 40)) | (
                                            (payload_res[6] << 48) & (0xFF << 48)) | (
                                            (payload_res[7] << 56) & (0xFF << 56)))
                # print(single_accumebit)
                single_accumecount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
                        (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
                                              (payload_res[12] << 32) & (0xFF << 32)) | (
                                              (payload_res[13] << 40) & (0xFF << 40)) | (
                                              (payload_res[14] << 48) & (0xFF << 48)) | (
                                              (payload_res[15] << 56) & (0xFF << 56)))
                # print(single_accumecount)
                single_maxbit = ((payload_res[16] & 0xFF) | ((payload_res[17] << 8) & (0xFF << 8)) | (
                        (payload_res[18] << 16) & (0xFF << 16)) | ((payload_res[19] << 24) & (0xFF << 24)) | (
                                         (payload_res[20] << 32) & (0xFF << 32)) | (
                                         (payload_res[21] << 40) & (0xFF << 40)) | (
                                         (payload_res[22] << 48) & (0xFF << 48)) | (
                                         (payload_res[23] << 56) & (0xFF << 56)))
                # print(single_maxbit)
                single_maxcount = ((payload_res[24] & 0xFF) | ((payload_res[25] << 8) & (0xFF << 8)) | (
                        (payload_res[26] << 16) & (0xFF << 16)) | ((payload_res[27] << 24) & (0xFF << 24)) | (
                                           (payload_res[28] << 32) & (0xFF << 32)) | (
                                           (payload_res[29] << 40) & (0xFF << 40)) | (
                                           (payload_res[30] << 48) & (0xFF << 48)) | (
                                           (payload_res[31] << 56) & (0xFF << 56)))
                # print(single_maxcount)
                single_minbit = ((payload_res[32] & 0xFF) | ((payload_res[33] << 8) & (0xFF << 8)) | (
                        (payload_res[34] << 16) & (0xFF << 16)) | ((payload_res[35] << 24) & (0xFF << 24)) | (
                                         (payload_res[36] << 32) & (0xFF << 32)) | (
                                         (payload_res[37] << 40) & (0xFF << 40)) | (
                                         (payload_res[38] << 48) & (0xFF << 48)) | (
                                         (payload_res[39] << 56) & (0xFF << 56)))
                # print(single_minbit)
                single_mincount = ((payload_res[40] & 0xFF) | ((payload_res[41] << 8) & (0xFF << 8)) | (
                        (payload_res[42] << 16) & (0xFF << 16)) | ((payload_res[43] << 24) & (0xFF << 24)) | (
                                           (payload_res[44] << 32) & (0xFF << 32)) | (
                                           (payload_res[45] << 40) & (0xFF << 40)) | (
                                           (payload_res[46] << 48) & (0xFF << 48)) | (
                                           (payload_res[47] << 56) & (0xFF << 56)))
                # print(single_mincount)
            except IndexError:
                print('Index error')
                return ['error', 'error', 'error', 'error', 'error', 'error', 'error', 'error', 'error']
            else:
                if single_accumebit > 0:
                    accumecount += single_accumecount
                    accumebit += single_accumebit
                    accumber = '{:.3E}'.format(accumecount / accumebit)
                    print(accumebit, accumecount, accumber)
                else:
                    accumber = '{:.3E}'.format(1.0)  # if bit less than or equal to 0,the BER output is 999.0
                if single_maxbit > 0:
                    maxcount += single_maxcount
                    maxbit += single_maxbit
                    maxber = '{:.3E}'.format(maxcount / maxbit)
                    print(maxcount, maxbit, maxber)
                else:
                    maxber = '{:.3E}'.format(1.0)
                if single_minbit > 0:
                    mincount += single_mincount
                    minbit += single_minbit
                    minber = '{:.3E}'.format(mincount / minbit)
                    print(mincount, minbit, minber)
                else:
                    minber = '{:.3E}'.format(1.0)
        else:
            pass
        costtime = round(time.perf_counter() - start, 4)
        return [accumber, maxber, minber, accumebit, accumecount, maxbit, maxcount, minbit, mincount, costtime]

    # def GetPostFecBER(self,delaytime=0.5):
    #     start = time.perf_counter()
    #     self.send_cdb_command_DSP(0x8112, 0, [0])  # Set twice TriggerMonitors
    #     time.sleep(delaytime)
    #     self.send_cdb_command_DSP(0x8112, 0, [0])
    #     TM = self.send_cdb_command_DSP(0x8370, 0, [0]) #GetCorefecTestPatternCheckerCounters
    #     print("GetCorefecTestPatternCheckerCounters TM:" + str(TM))
    #     payload_res = (TM[2])[4:]
    #     print(payload_res)
    #     try:
    #         postfecbit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
    #                 (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
    #                              (payload_res[4] << 32) & (0xFF << 32)) | (
    #                              (payload_res[5] << 40) & (0xFF << 40)) | (
    #                              (payload_res[6] << 48) & (0xFF << 48)) | (
    #                              (payload_res[7] << 56) & (0xFF << 56)))
    #         #print(postfecbit)
    #         postfeccount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
    #                 (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
    #                                (payload_res[12] << 32) & (0xFF << 32)) | (
    #                                (payload_res[13] << 40) & (0xFF << 40)) | (
    #                                (payload_res[14] << 48) & (0xFF << 48)) | (
    #                                (payload_res[15] << 56) & (0xFF << 56)))
    #
    #         #print(postfeccount)
    #     except IndexError:
    #         print('error')
    #         return ['error', 'error', 'error']
    #     else:
    #         if postfecbit > 0:
    #             postber = '{:.3E}'.format(postfeccount / postfecbit)
    #         else:
    #             postber = '{:.3E}'.format(1.0)
    #         costtime = round(time.perf_counter() - start,4)
    #         return [postber,postfecbit,postfeccount,costtime]

    def GetPostFecBER(self, delaytime=0.5):
        start = time.perf_counter()
        cycle = int(delaytime // 5)
        remaining_time = delaytime % 5
        print(cycle, remaining_time)
        postfecbit = 0
        postfeccount = 0
        postber = 0
        self.page_select(0xE4)
        TMonitors = self.my_i2c.read_bytes_maximum_58bytes(0xC1, 1)[
            0]  # Because of FW will auto send Triggermonitors per sencond,external Triggermonitors did not working properly,wirte 0x5A for TableE1 0xC1 will stop auto send.
        if TMonitors != 0x5A:
            self.my_i2c.write_bytes_maximum_55bytes(0xC1, [0x5A])
        for i in range(0, cycle, 1):
            print("Cycle = ", i + 1)
            self.send_cdb_command_DSP(0x8112, 0, [0])  # Set twice TriggerMonitors
            time.sleep(5)
            self.send_cdb_command_DSP(0x8112, 0, [0])
            TM = self.send_cdb_command_DSP(0x8370, 0, [0])  # GetCorefecTestPatternCheckerCounters
            print("GetCorefecTestPatternCheckerCounters TM:" + str(TM))
            payload_res = (TM[2])[4:]
            # print(payload_res)
            try:
                single_postfecbit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                        (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
                                             (payload_res[4] << 32) & (0xFF << 32)) | (
                                             (payload_res[5] << 40) & (0xFF << 40)) | (
                                             (payload_res[6] << 48) & (0xFF << 48)) | (
                                             (payload_res[7] << 56) & (0xFF << 56)))
                print(single_postfecbit)
                single_postfeccount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
                        (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
                                               (payload_res[12] << 32) & (0xFF << 32)) | (
                                               (payload_res[13] << 40) & (0xFF << 40)) | (
                                               (payload_res[14] << 48) & (0xFF << 48)) | (
                                               (payload_res[15] << 56) & (0xFF << 56)))
                print(single_postfeccount)
            except IndexError:
                print('error')
                return ['error', 'error', 'error']
            else:
                if single_postfecbit > 0:
                    postfecbit += single_postfecbit
                    postfeccount += single_postfeccount
                    postber = '{:.3E}'.format(postfeccount / postfecbit)
                    print(postfeccount, postfecbit, postber)
                else:
                    postber = '{:.3E}'.format(1.0)

        if remaining_time > 0:
            self.send_cdb_command_DSP(0x8112, 0, [0])  # Set twice TriggerMonitors
            time.sleep(remaining_time)
            self.send_cdb_command_DSP(0x8112, 0, [0])
            TM = self.send_cdb_command_DSP(0x8370, 0, [0])  # GetCorefecTestPatternCheckerCounters
            print("GetCorefecTestPatternCheckerCounters TM:" + str(TM))
            payload_res = (TM[2])[4:]
            # print(payload_res)
            try:
                single_postfecbit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                        (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
                                             (payload_res[4] << 32) & (0xFF << 32)) | (
                                             (payload_res[5] << 40) & (0xFF << 40)) | (
                                             (payload_res[6] << 48) & (0xFF << 48)) | (
                                             (payload_res[7] << 56) & (0xFF << 56)))
                print(single_postfecbit)
                single_postfeccount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
                        (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
                                               (payload_res[12] << 32) & (0xFF << 32)) | (
                                               (payload_res[13] << 40) & (0xFF << 40)) | (
                                               (payload_res[14] << 48) & (0xFF << 48)) | (
                                               (payload_res[15] << 56) & (0xFF << 56)))
                print(single_postfeccount)
            except IndexError:
                print('error')
                return ['error', 'error', 'error']
            else:
                if single_postfecbit > 0:
                    postfecbit += single_postfecbit
                    postfeccount += single_postfeccount
                    postber = '{:.3E}'.format(postfeccount / postfecbit)
                    print(postfeccount, postfecbit, postber)
                else:
                    postber = '{:.3E}'.format(1.0)
        else:
            pass
        costtime = round(time.perf_counter() - start, 4)
        return [postber, postfecbit, postfeccount, costtime]

    def GetAllBER(self, delaytime=2):
        cycle = int(delaytime // 5)
        remaining_time = delaytime % 5
        print(cycle, remaining_time)
        prefecber = 0
        accumebit = 0
        accumecount = 0
        postfecbit = 0
        postfeccount = 0
        postber = 0
        stair_hamming_ber = []
        self.page_select(0xE4)
        TMonitors = self.my_i2c.read_bytes_maximum_58bytes(0xC1, 1)[
            0]  # Because of FW will auto send Triggermonitors per sencond,external Triggermonitors did not working properly,wirte 0x5A for TableE1 0xC1 will stop auto send.
        if TMonitors != 0x5A:
            self.my_i2c.write_bytes_maximum_55bytes(0xC1, [0x5A])
        for i in range(0, cycle, 1):
            print("Cycle = ", i + 1)
            self.send_cdb_command_DSP(0x8112, 0, [0])  # Set twice TriggerMonitors
            time.sleep(delaytime)
            self.send_cdb_command_DSP(0x8112, 0, [0])
            TM = self.send_cdb_command_DSP(0x8314, 0, [0])  # GetFawErrorStatistics Prefec BER read
            print("GetFawErrorStatics TM:" + str(TM))
            payload_res = (TM[2])[4:]
            single_accumebit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                    (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
                                        (payload_res[4] << 32) & (0xFF << 32)) | (
                                        (payload_res[5] << 40) & (0xFF << 40)) | (
                                        (payload_res[6] << 48) & (0xFF << 48)) | (
                                        (payload_res[7] << 56) & (0xFF << 56)))
            single_accumecount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
                    (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
                                          (payload_res[12] << 32) & (0xFF << 32)) | (
                                          (payload_res[13] << 40) & (0xFF << 40)) | (
                                          (payload_res[14] << 48) & (0xFF << 48)) | (
                                          (payload_res[15] << 56) & (0xFF << 56)))
            if single_accumebit > 0:
                accumecount += single_accumecount
                accumebit += single_accumebit
                prefecber = float(accumecount / accumebit)
            else:
                prefecber = float(1.0)  # if bit less than or equal to 0,the BER output is 999.0

            TM = self.send_cdb_command_DSP(0x8370, 0, [0])  # GetCorefecTestPatternCheckerCounters POST ber read
            print("GetCorefecTestPatternCheckerCounters TM:" + str(TM))
            payload_res = (TM[2])[4:]
            print(payload_res)
            single_postfecbit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                    (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
                                         (payload_res[4] << 32) & (0xFF << 32)) | (
                                         (payload_res[5] << 40) & (0xFF << 40)) | (
                                         (payload_res[6] << 48) & (0xFF << 48)) | (
                                         (payload_res[7] << 56) & (0xFF << 56)))
            # print(postfecbit)
            single_postfeccount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
                    (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
                                           (payload_res[12] << 32) & (0xFF << 32)) | (
                                           (payload_res[13] << 40) & (0xFF << 40)) | (
                                           (payload_res[14] << 48) & (0xFF << 48)) | (
                                           (payload_res[15] << 56) & (0xFF << 56)))
            if single_postfecbit > 0:
                postfecbit += single_postfecbit
                postfeccount += single_postfeccount
                postber = float(postfeccount / postfecbit)
            else:
                postber = float(1.0)
            stair_hamming_ber += self.EstimatedPreFecBER()

        if remaining_time > 0:
            self.send_cdb_command_DSP(0x8112, 0, [0])  # Set twice TriggerMonitors
            time.sleep(delaytime)
            self.send_cdb_command_DSP(0x8112, 0, [0])
            TM = self.send_cdb_command_DSP(0x8314, 0, [0])  # GetFawErrorStatistics Prefec BER read
            print("GetFawErrorStatics TM:" + str(TM))
            payload_res = (TM[2])[4:]
            single_accumebit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                    (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
                                        (payload_res[4] << 32) & (0xFF << 32)) | (
                                        (payload_res[5] << 40) & (0xFF << 40)) | (
                                        (payload_res[6] << 48) & (0xFF << 48)) | (
                                        (payload_res[7] << 56) & (0xFF << 56)))
            single_accumecount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
                    (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
                                          (payload_res[12] << 32) & (0xFF << 32)) | (
                                          (payload_res[13] << 40) & (0xFF << 40)) | (
                                          (payload_res[14] << 48) & (0xFF << 48)) | (
                                          (payload_res[15] << 56) & (0xFF << 56)))
            if single_accumebit > 0:
                accumecount += single_accumecount
                accumebit += single_accumebit
                prefecber = float(accumecount / accumebit)
            else:
                prefecber = float(1.0)  # if bit less than or equal to 0,the BER output is 999.0

            TM = self.send_cdb_command_DSP(0x8370, 0, [0])  # GetCorefecTestPatternCheckerCounters POST ber read
            print("GetCorefecTestPatternCheckerCounters TM:" + str(TM))
            payload_res = (TM[2])[4:]
            print(payload_res)
            single_postfecbit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                    (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
                                         (payload_res[4] << 32) & (0xFF << 32)) | (
                                         (payload_res[5] << 40) & (0xFF << 40)) | (
                                         (payload_res[6] << 48) & (0xFF << 48)) | (
                                         (payload_res[7] << 56) & (0xFF << 56)))
            # print(postfecbit)
            single_postfeccount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
                    (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
                                           (payload_res[12] << 32) & (0xFF << 32)) | (
                                           (payload_res[13] << 40) & (0xFF << 40)) | (
                                           (payload_res[14] << 48) & (0xFF << 48)) | (
                                           (payload_res[15] << 56) & (0xFF << 56)))
            if single_postfecbit > 0:
                postfecbit += single_postfecbit
                postfeccount += single_postfeccount
                postber = float(postfeccount / postfecbit)
            else:
                postber = float(1.0)
            stair_hamming_ber += self.EstimatedPreFecBER()
        else:
            pass
        return [postber, prefecber, stair_hamming_ber[5], stair_hamming_ber[4], postfeccount, postfecbit, accumecount,
                accumebit]

    # def GetPCSBER(self,channel = 0,direction = 0,delaytime=0.5 ):
    #     #     start = time.perf_counter()
    #     #     self.send_cdb_command_DSP(0x8112, 0, [0]) # Set twice TriggerMonitors
    #     #     time.sleep(delaytime)
    #     #     self.send_cdb_command_DSP(0x8112, 0, [0])
    #     #     command_array = [0] * 2
    #     #     command_array[0] = channel >> 0 & 0xFF
    #     #     command_array[1] = direction >> 0 & 0xFF
    #     #     TM = self.send_cdb_command_DSP(0x8390, 0, command_array) #GetFawErrorStatistics
    #     #     print("GetPcsTestPatternCheckerStatistics TM:" + str(TM))
    #     #     payload_res = (TM[2])[4:]
    #     #     print(payload_res)
    #     #     try:
    #     #         accumebit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
    #     #                     (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
    #     #                                               (payload_res[4] << 32) & (0xFF << 32)) | (
    #     #                                               (payload_res[5] << 40) & (0xFF << 40)) | (
    #     #                                               (payload_res[6] << 48) & (0xFF << 48)) | (
    #     #                                               (payload_res[7] << 56) & (0xFF << 56)))
    #     #         print(accumebit)
    #     #         accumecount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
    #     #                     (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
    #     #                                                 (payload_res[12] << 32) & (0xFF << 32)) | (
    #     #                                                 (payload_res[13] << 40) & (0xFF << 40)) | (
    #     #                                                 (payload_res[14] << 48) & (0xFF << 48)) | (
    #     #                                                 (payload_res[15] << 56) & (0xFF << 56)))
    #     #         print(accumecount)
    #     #         maxbit = ((payload_res[16] & 0xFF) | ((payload_res[17] << 8) & (0xFF << 8)) | (
    #     #                     (payload_res[18] << 16) & (0xFF << 16)) | ((payload_res[19] << 24) & (0xFF << 24)) | (
    #     #                                             (payload_res[20] << 32) & (0xFF << 32)) | (
    #     #                                             (payload_res[21] << 40) & (0xFF << 40)) | (
    #     #                                             (payload_res[22] << 48) & (0xFF << 48)) | (
    #     #                                             (payload_res[23] << 56) & (0xFF << 56)))
    #     #         print(maxbit)
    #     #         maxcount = ((payload_res[24] & 0xFF) | ((payload_res[25] << 8) & (0xFF << 8)) | (
    #     #                     (payload_res[26] << 16) & (0xFF << 16)) | ((payload_res[27] << 24) & (0xFF << 24)) | (
    #     #                                               (payload_res[28] << 32) & (0xFF << 32)) | (
    #     #                                               (payload_res[29] << 40) & (0xFF << 40)) | (
    #     #                                               (payload_res[30] << 48) & (0xFF << 48)) | (
    #     #                                               (payload_res[31] << 56) & (0xFF << 56)))
    #     #         print(maxcount)
    #     #         minbit = ((payload_res[32] & 0xFF) | ((payload_res[33] << 8) & (0xFF << 8)) | (
    #     #                     (payload_res[34] << 16) & (0xFF << 16)) | ((payload_res[35] << 24) & (0xFF << 24)) | (
    #     #                                             (payload_res[36] << 32) & (0xFF << 32)) | (
    #     #                                             (payload_res[37] << 40) & (0xFF << 40)) | (
    #     #                                             (payload_res[38] << 48) & (0xFF << 48)) | (
    #     #                                             (payload_res[39] << 56) & (0xFF << 56)))
    #     #         print(minbit)
    #     #         mincount = ((payload_res[40] & 0xFF) | ((payload_res[41] << 8) & (0xFF << 8)) | (
    #     #                     (payload_res[42] << 16) & (0xFF << 16)) | ((payload_res[43] << 24) & (0xFF << 24)) | (
    #     #                                               (payload_res[44] << 32) & (0xFF << 32)) | (
    #     #                                               (payload_res[45] << 40) & (0xFF << 40)) | (
    #     #                                               (payload_res[46] << 48) & (0xFF << 48)) | (
    #     #                                               (payload_res[47] << 56) & (0xFF << 56)))
    #     #         print(mincount)
    #     #     except IndexError:
    #     #         print('Index error')
    #     #         return ['error','error','error','error','error','error','error','error','error']
    #     #     else:
    #     #         if accumebit > 0:
    #     #             accumber = '{:.3E}'.format(accumecount / accumebit)#float(accumecount / accumebit)
    #     #         else:
    #     #             accumber = '{:.3E}'.format(1.0)  # if bit less than or equal to 0,the BER output is 999.0
    #     #         if maxbit > 0:
    #     #             maxber = '{:.3E}'.format(maxcount / maxbit)
    #     #         else:
    #     #             maxber = '{:.3E}'.format(1.0)
    #     #         if minbit > 0:
    #     #             minber = '{:.3E}'.format(mincount / minbit)
    #     #         else:
    #     #             minber = '{:.3E}'.format(1.0)
    #     #         costtime = round(time.perf_counter() - start,4)
    #     #         return [accumber, maxber, minber,accumebit,accumecount,maxbit,maxcount,minbit,mincount,costtime]

    def GetPCSBER(self, channel=0, direction=0, delaytime=0.5):
        start = time.perf_counter()
        cycle = int(delaytime // 5)
        remaining_time = delaytime % 5
        print(cycle, remaining_time)
        accumber = 0
        maxber = 0
        minber = 0
        accumebit = 0
        accumecount = 0
        maxbit = 0
        maxcount = 0
        minbit = 0
        mincount = 0
        for i in range(0, cycle, 1):
            print("Cycle = ", i + 1)
            self.send_cdb_command_DSP(0x8112, 0, [0])  # Set twice TriggerMonitors
            time.sleep(5)
            self.send_cdb_command_DSP(0x8112, 0, [0])
            command_array = [0] * 2
            command_array[0] = channel >> 0 & 0xFF
            command_array[1] = direction >> 0 & 0xFF
            TM = self.send_cdb_command_DSP(0x8390, 0, command_array)  # GetFawErrorStatistics
            print("GetPcsTestPatternCheckerStatistics TM:" + str(TM))
            payload_res = (TM[2])[4:]
            # print(payload_res)
            try:
                single_accumebit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                        (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
                                            (payload_res[4] << 32) & (0xFF << 32)) | (
                                            (payload_res[5] << 40) & (0xFF << 40)) | (
                                            (payload_res[6] << 48) & (0xFF << 48)) | (
                                            (payload_res[7] << 56) & (0xFF << 56)))
                # print(accumebit)
                single_accumecount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
                        (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
                                              (payload_res[12] << 32) & (0xFF << 32)) | (
                                              (payload_res[13] << 40) & (0xFF << 40)) | (
                                              (payload_res[14] << 48) & (0xFF << 48)) | (
                                              (payload_res[15] << 56) & (0xFF << 56)))
                # print(accumecount)
                single_maxbit = ((payload_res[16] & 0xFF) | ((payload_res[17] << 8) & (0xFF << 8)) | (
                        (payload_res[18] << 16) & (0xFF << 16)) | ((payload_res[19] << 24) & (0xFF << 24)) | (
                                         (payload_res[20] << 32) & (0xFF << 32)) | (
                                         (payload_res[21] << 40) & (0xFF << 40)) | (
                                         (payload_res[22] << 48) & (0xFF << 48)) | (
                                         (payload_res[23] << 56) & (0xFF << 56)))
                # print(maxbit)
                single_maxcount = ((payload_res[24] & 0xFF) | ((payload_res[25] << 8) & (0xFF << 8)) | (
                        (payload_res[26] << 16) & (0xFF << 16)) | ((payload_res[27] << 24) & (0xFF << 24)) | (
                                           (payload_res[28] << 32) & (0xFF << 32)) | (
                                           (payload_res[29] << 40) & (0xFF << 40)) | (
                                           (payload_res[30] << 48) & (0xFF << 48)) | (
                                           (payload_res[31] << 56) & (0xFF << 56)))
                # print(maxcount)
                single_minbit = ((payload_res[32] & 0xFF) | ((payload_res[33] << 8) & (0xFF << 8)) | (
                        (payload_res[34] << 16) & (0xFF << 16)) | ((payload_res[35] << 24) & (0xFF << 24)) | (
                                         (payload_res[36] << 32) & (0xFF << 32)) | (
                                         (payload_res[37] << 40) & (0xFF << 40)) | (
                                         (payload_res[38] << 48) & (0xFF << 48)) | (
                                         (payload_res[39] << 56) & (0xFF << 56)))
                # print(minbit)
                single_mincount = ((payload_res[40] & 0xFF) | ((payload_res[41] << 8) & (0xFF << 8)) | (
                        (payload_res[42] << 16) & (0xFF << 16)) | ((payload_res[43] << 24) & (0xFF << 24)) | (
                                           (payload_res[44] << 32) & (0xFF << 32)) | (
                                           (payload_res[45] << 40) & (0xFF << 40)) | (
                                           (payload_res[46] << 48) & (0xFF << 48)) | (
                                           (payload_res[47] << 56) & (0xFF << 56)))
                # print(mincount)
            except IndexError:
                print('Index error')
                return ['error', 'error', 'error', 'error', 'error', 'error', 'error', 'error', 'error']
            else:
                if single_accumebit > 0:
                    accumecount += single_accumecount
                    accumebit += single_accumebit
                    accumber = '{:.3E}'.format(accumecount / accumebit)  # float(accumecount / accumebit)
                    print(accumecount, accumebit, accumber)
                else:
                    accumber = '{:.3E}'.format(1.0)  # if bit less than or equal to 0,the BER output is 999.0
                if single_maxbit > 0:
                    maxcount += single_maxcount
                    maxbit += single_maxbit
                    maxber = '{:.3E}'.format(maxcount / maxbit)
                    print(maxcount, maxbit, maxber)
                else:
                    maxber = '{:.3E}'.format(1.0)
                if single_minbit > 0:
                    mincount += single_mincount
                    minbit += single_maxbit
                    minber = '{:.3E}'.format(mincount / minbit)
                    print(mincount, minbit, minber)
                else:
                    minber = '{:.3E}'.format(1.0)

        if remaining_time > 0:
            self.send_cdb_command_DSP(0x8112, 0, [0])  # Set twice TriggerMonitors
            time.sleep(remaining_time)
            self.send_cdb_command_DSP(0x8112, 0, [0])
            command_array = [0] * 2
            command_array[0] = channel >> 0 & 0xFF
            command_array[1] = direction >> 0 & 0xFF
            TM = self.send_cdb_command_DSP(0x8390, 0, command_array)  # GetFawErrorStatistics
            print("GetPcsTestPatternCheckerStatistics TM:" + str(TM))
            payload_res = (TM[2])[4:]
            # print(payload_res)
            try:
                single_accumebit = ((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                        (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
                                            (payload_res[4] << 32) & (0xFF << 32)) | (
                                            (payload_res[5] << 40) & (0xFF << 40)) | (
                                            (payload_res[6] << 48) & (0xFF << 48)) | (
                                            (payload_res[7] << 56) & (0xFF << 56)))
                # print(accumebit)
                single_accumecount = ((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
                        (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24)) | (
                                              (payload_res[12] << 32) & (0xFF << 32)) | (
                                              (payload_res[13] << 40) & (0xFF << 40)) | (
                                              (payload_res[14] << 48) & (0xFF << 48)) | (
                                              (payload_res[15] << 56) & (0xFF << 56)))
                # print(accumecount)
                single_maxbit = ((payload_res[16] & 0xFF) | ((payload_res[17] << 8) & (0xFF << 8)) | (
                        (payload_res[18] << 16) & (0xFF << 16)) | ((payload_res[19] << 24) & (0xFF << 24)) | (
                                         (payload_res[20] << 32) & (0xFF << 32)) | (
                                         (payload_res[21] << 40) & (0xFF << 40)) | (
                                         (payload_res[22] << 48) & (0xFF << 48)) | (
                                         (payload_res[23] << 56) & (0xFF << 56)))
                # print(maxbit)
                single_maxcount = ((payload_res[24] & 0xFF) | ((payload_res[25] << 8) & (0xFF << 8)) | (
                        (payload_res[26] << 16) & (0xFF << 16)) | ((payload_res[27] << 24) & (0xFF << 24)) | (
                                           (payload_res[28] << 32) & (0xFF << 32)) | (
                                           (payload_res[29] << 40) & (0xFF << 40)) | (
                                           (payload_res[30] << 48) & (0xFF << 48)) | (
                                           (payload_res[31] << 56) & (0xFF << 56)))
                # print(maxcount)
                single_minbit = ((payload_res[32] & 0xFF) | ((payload_res[33] << 8) & (0xFF << 8)) | (
                        (payload_res[34] << 16) & (0xFF << 16)) | ((payload_res[35] << 24) & (0xFF << 24)) | (
                                         (payload_res[36] << 32) & (0xFF << 32)) | (
                                         (payload_res[37] << 40) & (0xFF << 40)) | (
                                         (payload_res[38] << 48) & (0xFF << 48)) | (
                                         (payload_res[39] << 56) & (0xFF << 56)))
                # print(minbit)
                single_mincount = ((payload_res[40] & 0xFF) | ((payload_res[41] << 8) & (0xFF << 8)) | (
                        (payload_res[42] << 16) & (0xFF << 16)) | ((payload_res[43] << 24) & (0xFF << 24)) | (
                                           (payload_res[44] << 32) & (0xFF << 32)) | (
                                           (payload_res[45] << 40) & (0xFF << 40)) | (
                                           (payload_res[46] << 48) & (0xFF << 48)) | (
                                           (payload_res[47] << 56) & (0xFF << 56)))
                # print(mincount)
            except IndexError:
                print('Index error')
                return ['error', 'error', 'error', 'error', 'error', 'error', 'error', 'error', 'error']
            else:
                if single_accumebit > 0:
                    accumecount += single_accumecount
                    accumebit += single_accumebit
                    accumber = '{:.3E}'.format(accumecount / accumebit)  # float(accumecount / accumebit)
                    print(accumecount, accumebit, accumber)
                else:
                    accumber = '{:.3E}'.format(1.0)  # if bit less than or equal to 0,the BER output is 999.0
                if single_maxbit > 0:
                    maxcount += single_maxcount
                    maxbit += single_maxbit
                    maxber = '{:.3E}'.format(maxcount / maxbit)
                    print(maxcount, maxbit, maxber)
                else:
                    maxber = '{:.3E}'.format(1.0)
                if single_minbit > 0:
                    mincount += single_mincount
                    minbit += single_maxbit
                    minber = '{:.3E}'.format(mincount / minbit)
                    print(mincount, minbit, minber)
                else:
                    minber = '{:.3E}'.format(1.0)
        else:
            pass
        costtime = round(time.perf_counter() - start, 4)
        return [accumber, maxber, minber, accumebit, accumecount, maxbit, maxcount, minbit, mincount, costtime]

    def EstimatedPreFecBER(self):
        start = time.perf_counter()
        rc = self.send_cdb_command_DSP(0x831C, 0, [0])
        print("Current rc is" + str(rc))
        payload_res = (rc[2])[4:]
        print("getEstimatedPreCfecBer is" + str(payload_res))
        mantissa_Stair_BER = self.unsigned_get((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)), 12)
        order_magnitude_stair_BER = self.signed_get((payload_res[2] & 0xFF) | ((payload_res[3] << 8) & (0xFF << 8)), 16,
                                                    0)
        mantissa_hamming_BER = self.unsigned_get((payload_res[4] & 0xFF) | ((payload_res[5] << 8) & (0xFF << 8)), 12)
        order_magnitude_hamming_BER = self.signed_get((payload_res[6] & 0xFF) | ((payload_res[7] << 8) & (0xFF << 8)),
                                                      16, 0)
        stair_BER_raw = float(mantissa_Stair_BER) * pow(10, float(np.int16(order_magnitude_stair_BER)))
        # stair_BER = format(stair_BER_raw, '.3e')
        hamming_BER_raw = float(mantissa_hamming_BER) * pow(10, float(np.int16(order_magnitude_hamming_BER)))
        # hamming_BER = format(hamming_BER_raw, '.3e')
        runtime = round(time.perf_counter() - start, 4)
        return [mantissa_Stair_BER, order_magnitude_stair_BER, mantissa_hamming_BER, order_magnitude_hamming_BER,
                stair_BER_raw, hamming_BER_raw, runtime]

    def SetLineEgressLowSrLaneAttenuation(self, lane=0, att=0):
        attenuation_temp = np.uint16(self.unsigned_set(att, 16, 16))
        # print("atten:" + str(attenuation_temp))
        # attenuation = (((attenuation_temp & 0xFF) << 8) | ((attenuation_temp >> 8) & 0xFF ))
        command_array = [0] * 3
        command_array[0] = lane >> 0 & 0xFF
        # assert: (x >= 0 && x <= 3)
        command_array[1] = attenuation_temp >> 0 & 0xFF
        command_array[2] = attenuation_temp >> 8 & 0xFF
        print("SetLineEgressLowSrLaneAttenuation" + str(command_array))
        self.send_cdb_command_DSP(0x8221, 0, command_array)
        time.sleep(1)

    def GetLineEgressLowSrLaneAttenuation(self, lane=0):
        TM = self.send_cdb_command_DSP(0x8220, 0, [lane])
        payload_res = (TM[2])[4:]
        # print("GetLineEgressLowSrLaneAttenuationTM:" + str(TM))
        return float(self.unsigned_get((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)), 16))

    def SetLineEgressLowSrLaneSkew(self, Tlane=0, skew_raw=0):
        skew = self.signed_set(float(skew_raw), 16, 0)
        # fraskew_temp = (self.data.dut_obj.unsigned_set(self.txt_coefficients0_str.get(),0)) & 0x7FF
        # fraskew = ((fraskew_temp & 0xFF) << 8) | ((fraskew_temp >> 8) & 0xFF)
        command_array = [0] * 3
        command_array[0] = Tlane >> 0 & 0xFF
        # assert: (x >= 0 && x <= 3)
        # command_array[1] = skew >> 0 & 0xFF
        command_array[1] = skew >> 0 & 0xFF
        command_array[2] = skew >> 8 & 0xFF
        self.send_cdb_command_DSP(0x8224, 0, command_array)

    def GetLineEgressLowSrLaneSkew(self, Tlane=0):
        TM = self.send_cdb_command_DSP(0x8225, 0, [Tlane])
        print("GetLineEgressLowSrLaneskew TM:" + str(TM))
        payload_res = (TM[2])[4:]
        print(payload_res)
        # self.txt_skew_str.set((np.uint8((payload_res[0] & 0xFF))))
        return float((self.signed_get(((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8))), 16, 0)))

    def setLineIngressSkew_H(self, raw_H):
        print('/n Entering Func setLineIngressSkew...')
        skew_H = self.signed_set(raw_H, 16, 0)
        print('skewH : ' + str(skew_H))
        command_array = [0] * 3
        if raw_H > -320 and raw_H < 320:  # skew_H setting is legal
            command_array[0] = 0
            command_array[1] = skew_H & 0xFF  # TODO: MSB?
            command_array[2] = (skew_H & 0xFF00) >> 8
            print("Send command array is:" + str(command_array))
            self.send_cdb_command_DSP(0x8250, 0, command_array)
        else:  # skew_H setting is out of +-320 boundary
            print('skew H is out of +-320 boundary!')

    def setLineIngressSkew_V(self, raw_V):
        print('/n Entering Func setLineIngressSkew...')
        skew_V = self.signed_set(raw_V, 16, 0)
        print('skewV : ' + str(skew_V))
        command_array = [0] * 3
        if raw_V > -320 and raw_V < 320:  # skew_V setting is legal
            command_array[0] = 1
            command_array[1] = skew_V & 0xFF  # TODO: MSB?
            command_array[2] = (skew_V & 0xFF00) >> 8
            print("Send command array is:" + str(command_array))
            self.send_cdb_command_DSP(0x8250, 0, command_array)
        else:  # skew_V setting is out of +-320 boundary
            print('skew V is out of +-320 boundary!')

    def getLineIngressSkew(self):
        print('/n Entering Func getLineIngressSkew...')
        rc = self.send_cdb_command_DSP(0x8251, 0, [0])
        rc = (rc[2])[4:]
        print("Current rc is " + str(rc))
        skew_H = self.signed_get(((rc[0] & 0xFF) | ((rc[1] << 8) & (0xFF << 8))), 16, 0)

        rc = self.send_cdb_command_DSP(0x8251, 0, [1])
        rc = (rc[2])[4:]
        skew_V = self.signed_get(((rc[0] & 0xFF) | ((rc[1] << 8) & (0xFF << 8))), 16, 0)
        return skew_H, skew_V

    def SetLineEgressLowSrFilterCoefficients(self, lane=0, coefs=[]):
        coefficients = []
        for coef in coefs:
            coefficients.append(self.signed_set(coef, 9, 2))
        command_array = [0] * 15
        command_array[0] = lane >> 0
        # assert: (x >= 0 && x <= 3)
        command_array[1] = coefficients[0] >> 0 & 0xFF
        command_array[2] = coefficients[0] >> 8 & 0xFF
        # assert: (x<512)
        command_array[3] = coefficients[1] >> 0 & 0xFF
        command_array[4] = coefficients[1] >> 8 & 0xFF
        # assert: (x<512)
        command_array[5] = coefficients[2] >> 0 & 0xFF
        command_array[6] = coefficients[2] >> 8 & 0xFF
        # assert: (x<512)
        command_array[7] = coefficients[3] >> 0 & 0xFF
        command_array[8] = coefficients[3] >> 8 & 0xFF
        # assert: (x<512)
        command_array[9] = coefficients[4] >> 0 & 0xFF
        command_array[10] = coefficients[4] >> 8 & 0xFF
        # assert: (x<512)
        command_array[11] = coefficients[5] >> 0 & 0xFF
        command_array[12] = coefficients[5] >> 8 & 0xFF
        # assert: (x<512)
        command_array[13] = coefficients[6] >> 0 & 0xFF
        command_array[14] = coefficients[6] >> 8 & 0xFF
        self.send_cdb_command_DSP(0x8222, 0, command_array)

    def PreAgcSwing_DISABLE(self):
        for i in range(4):
            command_array = [0] * 9
            buffer_lane_sel = i
            command_array[0] = buffer_lane_sel >> 0 & 0xFF
            command_array[1] = 28 >> 0 & 0xFF
            command_array[2] = 256 >> 0 & 0xFF
            command_array[3] = 256 >> 8 & 0xFF
            command_array[4] = 511 >> 0 & 0xFF
            command_array[5] = 511 >> 8 & 0xFF
            command_array[6] = 0 >> 0 & 0xFF
            command_array[7] = 0 >> 8 & 0xFF
            command_array[8] = 0 >> 0 & 0xFF
            print("Set line agc disable:" + str(command_array))
            self.send_cdb_command_DSP(0x825A, 0,
                                      command_array)  # 先将“Enable AGC for all lanes设为0”，然后配置四个通道的signal_reference = 28 ,signal_gain = 256 , signal_max = 511 , signal_min = 0；

    def PreAgcSwing_ENABLE(self):
        for i in range(4):
            command_array1 = [0] * 9
            buffer_lane_sel = i
            command_array1[0] = buffer_lane_sel >> 0 & 0xFF
            command_array1[1] = 28 >> 0 & 0xFF
            command_array1[2] = 256 >> 0 & 0xFF
            command_array1[3] = 256 >> 8 & 0xFF
            command_array1[4] = 511 >> 0 & 0xFF
            command_array1[5] = 511 >> 8 & 0xFF
            command_array1[6] = 0 >> 0 & 0xFF
            command_array1[7] = 0 >> 8 & 0xFF
            command_array1[8] = 1 >> 0 & 0xFF
            print("Set line agc enable:" + str(command_array1))
            self.send_cdb_command_DSP(0x825A, 0, command_array1)

    def getLineIngressDspStatus(self):
        print('/n Entering Func getLineIngressDspStatus...')
        rc = self.send_cdb_command_DSP(0x8262, 0, [0])
        print("Current rc is" + str(rc))
        try:
            payload_res = (rc[2])[4:]
            print("getLineIngressDspStatus is" + str(payload_res))
            dsp_status = {}
            dsp_status.update(
                amplitude_hi=self.unsigned_get((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)), 15))
            dsp_status.update(
                amplitude_hq=self.unsigned_get((payload_res[2] & 0xFF) | ((payload_res[3] << 8) & (0xFF << 8)), 15))
            dsp_status.update(
                amplitude_vi=self.unsigned_get((payload_res[4] & 0xFF) | ((payload_res[5] << 8) & (0xFF << 8)), 15))
            dsp_status.update(
                amplitude_vq=self.unsigned_get((payload_res[6] & 0xFF) | ((payload_res[7] << 8) & (0xFF << 8)), 15))
            dsp_status.update(mse_hi=10 * np.log10(
                float(self.unsigned_get((payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)), 11))))
            dsp_status.update(mse_hq=10 * np.log10(
                float(self.unsigned_get((payload_res[10] & 0xFF) | ((payload_res[11] << 8) & (0xFF << 8)), 11))))
            dsp_status.update(mse_vi=10 * np.log10(
                float(self.unsigned_get((payload_res[12] & 0xFF) | ((payload_res[13] << 8) & (0xFF << 8)), 11))))
            dsp_status.update(mse_vq=10 * np.log10(
                float(self.unsigned_get((payload_res[14] & 0xFF) | ((payload_res[15] << 8) & (0xFF << 8)), 11))))
            dsp_status.update(cg_h=self.signed_get((payload_res[16]), 8, 0))
            dsp_status.update(cg_v=self.signed_get((payload_res[17]), 8, 0))
            dsp_status.update(
                evm_h=self.unsigned_get((payload_res[18] & 0xFF) | ((payload_res[19] << 8) & (0xFF << 8)), 11))
            dsp_status.update(
                evm_v=self.unsigned_get((payload_res[20] & 0xFF) | ((payload_res[21] << 8) & (0xFF << 8)), 11))
        except:
            dsp_status = {}
            invalid_data = float('1e-4')
            dsp_status.update(amplitude_hi=invalid_data)
            dsp_status.update(amplitude_hq=invalid_data)
            dsp_status.update(amplitude_vi=invalid_data)
            dsp_status.update(amplitude_vq=invalid_data)
            dsp_status.update(mse_hi=invalid_data)
            dsp_status.update(mse_hq=invalid_data)
            dsp_status.update(mse_vi=invalid_data)
            dsp_status.update(mse_vq=invalid_data)
            dsp_status.update(cg_h=invalid_data)
            dsp_status.update(cg_v=invalid_data)
            dsp_status.update(evm_h=invalid_data)
            dsp_status.update(evm_v=invalid_data)
        # TODO: implement
        print('Existing Func getLineIngressDspStatus...')
        return dsp_status

    def Save_LineEgress_Att(self):
        Att_data = []
        for x in (0, 1, 2, 3):
            TM = self.send_cdb_command_DSP(0x8220, 0, [x])
            payload_res = (TM[2])[4:]
            Att_data.extend([payload_res[1], payload_res[0]])
        self.page_select(0xC2)
        self.my_i2c.write_bytes_maximum_55bytes(0xA8, Att_data)
        Att = self.my_i2c.read_bytes_maximum_58bytes(0xA8, 8)
        HI = Att[0] << 8 | Att[1]
        HQ = Att[2] << 8 | Att[3]
        VI = Att[4] << 8 | Att[5]
        VQ = Att[6] << 8 | Att[7]
        return [HI, HQ, VI, VQ]

    def Save_LineEgress_FilterCoef(self):
        Coef_data = []
        for x in (0, 1, 2, 3):
            TM = self.send_cdb_command_DSP(0x8223, 0, [x])
            payload_res = (TM[2])[4:]
            Coef_data.extend([payload_res[0:15]])
        coefdata_raw = []
        for msb, lsb in zip(Coef_data[0][1::2], Coef_data[0][0::2]):
            coefdata_raw.extend([msb, lsb])
        self.page_select(0xC3)
        print(coefdata_raw)
        self.my_i2c.write_bytes_maximum_55bytes(0x80, coefdata_raw)
        Coef = self.my_i2c.read_bytes_maximum_58bytes(0x80, 14)
        hicoef0 = Coef[0] << 8 | Coef[1]
        hicoef1 = Coef[2] << 8 | Coef[3]
        hicoef2 = Coef[4] << 8 | Coef[5]
        hicoef3 = Coef[6] << 8 | Coef[7]
        hicoef4 = Coef[8] << 8 | Coef[9]
        hicoef5 = Coef[10] << 8 | Coef[11]
        hicoef6 = Coef[12] << 8 | Coef[13]
        return [hicoef0, hicoef1, hicoef2, hicoef3, hicoef4, hicoef5, hicoef6]

    def Save_LineEgress_FilterCoef1(self):
        Coef_data = []
        for x in (0, 1, 2, 3):
            TM = self.send_cdb_command_DSP(0x8223, 0, [x])
            payload_res = (TM[2])[4:]
            Coef_data = Coef_data + ([payload_res[0:14]])
        print(Coef_data)
        coefdata_raw = []
        for x in (0, 1, 2, 3):
            for n in (0, 2, 4, 6, 8, 10, 12):
                coefdata_raw.append(int((self.signed_get(
                    ((Coef_data[x][n] & 0xFF) | ((Coef_data[x][n + 1] & 0xFF) << 8)), 9, 2)) * 4 + 87))
                # ((payload_res[0] & 0xFF)|((payload_res[1]<<8) & (0xFF<<8))&0x1FF),9,2)
        "Save_data = filter_coefficient_data_to_DSP + 87.For example: " \
        "if original filter coefficient is (-1.5, 0, -0.5, 28.25, -0.5, 0, -1.5), the filter_coefficient_data_to_DSP is " \
        "(-6, 0, -2, 113, -2, 0, -6)Save data should be: (81, 87, 85, 200, 85, 87, 81)"
        print(coefdata_raw)
        self.page_select(0xC1)
        Add = 0xBC
        for val in coefdata_raw:
            self.my_i2c.write_bytes_maximum_55bytes(Add, [val])
            Add += 1

    def Save_LineEgressLowSrLaneSkew(self):
        Tx_skew_data = []
        for x in (0, 1, 2, 3):
            TM = self.send_cdb_command_DSP(0x8225, 0, [x])
            payload_res = (TM[2])[4:]
            Tx_skew_data.extend([payload_res[1], payload_res[0]])
        self.page_select(0xC2)
        self.my_i2c.write_bytes_maximum_55bytes(0xB0, Tx_skew_data)
        Tx_skew = self.my_i2c.read_bytes_maximum_58bytes(0xB0, 8)
        HI = Tx_skew[0] << 8 | Tx_skew[1]
        HQ = Tx_skew[2] << 8 | Tx_skew[3]
        VI = Tx_skew[4] << 8 | Tx_skew[5]
        VQ = Tx_skew[6] << 8 | Tx_skew[7]
        return [HI, HQ, VI, VQ]

    def Save_LineIngressSkew(self):
        H_data = self.send_cdb_command_DSP(0x8251, 0, [0])
        H = (H_data[2])[4:]
        H_raw = [H[1], H[0]]

        V_data = self.send_cdb_command_DSP(0x8251, 0, [1])
        V = (V_data[2])[4:]
        V_raw = [V[1], V[0]]

        self.page_select(0xC2)
        self.my_i2c.write_bytes_maximum_55bytes(0xB8, H_raw)
        self.my_i2c.write_bytes_maximum_55bytes(0xBA, V_raw)
        Rx_skew_H = self.my_i2c.read_bytes_maximum_58bytes(0xB8, 2)
        Rx_skew_V = self.my_i2c.read_bytes_maximum_58bytes(0xBA, 2)
        Rx_H = Rx_skew_H[0] << 8 | Rx_skew_H[1]
        Rx_V = Rx_skew_V[0] << 8 | Rx_skew_V[1]
        return [Rx_H, Rx_V]

    def ControlAvs(self, Ctrl=1, Vstep=5, CurrentV=650, AVSAnalysisMode=0, AVSRate=2, Prv=0, Reserved=0):
        print('ControlAvs Setting')
        payload = [Ctrl, Vstep, CurrentV & 0xFF, CurrentV >> 8, AVSAnalysisMode, AVSRate, Prv, Reserved]
        TM = self.send_cdb_command_DSP(0x8109, 0, payload)
        payload_res = (TM[2])
        print('ControlAvs response info:' + str(payload_res))
        AVS_CTRL = {}
        # Canopus {'Info': 0, 'RODropGoalVT2': 12681, 'AVSStatus': 2, 'ROMinCountVT3': 16891, 'ROMinCountVT2': 13564, 'Length': 24, 'Status': 0, 'RODropGoalVT3': 16236, 'RODropGoalVT1': 8638, 'ROMinCountVT1': 9345, 'Flag': 1, 'ROGoalVT3': 15972, 'ROGoalVT2': 12411, 'ROGoalVT1': 8373}
        AVS_CTRL.update(Info=payload_res[3])
        AVS_CTRL.update(RODropGoalVT2=(payload_res[0x0F] << 8) | payload_res[0x0E])
        AVS_CTRL.update(AVSStatus=payload_res[4])
        AVS_CTRL.update(ROMinCountVT3=(payload_res[0x17] << 8) | payload_res[0x16])
        AVS_CTRL.update(ROMinCountVT2=(payload_res[0x15] << 8) | payload_res[0x14])
        AVS_CTRL.update(Length=(payload_res[1] << 8) | payload_res[0])
        AVS_CTRL.update(Status=payload_res[2])
        AVS_CTRL.update(RODropGoalVT3=(payload_res[0x11] << 8) | payload_res[0x10])
        AVS_CTRL.update(RODropGoalVT1=(payload_res[0x0D] << 8) | payload_res[0x0C])
        AVS_CTRL.update(ROMinCountVT1=(payload_res[0x13] << 8) | payload_res[0x12])
        AVS_CTRL.update(Flag=payload_res[5])
        AVS_CTRL.update(ROGoalVT3=(payload_res[0x0B] << 8) | payload_res[0x0A])
        AVS_CTRL.update(ROGoalVT2=(payload_res[0x09] << 8) | payload_res[0x08])
        AVS_CTRL.update(ROGoalVT1=(payload_res[0x07] << 8) | payload_res[0x06])
        return AVS_CTRL

    def GetLineOpticalChannelMonitorsItem(self, item):
        self.send_cdb_command_DSP(0x8112, 0, [0])  # Set TriggerMonitors
        time.sleep(5)
        command_array = [0] * 1
        command_array[0] = item >> 0 & 0xFF
        TM = self.send_cdb_command_DSP_V2(0x8324, 0, command_array)
        print("GetLineOpticalChannelMonitorsItem is" + str(TM))
        payload_res = (TM[2])[4:]
        # print("GetLineOpticalChannelMonitorsItem is" + payload_res)
        average = (payload_res[0] & 0xFF | ((payload_res[1] << 8) & (0xFF << 8)))
        min = (payload_res[2] & 0xFF | ((payload_res[3] << 8) & (0xFF << 8)))
        max = (payload_res[4] & 0xFF | ((payload_res[5] << 8) & (0xFF << 8)))
        return average, min, max

    def GetLineOpticalChannelMonitorsAll(self):
        self.send_cdb_command_DSP(0x8112, 0, [0])  # Set twice TriggerMonitors
        time.sleep(5)
        TM = self.send_cdb_command_DSP_V2(0x8322, 0, [0])
        print("GetLineOpticalChannelMonitorsAll TM:" + str(TM))
        x = (TM[2])[4:]
        print(x)

        allmonitor_vals = []

        allmonitor_vals.append(str(self.unsigned_get((x[0] & 0xFF) | ((x[1] << 8) & (0xFF << 8)), 12)))  # q average
        allmonitor_vals.append(str(self.unsigned_get(((x[2] & 0xFF) | ((x[3] << 8) & (0xFF << 8))), 12)))  # q min
        allmonitor_vals.append(str(self.unsigned_get(((x[4] & 0xFF) | ((x[5] << 8) & (0xFF << 8))), 12)))  # q max

        allmonitor_vals.append(str(self.signed_get(((x[6] & 0xFF) | ((x[7] << 8) & (0xFF << 8))), 16, 6)))  # cd
        allmonitor_vals.append(str(self.signed_get(((x[8] & 0xFF) | ((x[9] << 8) & (0xFF << 8))), 16, 6)))
        allmonitor_vals.append(str(self.signed_get(((x[10] & 0xFF) | ((x[11] << 8) & (0xFF << 8))), 16, 6)))

        allmonitor_vals.append(str(self.signed_get(((x[12] & 0xFF) | ((x[13] << 8) & (0xFF << 8))), 16, 4)))  # dgd
        allmonitor_vals.append(str(self.signed_get(((x[14] & 0xFF) | ((x[15] << 8) & (0xFF << 8))), 16, 4)))
        allmonitor_vals.append(str(self.signed_get(((x[16] & 0xFF) | ((x[17] << 8) & (0xFF << 8))), 16, 4)))
        # resverd #
        allmonitor_vals.append(str(self.unsigned_get(((x[24] & 0xFF) | ((x[25] << 8) & (0xFF << 8))), 8)))  # pdl
        allmonitor_vals.append(str(self.unsigned_get(((x[26] & 0xFF) | ((x[27] << 8) & (0xFF << 8))), 8)))
        allmonitor_vals.append(str(self.unsigned_get(((x[28] & 0xFF) | ((x[29] << 8) & (0xFF << 8))), 8)))

        allmonitor_vals.append(str(self.unsigned_get(((x[30] & 0xFF) | ((x[31] << 8) & (0xFF << 8))), 7)))  # osnr
        allmonitor_vals.append(str(self.unsigned_get(((x[32] & 0xFF) | ((x[33] << 8) & (0xFF << 8))), 7)))
        allmonitor_vals.append(str(self.unsigned_get(((x[34] & 0xFF) | ((x[35] << 8) & (0xFF << 8))), 7)))

        allmonitor_vals.append(str(self.unsigned_get(((x[36] & 0xFF) | ((x[37] << 8) & (0xFF << 8))), 7)))  # esnr
        allmonitor_vals.append(str(self.unsigned_get(((x[38] & 0xFF) | ((x[39] << 8) & (0xFF << 8))), 7)))
        allmonitor_vals.append(str(self.unsigned_get(((x[40] & 0xFF) | ((x[41] << 8) & (0xFF << 8))), 7)))

        allmonitor_vals.append(str(self.signed_get(((x[42] & 0xFF) | ((x[43] << 8) & (0xFF << 8))), 16, 2)))  # cfo
        allmonitor_vals.append(str(self.signed_get(((x[44] & 0xFF) | ((x[45] << 8) & (0xFF << 8))), 16, 2)))
        allmonitor_vals.append(str(self.signed_get(((x[46] & 0xFF) | ((x[47] << 8) & (0xFF << 8))), 16, 2)))

        allmonitor_vals.append(str(self.unsigned_get(((x[48] & 0xFF) | ((x[49] << 8) & (0xFF << 8))), 8)))  # evm
        allmonitor_vals.append(str(self.unsigned_get(((x[50] & 0xFF) | ((x[51] << 8) & (0xFF << 8))), 8)))
        allmonitor_vals.append(str(self.unsigned_get(((x[52] & 0xFF) | ((x[53] << 8) & (0xFF << 8))), 8)))

        allmonitor_vals.append(str(self.unsigned_get(((x[54] & 0xFF) | ((x[55] << 8) & (0xFF << 8))), 4)))  # sop
        allmonitor_vals.append(str(self.unsigned_get(((x[56] & 0xFF) | ((x[57] << 8) & (0xFF << 8))), 4)))
        allmonitor_vals.append(str(self.unsigned_get(((x[58] & 0xFF) | ((x[59] << 8) & (0xFF << 8))), 4)))
        # resverd #
        allmonitor_vals.append(
            str(self.signed_get(((x[66] & 0xFF) | ((x[67] << 8) & (0xFF << 8))), 16, 8)))  # rx angle h
        allmonitor_vals.append(str(self.signed_get(((x[68] & 0xFF) | ((x[69] << 8) & (0xFF << 8))), 16, 8)))
        allmonitor_vals.append(str(self.signed_get(((x[70] & 0xFF) | ((x[71] << 8) & (0xFF << 8))), 16, 8)))

        allmonitor_vals.append(
            str(self.signed_get(((x[72] & 0xFF) | ((x[73] << 8) & (0xFF << 8))), 16, 8)))  # rx angle v
        allmonitor_vals.append(str(self.signed_get(((x[74] & 0xFF) | ((x[75] << 8) & (0xFF << 8))), 16, 8)))
        allmonitor_vals.append(str(self.signed_get(((x[76] & 0xFF) | ((x[77] << 8) & (0xFF << 8))), 16, 8)))

        allmonitor_vals.append(
            str(self.unsigned_get(((x[78] & 0xFF) | ((x[79] << 8) & (0xFF << 8))), 8)))  # rx gain mism h
        allmonitor_vals.append(str(self.unsigned_get(((x[80] & 0xFF) | ((x[81] << 8) & (0xFF << 8))), 8)))
        allmonitor_vals.append(str(self.unsigned_get(((x[82] & 0xFF) | ((x[83] << 8) & (0xFF << 8))), 8)))

        allmonitor_vals.append(
            str(self.unsigned_get(((x[84] & 0xFF) | ((x[85] << 8) & (0xFF << 8))), 8)))  # rx gain mism v
        allmonitor_vals.append(str(self.unsigned_get(((x[86] & 0xFF) | ((x[87] << 8) & (0xFF << 8))), 8)))
        allmonitor_vals.append(str(self.unsigned_get(((x[88] & 0xFF) | ((x[89] << 8) & (0xFF << 8))), 8)))

        allmonitor_vals.append(
            str(self.signed_get(((x[90] & 0xFF) | ((x[91] << 8) & (0xFF << 8))), 16, 8)))  # rx skew h
        allmonitor_vals.append(str(self.signed_get(((x[92] & 0xFF) | ((x[93] << 8) & (0xFF << 8))), 16, 8)))
        allmonitor_vals.append(str(self.signed_get(((x[94] & 0xFF) | ((x[95] << 8) & (0xFF << 8))), 16, 8)))

        allmonitor_vals.append(
            str(self.signed_get(((x[96] & 0xFF) | ((x[97] << 8) & (0xFF << 8))), 16, 8)))  # rx skew v
        allmonitor_vals.append(str(self.signed_get(((x[98] & 0xFF) | ((x[99] << 8) & (0xFF << 8))), 16, 8)))
        allmonitor_vals.append(str(self.signed_get(((x[100] & 0xFF) | ((x[101] << 8) & (0xFF << 8))), 16, 8)))

        allmonitor_vals.append(
            str(self.signed_get(((x[102] & 0xFF) | ((x[103] << 8) & (0xFF << 8))), 16, 8)))  # rx dc h
        allmonitor_vals.append(str(self.signed_get(((x[104] & 0xFF) | ((x[105] << 8) & (0xFF << 8))), 16, 8)))
        allmonitor_vals.append(str(self.signed_get(((x[106] & 0xFF) | ((x[107] << 8) & (0xFF << 8))), 16, 8)))

        allmonitor_vals.append(
            str(self.signed_get(((x[108] & 0xFF) | ((x[109] << 8) & (0xFF << 8))), 16, 8)))  # rx dc v
        allmonitor_vals.append(str(self.signed_get(((x[110] & 0xFF) | ((x[111] << 8) & (0xFF << 8))), 16, 8)))
        allmonitor_vals.append(str(self.signed_get(((x[112] & 0xFF) | ((x[113] << 8) & (0xFF << 8))), 16, 8)))

        allmonitor_vals.append(
            str(self.signed_get(((x[114] & 0xFF) | ((x[115] << 8) & (0xFF << 8))), 16, 8)))  # tx angle h
        allmonitor_vals.append(str(self.signed_get(((x[116] & 0xFF) | ((x[117] << 8) & (0xFF << 8))), 16, 8)))
        allmonitor_vals.append(str(self.signed_get(((x[118] & 0xFF) | ((x[119] << 8) & (0xFF << 8))), 16, 8)))

        allmonitor_vals.append(
            str(self.signed_get(((x[120] & 0xFF) | ((x[121] << 8) & (0xFF << 8))), 16, 8)))  # tx angle v
        allmonitor_vals.append(str(self.signed_get(((x[122] & 0xFF) | ((x[123] << 8) & (0xFF << 8))), 16, 8)))
        allmonitor_vals.append(str(self.signed_get(((x[124] & 0xFF) | ((x[125] << 8) & (0xFF << 8))), 16, 8)))

        allmonitor_vals.append(
            str(self.unsigned_get(((x[126] & 0xFF) | ((x[127] << 8) & (0xFF << 8))), 8)))  # tx gain mism h
        allmonitor_vals.append(str(self.unsigned_get(((x[128] & 0xFF) | ((x[129] << 8) & (0xFF << 8))), 8)))
        allmonitor_vals.append(str(self.unsigned_get(((x[130] & 0xFF) | ((x[131] << 8) & (0xFF << 8))), 8)))

        allmonitor_vals.append(
            str(self.unsigned_get(((x[132] & 0xFF) | ((x[133] << 8) & (0xFF << 8))), 8)))  # tx gain mism v
        allmonitor_vals.append(str(self.unsigned_get(((x[134] & 0xFF) | ((x[135] << 8) & (0xFF << 8))), 8)))
        allmonitor_vals.append(str(self.unsigned_get(((x[136] & 0xFF) | ((x[137] << 8) & (0xFF << 8))), 8)))

        allmonitor_vals.append(
            str(self.signed_get(((x[138] & 0xFF) | ((x[139] << 8) & (0xFF << 8))), 16, 8)))  # tx skew h
        allmonitor_vals.append(str(self.signed_get(((x[140] & 0xFF) | ((x[141] << 8) & (0xFF << 8))), 16, 8)))
        allmonitor_vals.append(str(self.signed_get(((x[142] & 0xFF) | ((x[143] << 8) & (0xFF << 8))), 16, 8)))

        allmonitor_vals.append(
            str(self.signed_get(((x[144] & 0xFF) | ((x[145] << 8) & (0xFF << 8))), 16, 8)))  # tx skew v
        allmonitor_vals.append(str(self.signed_get(((x[146] & 0xFF) | ((x[147] << 8) & (0xFF << 8))), 16, 8)))
        allmonitor_vals.append(str(self.signed_get(((x[148] & 0xFF) | ((x[149] << 8) & (0xFF << 8))), 16, 8)))

        allmonitor_vals.append(
            str(self.unsigned_get(((x[150] & 0xFF) | ((x[151] << 8) & (0xFF << 8))), 16)))  # rx csr h
        allmonitor_vals.append(str(self.unsigned_get(((x[152] & 0xFF) | ((x[153] << 8) & (0xFF << 8))), 16)))
        allmonitor_vals.append(str(self.unsigned_get(((x[154] & 0xFF) | ((x[155] << 8) & (0xFF << 8))), 16)))

        allmonitor_vals.append(
            str(self.unsigned_get(((x[156] & 0xFF) | ((x[157] << 8) & (0xFF << 8))), 16)))  # rx csr v
        allmonitor_vals.append(str(self.unsigned_get(((x[158] & 0xFF) | ((x[159] << 8) & (0xFF << 8))), 16)))
        allmonitor_vals.append(str(self.unsigned_get(((x[160] & 0xFF) | ((x[161] << 8) & (0xFF << 8))), 16)))
        time.sleep(2)

        return allmonitor_vals

    def Set_dsp_power(self, vcc_mv=550):  # unit is mV
        print("Set DSP power")
        if vcc_mv <= 650:
            self.send_cdb_command_DSP(0x9114, 0, [int(vcc_mv) & 0xFF, int(vcc_mv) >> 8])
        else:
            print('current volt is ' + str(vcc_mv) + ' mv, out of range')

    def Set_dsp_power_p4(self, vcc=1719):
        print("Set DSP power")
        self.page_select(0xE4)
        self.my_i2c.write_bytes_maximum_55bytes(0xB0, [int(vcc) >> 8, int(vcc) & 0xFF])

    def Get_dsp_power(self):
        print("Get DSP power")
        TM = self.send_cdb_command_DSP(0x9116, 0, [])
        payload_res = TM[2]
        print('Get DSP power response info:' + str(payload_res))
        volt_v = (payload_res[1] << 8 | payload_res[0]) / 1000
        current_A = (payload_res[3] << 8 | payload_res[2]) / 1000
        return volt_v, current_A

    def Get_dsp_power_p4(self):
        self.page_select(0xE4)
        buffer = self.my_i2c.read_bytes_maximum_58bytes(0xB0, 2)
        dac_u12 = (buffer[0] << 8 | buffer[1]) & 0x0FFF
        return (1 - dac_u12 / 4096 * 1.024) / 261 * 68.1 + 0.5

    def GetHostUnframedTestPatternCheckerStatistics(self):
        ber_list = []
        for i in range(8):
            command_array = [0] * 1
            command_array[0] = i >> 0 & 0xFF
            TM = self.send_cdb_command_DSP(0x8382, 0, command_array)
            print("GetHostUnframedTestPatternCheckerStatistics TM:" + str(TM))
            payload_res = (TM[2])[4:]
            print(payload_res)
            bitcount = (payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                    (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)) | (
                               (payload_res[4] << 32) & (0xFF << 32)) | (
                               (payload_res[5] << 40) & (0xFF << 40)) | (
                               (payload_res[6] << 48) & (0xFF << 48)) | (
                               (payload_res[7] << 56) & (0xFF << 56))
            errorcount = int(payload_res[8] & 0xFF) | ((payload_res[9] << 8) & (0xFF << 8)) | (
                    (payload_res[10] << 16) & (0xFF << 16)) | ((payload_res[11] << 24) & (0xFF << 24))
            if int(bitcount) > 0:
                ber = '{:.4e}'.format(int(errorcount) / int(bitcount))
            else:
                ber = 'unlocked'
            ber_list.append(ber)
        return ber_list

    def RunDiagnosticUnitCapture(self, du_signal_source):
        print('RunDiagnosticUnitCapture')
        self.send_cdb_command_DSP(0x811C, 0, [du_signal_source])

    def GetDiagnosticUnitCaptureData(self):
        print('GetDiagnosticUnitCaptureData')
        TM = self.send_cdb_command_DSP_V2(0x811D, 0, [])
        print("Current TM is" + str(TM))
        response = TM[2]
        apiResponse = {
            'valid_data_elements': (response[4] & 0xFF),
            'remaining_pages': (response[5] & 0xFF),
            'remaining_cycles': (response[6] & 0xFF) | ((response[7] << 8) & (0xFF << 8)),
            'data': [
                (response[8] & 0xFF) | ((response[9] << 8) & (0xFF << 8)) | ((response[10] << 16) & (0xFF << 16)) | (
                        (response[11] << 24) & (0xFF << 24)),
                (response[12] & 0xFF) | ((response[13] << 8) & (0xFF << 8)) | ((response[14] << 16) & (0xFF << 16)) | (
                        (response[15] << 24) & (0xFF << 24)),
                (response[16] & 0xFF) | ((response[17] << 8) & (0xFF << 8)) | ((response[18] << 16) & (0xFF << 16)) | (
                        (response[19] << 24) & (0xFF << 24)),
                (response[20] & 0xFF) | ((response[21] << 8) & (0xFF << 8)) | ((response[22] << 16) & (0xFF << 16)) | (
                        (response[23] << 24) & (0xFF << 24)),
                (response[24] & 0xFF) | ((response[25] << 8) & (0xFF << 8)) | ((response[26] << 16) & (0xFF << 16)) | (
                        (response[27] << 24) & (0xFF << 24)),
                (response[28] & 0xFF) | ((response[29] << 8) & (0xFF << 8)) | ((response[30] << 16) & (0xFF << 16)) | (
                        (response[31] << 24) & (0xFF << 24)),
                (response[32] & 0xFF) | ((response[33] << 8) & (0xFF << 8)) | ((response[34] << 16) & (0xFF << 16)) | (
                        (response[35] << 24) & (0xFF << 24)),
                (response[36] & 0xFF) | ((response[37] << 8) & (0xFF << 8)) | ((response[38] << 16) & (0xFF << 16)) | (
                        (response[39] << 24) & (0xFF << 24)),
                (response[40] & 0xFF) | ((response[41] << 8) & (0xFF << 8)) | ((response[42] << 16) & (0xFF << 16)) | (
                        (response[43] << 24) & (0xFF << 24)),
                (response[44] & 0xFF) | ((response[45] << 8) & (0xFF << 8)) | ((response[46] << 16) & (0xFF << 16)) | (
                        (response[47] << 24) & (0xFF << 24)),
                (response[48] & 0xFF) | ((response[49] << 8) & (0xFF << 8)) | ((response[50] << 16) & (0xFF << 16)) | (
                        (response[51] << 24) & (0xFF << 24)),
                (response[52] & 0xFF) | ((response[53] << 8) & (0xFF << 8)) | ((response[54] << 16) & (0xFF << 16)) | (
                        (response[55] << 24) & (0xFF << 24)),
                (response[56] & 0xFF) | ((response[57] << 8) & (0xFF << 8)) | ((response[58] << 16) & (0xFF << 16)) | (
                        (response[59] << 24) & (0xFF << 24)),
                (response[60] & 0xFF) | ((response[61] << 8) & (0xFF << 8)) | ((response[62] << 16) & (0xFF << 16)) | (
                        (response[63] << 24) & (0xFF << 24)),
                (response[64] & 0xFF) | ((response[65] << 8) & (0xFF << 8)) | ((response[66] << 16) & (0xFF << 16)) | (
                        (response[67] << 24) & (0xFF << 24)),
                (response[68] & 0xFF) | ((response[69] << 8) & (0xFF << 8)) | ((response[70] << 16) & (0xFF << 16)) | (
                        (response[71] << 24) & (0xFF << 24)),
                (response[72] & 0xFF) | ((response[73] << 8) & (0xFF << 8)) | ((response[74] << 16) & (0xFF << 16)) | (
                        (response[75] << 24) & (0xFF << 24)),
                (response[76] & 0xFF) | ((response[77] << 8) & (0xFF << 8)) | ((response[78] << 16) & (0xFF << 16)) | (
                        (response[79] << 24) & (0xFF << 24)),
                (response[80] & 0xFF) | ((response[81] << 8) & (0xFF << 8)) | ((response[82] << 16) & (0xFF << 16)) | (
                        (response[83] << 24) & (0xFF << 24)),
                (response[84] & 0xFF) | ((response[85] << 8) & (0xFF << 8)) | ((response[86] << 16) & (0xFF << 16)) | (
                        (response[87] << 24) & (0xFF << 24)),
                (response[88] & 0xFF) | ((response[89] << 8) & (0xFF << 8)) | ((response[90] << 16) & (0xFF << 16)) | (
                        (response[91] << 24) & (0xFF << 24)),
                (response[92] & 0xFF) | ((response[93] << 8) & (0xFF << 8)) | ((response[94] << 16) & (0xFF << 16)) | (
                        (response[95] << 24) & (0xFF << 24)),
                (response[96] & 0xFF) | ((response[97] << 8) & (0xFF << 8)) | ((response[98] << 16) & (0xFF << 16)) | (
                        (response[99] << 24) & (0xFF << 24)),
                (response[100] & 0xFF) | ((response[101] << 8) & (0xFF << 8)) | (
                        (response[102] << 16) & (0xFF << 16)) | ((response[103] << 24) & (0xFF << 24)),
                (response[104] & 0xFF) | ((response[105] << 8) & (0xFF << 8)) | (
                        (response[106] << 16) & (0xFF << 16)) | ((response[107] << 24) & (0xFF << 24)),
                (response[108] & 0xFF) | ((response[109] << 8) & (0xFF << 8)) | (
                        (response[110] << 16) & (0xFF << 16)) | ((response[111] << 24) & (0xFF << 24)),
                (response[112] & 0xFF) | ((response[113] << 8) & (0xFF << 8)) | (
                        (response[114] << 16) & (0xFF << 16)) | ((response[115] << 24) & (0xFF << 24)),
                (response[116] & 0xFF) | ((response[117] << 8) & (0xFF << 8)) | (
                        (response[118] << 16) & (0xFF << 16)) | ((response[119] << 24) & (0xFF << 24)),
                (response[120] & 0xFF) | ((response[121] << 8) & (0xFF << 8)) | (
                        (response[122] << 16) & (0xFF << 16)) | ((response[123] << 24) & (0xFF << 24)),
                (response[124] & 0xFF) | ((response[125] << 8) & (0xFF << 8)) | (
                        (response[126] << 16) & (0xFF << 16)) | ((response[127] << 24) & (0xFF << 24)),
                (response[128] & 0xFF) | ((response[129] << 8) & (0xFF << 8)) | (
                        (response[130] << 16) & (0xFF << 16)) | ((response[131] << 24) & (0xFF << 24)),
                (response[132] & 0xFF) | ((response[133] << 8) & (0xFF << 8)) | (
                        (response[134] << 16) & (0xFF << 16)) | ((response[135] << 24) & (0xFF << 24)),
                (response[136] & 0xFF) | ((response[137] << 8) & (0xFF << 8)) | (
                        (response[138] << 16) & (0xFF << 16)) | ((response[139] << 24) & (0xFF << 24)),
                (response[140] & 0xFF) | ((response[141] << 8) & (0xFF << 8)) | (
                        (response[142] << 16) & (0xFF << 16)) | ((response[143] << 24) & (0xFF << 24)),
                (response[144] & 0xFF) | ((response[145] << 8) & (0xFF << 8)) | (
                        (response[146] << 16) & (0xFF << 16)) | ((response[147] << 24) & (0xFF << 24)),
                (response[148] & 0xFF) | ((response[149] << 8) & (0xFF << 8)) | (
                        (response[150] << 16) & (0xFF << 16)) | ((response[151] << 24) & (0xFF << 24)),
                (response[152] & 0xFF) | ((response[153] << 8) & (0xFF << 8)) | (
                        (response[154] << 16) & (0xFF << 16)) | ((response[155] << 24) & (0xFF << 24)),
                (response[156] & 0xFF) | ((response[157] << 8) & (0xFF << 8)) | (
                        (response[158] << 16) & (0xFF << 16)) | ((response[159] << 24) & (0xFF << 24)),
                (response[160] & 0xFF) | ((response[161] << 8) & (0xFF << 8)) | (
                        (response[162] << 16) & (0xFF << 16)) | ((response[163] << 24) & (0xFF << 24)),
                (response[164] & 0xFF) | ((response[165] << 8) & (0xFF << 8)) | (
                        (response[166] << 16) & (0xFF << 16)) | ((response[167] << 24) & (0xFF << 24)),
                (response[168] & 0xFF) | ((response[169] << 8) & (0xFF << 8)) | (
                        (response[170] << 16) & (0xFF << 16)) | ((response[171] << 24) & (0xFF << 24)),
                (response[172] & 0xFF) | ((response[173] << 8) & (0xFF << 8)) | (
                        (response[174] << 16) & (0xFF << 16)) | ((response[175] << 24) & (0xFF << 24)),
                (response[176] & 0xFF) | ((response[177] << 8) & (0xFF << 8)) | (
                        (response[178] << 16) & (0xFF << 16)) | ((response[179] << 24) & (0xFF << 24)),
                (response[180] & 0xFF) | ((response[181] << 8) & (0xFF << 8)) | (
                        (response[182] << 16) & (0xFF << 16)) | ((response[183] << 24) & (0xFF << 24)),
                (response[184] & 0xFF) | ((response[185] << 8) & (0xFF << 8)) | (
                        (response[186] << 16) & (0xFF << 16)) | ((response[187] << 24) & (0xFF << 24)),
                (response[188] & 0xFF) | ((response[189] << 8) & (0xFF << 8)) | (
                        (response[190] << 16) & (0xFF << 16)) | ((response[191] << 24) & (0xFF << 24)),
                (response[192] & 0xFF) | ((response[193] << 8) & (0xFF << 8)) | (
                        (response[194] << 16) & (0xFF << 16)) | ((response[195] << 24) & (0xFF << 24)),
                (response[196] & 0xFF) | ((response[197] << 8) & (0xFF << 8)) | (
                        (response[198] << 16) & (0xFF << 16)) | ((response[199] << 24) & (0xFF << 24)),
                (response[200] & 0xFF) | ((response[201] << 8) & (0xFF << 8)) | (
                        (response[202] << 16) & (0xFF << 16)) | ((response[203] << 24) & (0xFF << 24)),
                (response[204] & 0xFF) | ((response[205] << 8) & (0xFF << 8)) | (
                        (response[206] << 16) & (0xFF << 16)) | ((response[207] << 24) & (0xFF << 24)),
                (response[208] & 0xFF) | ((response[209] << 8) & (0xFF << 8)) | (
                        (response[210] << 16) & (0xFF << 16)) | ((response[211] << 24) & (0xFF << 24)),
                (response[212] & 0xFF) | ((response[213] << 8) & (0xFF << 8)) | (
                        (response[214] << 16) & (0xFF << 16)) | ((response[215] << 24) & (0xFF << 24)),
                (response[216] & 0xFF) | ((response[217] << 8) & (0xFF << 8)) | (
                        (response[218] << 16) & (0xFF << 16)) | ((response[219] << 24) & (0xFF << 24)),
                (response[220] & 0xFF) | ((response[221] << 8) & (0xFF << 8)) | (
                        (response[222] << 16) & (0xFF << 16)) | ((response[223] << 24) & (0xFF << 24)),
                (response[224] & 0xFF) | ((response[225] << 8) & (0xFF << 8)) | (
                        (response[226] << 16) & (0xFF << 16)) | ((response[227] << 24) & (0xFF << 24)),
                (response[228] & 0xFF) | ((response[229] << 8) & (0xFF << 8)) | (
                        (response[230] << 16) & (0xFF << 16)) | ((response[231] << 24) & (0xFF << 24)),
                (response[232] & 0xFF) | ((response[233] << 8) & (0xFF << 8)) | (
                        (response[234] << 16) & (0xFF << 16)) | ((response[235] << 24) & (0xFF << 24)),
                (response[236] & 0xFF) | ((response[237] << 8) & (0xFF << 8)) | (
                        (response[238] << 16) & (0xFF << 16)) | ((response[239] << 24) & (0xFF << 24)),
                (response[240] & 0xFF) | ((response[241] << 8) & (0xFF << 8)) | (
                        (response[242] << 16) & (0xFF << 16)) | ((response[243] << 24) & (0xFF << 24)),
                (response[244] & 0xFF) | ((response[245] << 8) & (0xFF << 8)) | (
                        (response[246] << 16) & (0xFF << 16)) | ((response[247] << 24) & (0xFF << 24)),
                (response[248] & 0xFF) | ((response[249] << 8) & (0xFF << 8)) | (
                        (response[250] << 16) & (0xFF << 16)) | ((response[251] << 24) & (0xFF << 24)),
                (response[252] & 0xFF) | ((response[253] << 8) & (0xFF << 8)) | (
                        (response[254] << 16) & (0xFF << 16)) | ((response[255] << 24) & (0xFF << 24)),
                (response[256] & 0xFF) | ((response[257] << 8) & (0xFF << 8)) | (
                        (response[258] << 16) & (0xFF << 16)) | ((response[259] << 24) & (0xFF << 24)),
                (response[260] & 0xFF) | ((response[261] << 8) & (0xFF << 8)) | (
                        (response[262] << 16) & (0xFF << 16)) | ((response[263] << 24) & (0xFF << 24)),
                (response[264] & 0xFF) | ((response[265] << 8) & (0xFF << 8)) | (
                        (response[266] << 16) & (0xFF << 16)) | ((response[267] << 24) & (0xFF << 24)),
                (response[268] & 0xFF) | ((response[269] << 8) & (0xFF << 8)) | (
                        (response[270] << 16) & (0xFF << 16)) | ((response[271] << 24) & (0xFF << 24)),
                (response[272] & 0xFF) | ((response[273] << 8) & (0xFF << 8)) | (
                        (response[274] << 16) & (0xFF << 16)) | ((response[275] << 24) & (0xFF << 24)),
                (response[276] & 0xFF) | ((response[277] << 8) & (0xFF << 8)) | (
                        (response[278] << 16) & (0xFF << 16)) | ((response[279] << 24) & (0xFF << 24)),
                (response[280] & 0xFF) | ((response[281] << 8) & (0xFF << 8)) | (
                        (response[282] << 16) & (0xFF << 16)) | ((response[283] << 24) & (0xFF << 24)),
                (response[284] & 0xFF) | ((response[285] << 8) & (0xFF << 8)) | (
                        (response[286] << 16) & (0xFF << 16)) | ((response[287] << 24) & (0xFF << 24)),
                (response[288] & 0xFF) | ((response[289] << 8) & (0xFF << 8)) | (
                        (response[290] << 16) & (0xFF << 16)) | ((response[291] << 24) & (0xFF << 24)),
                (response[292] & 0xFF) | ((response[293] << 8) & (0xFF << 8)) | (
                        (response[294] << 16) & (0xFF << 16)) | ((response[295] << 24) & (0xFF << 24)),
                (response[296] & 0xFF) | ((response[297] << 8) & (0xFF << 8)) | (
                        (response[298] << 16) & (0xFF << 16)) | ((response[299] << 24) & (0xFF << 24)),
                (response[300] & 0xFF) | ((response[301] << 8) & (0xFF << 8)) | (
                        (response[302] << 16) & (0xFF << 16)) | ((response[303] << 24) & (0xFF << 24)),
                (response[304] & 0xFF) | ((response[305] << 8) & (0xFF << 8)) | (
                        (response[306] << 16) & (0xFF << 16)) | ((response[307] << 24) & (0xFF << 24)),
                (response[308] & 0xFF) | ((response[309] << 8) & (0xFF << 8)) | (
                        (response[310] << 16) & (0xFF << 16)) | ((response[311] << 24) & (0xFF << 24)),
                (response[312] & 0xFF) | ((response[313] << 8) & (0xFF << 8)) | (
                        (response[314] << 16) & (0xFF << 16)) | ((response[315] << 24) & (0xFF << 24)),
                (response[316] & 0xFF) | ((response[317] << 8) & (0xFF << 8)) | (
                        (response[318] << 16) & (0xFF << 16)) | ((response[319] << 24) & (0xFF << 24)),
                (response[320] & 0xFF) | ((response[321] << 8) & (0xFF << 8)) | (
                        (response[322] << 16) & (0xFF << 16)) | ((response[323] << 24) & (0xFF << 24)),
                (response[324] & 0xFF) | ((response[325] << 8) & (0xFF << 8)) | (
                        (response[326] << 16) & (0xFF << 16)) | ((response[327] << 24) & (0xFF << 24)),
                (response[328] & 0xFF) | ((response[329] << 8) & (0xFF << 8)) | (
                        (response[330] << 16) & (0xFF << 16)) | ((response[331] << 24) & (0xFF << 24)),
                (response[332] & 0xFF) | ((response[333] << 8) & (0xFF << 8)) | (
                        (response[334] << 16) & (0xFF << 16)) | ((response[335] << 24) & (0xFF << 24)),
                (response[336] & 0xFF) | ((response[337] << 8) & (0xFF << 8)) | (
                        (response[338] << 16) & (0xFF << 16)) | ((response[339] << 24) & (0xFF << 24)),
                (response[340] & 0xFF) | ((response[341] << 8) & (0xFF << 8)) | (
                        (response[342] << 16) & (0xFF << 16)) | ((response[343] << 24) & (0xFF << 24)),
                (response[344] & 0xFF) | ((response[345] << 8) & (0xFF << 8)) | (
                        (response[346] << 16) & (0xFF << 16)) | ((response[347] << 24) & (0xFF << 24)),
                (response[348] & 0xFF) | ((response[349] << 8) & (0xFF << 8)) | (
                        (response[350] << 16) & (0xFF << 16)) | ((response[351] << 24) & (0xFF << 24)),
                (response[352] & 0xFF) | ((response[353] << 8) & (0xFF << 8)) | (
                        (response[354] << 16) & (0xFF << 16)) | ((response[355] << 24) & (0xFF << 24)),
                (response[356] & 0xFF) | ((response[357] << 8) & (0xFF << 8)) | (
                        (response[358] << 16) & (0xFF << 16)) | ((response[359] << 24) & (0xFF << 24)),
                (response[360] & 0xFF) | ((response[361] << 8) & (0xFF << 8)) | (
                        (response[362] << 16) & (0xFF << 16)) | ((response[363] << 24) & (0xFF << 24)),
                (response[364] & 0xFF) | ((response[365] << 8) & (0xFF << 8)) | (
                        (response[366] << 16) & (0xFF << 16)) | ((response[367] << 24) & (0xFF << 24)),
                (response[368] & 0xFF) | ((response[369] << 8) & (0xFF << 8)) | (
                        (response[370] << 16) & (0xFF << 16)) | ((response[371] << 24) & (0xFF << 24)),
                (response[372] & 0xFF) | ((response[373] << 8) & (0xFF << 8)) | (
                        (response[374] << 16) & (0xFF << 16)) | ((response[375] << 24) & (0xFF << 24)),
                (response[376] & 0xFF) | ((response[377] << 8) & (0xFF << 8)) | (
                        (response[378] << 16) & (0xFF << 16)) | ((response[379] << 24) & (0xFF << 24)),
                (response[380] & 0xFF) | ((response[381] << 8) & (0xFF << 8)) | (
                        (response[382] << 16) & (0xFF << 16)) | ((response[383] << 24) & (0xFF << 24)),
                (response[384] & 0xFF) | ((response[385] << 8) & (0xFF << 8)) | (
                        (response[386] << 16) & (0xFF << 16)) | ((response[387] << 24) & (0xFF << 24)),
                (response[388] & 0xFF) | ((response[389] << 8) & (0xFF << 8)) | (
                        (response[390] << 16) & (0xFF << 16)) | ((response[391] << 24) & (0xFF << 24)),
            ],
        }
        return apiResponse

    def ReadRegister(self, addr):
        command_array = [0] * 4
        command_array[0] = addr >> 0 & 0xFF
        command_array[1] = addr >> 8 & 0xFF
        command_array[2] = addr >> 16 & 0xFF
        command_array[3] = addr >> 24 & 0xFF

        TM = self.send_cdb_command_DSP(0x8128, 0, command_array)
        print("Read register TM:" + str(TM))
        payload_res = (TM[2])[4:]
        print(payload_res)
        return (payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24))

    def WriteRegister(self, addr, value):
        command_array = [0] * 8
        command_array[0] = addr >> 0 & 0xFF
        command_array[1] = addr >> 8 & 0xFF
        command_array[2] = addr >> 16 & 0xFF
        command_array[3] = addr >> 24 & 0xFF
        command_array[4] = value >> 0 & 0xFF
        command_array[5] = value >> 8 & 0xFF
        command_array[6] = value >> 16 & 0xFF
        command_array[7] = value >> 24 & 0xFF
        self.send_cdb_command_DSP(0x8129, 0, command_array)

    def get_dsp_fw_ver(self):
        TM = self.send_cdb_command_DSP(0x8110, 0, [0])
        print("ReadFWVersion TM:" + str(TM))
        payload_res = (TM[2])[4:]
        return hex((payload_res[0] & 0xFF) | ((payload_res[1] << 8) & (0xFF << 8)) | (
                (payload_res[2] << 16) & (0xFF << 16)) | ((payload_res[3] << 24) & (0xFF << 24)))

    # ===========================EEPROM Operation=========================
    def read_eeprom_page(self, path="A922_QDD-DD 400G Coherent Memory Map.xls", page="LP_00H"):
        try:
            df = pd.read_excel(path, sheet_name=page, usecols=[1, 2], names=['addr', 'description'], skiprows=0,
                               nrows=128, keep_default_na=False)
            description = df['description'].tolist()
            # address = df['addr'].tolist()
            # address_dec = [int(val, 16) for val in address]
        except:
            print('Can not get register description for page:' + page + 'from memory map file')
            description = [''] * 128
        if page == "LP_00H":
            data = self.my_i2c.read_bytes_maximum_128bytes(0, 128)
            address_dec = ['{:02d}'.format(i) for i in range(128)]
            address = ['0x' + '{:02x}'.format(i).upper() for i in range(128)]
        else:
            self.page_select(int(page[3:5], 16))
            data = self.my_i2c.read_bytes_maximum_128bytes(0x80, 128)
            address_dec = ['{:02d}'.format(i) for i in range(128, 256)]
            address = ['0x' + '{:02x}'.format(i).upper() for i in range(128, 256)]
        data_str = []
        for i in data:
            data_str.append('0x' + '{:02x}'.format(i).upper())
        return [address_dec, address, description, data_str]

    def get_ddm_module(self):
        ddm_info = {}
        self.page_select(0x01)
        val = self.my_i2c.read_bytes_maximum_58bytes(145, 1)[0]
        aux1_type = val & 0x01  # 1 means TEC current, 0 means reserved
        aux2_type = (val >> 1) & 0x01  # 1 means TEC current, 0 means laser temp
        aux3_type = (val >> 2) & 0x01  # 1 means Vcc2, 0 means laser temp
        buff = self.my_i2c.read_bytes_maximum_58bytes(0x0E, 12)
        ddm_adc = []
        for msb, lsb in zip(buff[::2], buff[1::2]):
            ddm_adc.append(msb << 8 | lsb)
        if ddm_adc[0] > 32767:
            temp = ddm_adc[0] - 65536
        else:
            temp = ddm_adc[0]
        ddm_info.update(temp_ddm=temp / 256)
        ddm_info.update(vcc_ddm=ddm_adc[1] / 10000)
        # print(ddm_info)
        if aux1_type:
            if ddm_adc[2] > 32767:
                tec_cur = ddm_adc[2] - 65536
            else:
                tec_cur = ddm_adc[2]
            ddm_info.update(aux1=tec_cur / 32767)
        else:
            ddm_info.update(aux1=ddm_adc[2])
        if ddm_adc[3] > 32767:
            aux2_s16 = ddm_adc[3] - 65536
        else:
            aux2_s16 = ddm_adc[3]
        if aux2_type:
            ddm_info.update(aux2=aux2_s16 / 32767)
        else:
            ddm_info.update(aux2=aux2_s16 / 256)
        if aux3_type:
            ddm_info.update(aux3=ddm_adc[4] / 10000)
        else:
            if ddm_adc[4] > 32767:
                aux3_s16 = ddm_adc[4] - 65536
            else:
                aux3_s16 = ddm_adc[4]
            ddm_info.update(aux3=aux3_s16 / 256)
        ddm_info.update(custom_monitor=ddm_adc[5])
        # print(ddm_info)
        return ddm_info

    def get_ddm_lane(self):
        self.page_select(0x11)
        buff = []
        for add in [154, 170, 186]:
            buff += self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data_u16 = []
        for msb, lsb in zip(buff[::2], buff[1::2]):
            data_u16.append(msb << 8 | lsb)
        # print(data_u16)
        ddm_lane0 = {}
        try:
            ddm_lane0.update(Tx_pwr_dbm=10 * log10(data_u16[0] / 10000))
        except:
            ddm_lane0.update(Tx_pwr_dbm=float('-inf'))
        try:
            ddm_lane0.update(Tx_bias_mA=data_u16[1] * 2 / 1000)
        except:
            ddm_lane0.update(Tx_bias_mA=float('-inf'))
        try:
            ddm_lane0.update(Rx_pwr_dbm=10 * log10(data_u16[2] / 10000))
        except:
            ddm_lane0.update(Rx_pwr_dbm=float('-inf'))
        self.page_select(0x24)
        jj = self.my_i2c.read_bytes_maximum_58bytes(0x9C, 2)
        yy = jj[0] << 8 | jj[1]
        if yy > 32767:
            yy = yy - 65536
        data_u16.append(yy)
        try:
            # ddm_lane0.update(Rx_pwr_signal=10 * log10(data_u16[3] / 10000))
            ddm_lane0.update(Rx_pwr_signal=data_u16[3] / 100)
        except:
            ddm_lane0.update(Rx_pwr_signal=float('-inf'))
        return ddm_lane0, data_u16

    def get_data_path_state(self):
        self.page_select(0x11)
        return self.my_i2c.read_bytes_maximum_58bytes(0x80, 1)[0] & 0x0F

    def get_module_state(self):
        value = self.my_i2c.read_bytes_maximum_58bytes(0x03, 1)[0] & 0x0F
        signal_interrupt = value & 0x01
        state_module = (value & 0x0F) >> 1
        return [signal_interrupt, state_module]

    def read_single_value(self, sheet, add):
        dict = {"LP_00H": 0x00, "UP_00H": 0x00, "UP_01H": 0x01, "UP_02H": 0x02, "UP_03H_USEREEPROM": 0x03,
                "UP_04H": 0x04,
                "UP_10H": 0x10, "UP_11H": 0x11, "UP_12H": 0x12, "UP_13H": 0x13, "UP_14H": 0x14, "UP_20H": 0x20,
                "UP_21H": 0x21, "UP_22H": 0x22, "UP_23H": 0x23, "UP_24H": 0x24, "UP_25H": 0x25, "UP_26H": 0x26,
                "UP_27H": 0x27, "UP_28H": 0x28, "UP_29H": 0x29, "UP_2AH": 0x2A, "UP_2BH": 0x2B, "UP_2CH": 0x2C,
                "UP_2DH": 0x2D, "UP_2FH": 0x2F,
                "UP_30H": 0x30, "UP_31H": 0x31, "UP_32H": 0x32, "UP_33H": 0x33, "UP_34H": 0x34,
                "UP_35H": 0x35, "UP_38H": 0x38, "UP_3AH": 0x3A, "UP_3BH": 0x3B, "UP_41H": 0x41, "UP_42H": 0x42,
                "UP_85H": 0x85, "UP_9FH": 0x9F, "UP_A0H": 0xA0, "UP_A1H": 0xA1,
                "UP_C0H": 0xC0, "UP_C1H": 0xC1, "UP_C2H": 0xC2, "UP_C3H": 0xC3, "UP_C4H": 0xC4, "UP_C5H": 0xC5,
                "UP_CFH": 0xCF, "UP_E0H": 0xE0, "UP_E1H": 0xE1,
                "UP_E2H": 0xE2, "UP_E3H": 0xE3, "UP_E4H": 0xE4, "UP_E5H": 0xE5, "UP_E6H": 0xE6, "UP_E7H": 0xE7}

        sheetnum = list(dict.values())[list(dict.keys()).index(sheet)]
        # print(sheetnum)
        self.page_select(sheetnum)
        result = self.my_i2c.read_bytes_maximum_58bytes(add, 1)
        return result[0]

    def write_single_value(self, sheet, add, data):
        dict = {"LP_00H": 0x00, "UP_00H": 0x00, "UP_01H": 0x01, "UP_02H": 0x02, "UP_03H_USEREEPROM": 0x03,
                "UP_04H": 0x04,
                "UP_10H": 0x10, "UP_11H": 0x11, "UP_12H": 0x12, "UP_13H": 0x13, "UP_14H": 0x14, "UP_20H": 0x20,
                "UP_21H": 0x21, "UP_22H": 0x22, "UP_23H": 0x23, "UP_24H": 0x24, "UP_25H": 0x25, "UP_26H": 0x26,
                "UP_27H": 0x27, "UP_28H": 0x28, "UP_29H": 0x29, "UP_2AH": 0x2A, "UP_2BH": 0x2B, "UP_2CH": 0x2C,
                "UP_2DH": 0x2D, "UP_2FH": 0x2F,
                "UP_30H": 0x30, "UP_31H": 0x31, "UP_32H": 0x32, "UP_33H": 0x33, "UP_34H": 0x34,
                "UP_35H": 0x35, "UP_38H": 0x38, "UP_3AH": 0x3A, "UP_3BH": 0x3B, "UP_41H": 0x41, "UP_42H": 0x42,
                "UP_85H": 0x85, "UP_9FH": 0x9F, "UP_A0H": 0xA0, "UP_A1H": 0xA1,
                "UP_C0H": 0xC0, "UP_C1H": 0xC1, "UP_C2H": 0xC2, "UP_C3H": 0xC3, "UP_C4H": 0xC4, "UP_C5H": 0xC5,
                "UP_CFH": 0xCF, "UP_E0H": 0xE0, "UP_E1H": 0xE1,
                "UP_E2H": 0xE2, "UP_E3H": 0xE3, "UP_E4H": 0xE4, "UP_E5H": 0xE5, "UP_E6H": 0xE6, "UP_E7H": 0xE7}

        sheetnum = list(dict.values())[list(dict.keys()).index(sheet)]
        # print(sheetnum)
        self.page_select(sheetnum)
        self.my_i2c.write_bytes_maximum_55bytes(add, data)

    def read_4registers_value(self, sheet, add):
        dict = {"LP_00H": 0x00, "UP_00H": 0x00, "UP_01H": 0x01, "UP_02H": 0x02, "UP_03H_USEREEPROM": 0x03,
                "UP_04H": 0x04,
                "UP_10H": 0x10, "UP_11H": 0x11, "UP_12H": 0x12, "UP_13H": 0x13, "UP_14H": 0x14, "UP_20H": 0x20,
                "UP_21H": 0x21, "UP_22H": 0x22, "UP_23H": 0x23, "UP_24H": 0x24, "UP_25H": 0x25, "UP_26H": 0x26,
                "UP_27H": 0x27, "UP_28H": 0x28, "UP_29H": 0x29, "UP_2AH": 0x2A, "UP_2BH": 0x2B, "UP_2CH": 0x2C,
                "UP_2DH": 0x2D, "UP_2FH": 0x2F,
                "UP_30H": 0x30, "UP_31H": 0x31, "UP_32H": 0x32, "UP_33H": 0x33, "UP_34H": 0x34,
                "UP_35H": 0x35, "UP_38H": 0x38, "UP_3AH": 0x3A, "UP_3BH": 0x3B, "UP_41H": 0x41, "UP_42H": 0x42,
                "UP_85H": 0x85, "UP_9FH": 0x9F, "UP_A0H": 0xA0, "UP_A1H": 0xA1,
                "UP_C0H": 0xC0, "UP_C1H": 0xC1, "UP_C2H": 0xC2, "UP_C3H": 0xC3, "UP_C4H": 0xC4, "UP_C5H": 0xC5,
                "UP_CFH": 0xCF, "UP_E0H": 0xE0, "UP_E1H": 0xE1,
                "UP_E2H": 0xE2, "UP_E3H": 0xE3, "UP_E4H": 0xE4, "UP_E5H": 0xE5, "UP_E6H": 0xE6, "UP_E7H": 0xE7}

        sheetnum = list(dict.values())[list(dict.keys()).index(sheet)]
        # print(sheetnum)
        self.page_select(sheetnum)
        result = self.my_i2c.read_bytes_maximum_58bytes(add, 4)
        return result[0:4]

    def get_module_info(self):
        module_info = {}
        self.page_select(0x00)
        data = self.my_i2c.read_bytes_maximum_128bytes(0x80, 62)
        module_info.update(identifier=data[0])
        module_info.update(vendor_name=(bytearray(data[1:17])).decode(encoding='utf-8').strip())
        module_info.update(vendor_pn=(bytearray(data[20:36])).decode(encoding='utf-8').strip())
        module_info.update(vendor_rev=(bytearray(data[36:38])).decode(encoding='utf-8').strip())
        module_info.update(vendor_sn=(bytearray(data[38:54])).decode(encoding='utf-8').strip())
        module_info.update(datecode=(bytearray(data[54:62])).decode(encoding='utf-8').strip())
        return module_info

    def get_fw_pn_info(self):
        self.page_select(0x85)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0x80, 14)
        fw_pn = (bytearray(buff[0:10])).decode(encoding='utf-8')
        fw_ver = '.'.join([str(x) for x in buff[10:14]])
        return fw_pn, fw_ver

    def get_evb_fw_pn_info(self):
        buff = self.my_i2c.read_EVB_FW_Ver()
        print(buff)
        fw_pn = (bytearray(buff[0:10])).decode(encoding='utf-8')
        print(fw_pn)
        fw_ver = '.'.join([str(x) for x in buff[10:14]])
        print(fw_ver)
        return fw_pn, fw_ver

    def update_sn(self, sn=''):
        sn_data = []
        for char in sn:
            sn_data.append(ord(char))
        # print(sn_data)
        self.page_select(0x00)
        index = 0
        for val in (sn_data + [0x20] * 16)[0:16]:
            self.my_i2c.write_bytes_maximum_55bytes(166 + index, [val])
            index += 1

    def get_global_controls(self):
        buff = self.my_i2c.read_bytes_maximum_58bytes(0x1A, 1)[0]
        global_controls = {}
        global_controls.update(LowPwr=(buff >> 6) & 0x01)
        global_controls.update(Squelch_control=(buff >> 5) & 0x01)
        global_controls.update(ForceLowPwr=(buff >> 4) & 0x01)
        global_controls.update(Software_Reset=(buff >> 3) & 0x01)
        return global_controls

    def get_module_mission_mode(self):
        self.page_select(0xC0)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0x89, 1)
        return buff[0]

    def read_AVS_voltage(self):
        coeff = 0.0012
        self.page_select(0xC2)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0xE2, 2)
        time.sleep(0.01)
        AVS_raw = (buff[0] << 2) | ((buff[1] & 0xC0) >> 6)
        AVS_value = round(float(AVS_raw * coeff), 1)
        return AVS_value

    def write_AVS_voltage(self, value):
        coeff = 0.0012
        self.page_select(0xC2)
        AVS_origin = int(float(value) / coeff)
        self.my_i2c.write_bytes_maximum_55bytes(0xE2, [(AVS_origin >> 2) & 0xFF])
        time.sleep(0.01)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0xE3, 1)
        time.sleep(0.01)
        self.my_i2c.write_bytes_maximum_55bytes(0xE3, [(AVS_origin & 0x3) << 6 | buff])
        time.sleep(0.01)

    def set_module_mission_mode(self, value):
        self.page_select(0xC0)
        self.my_i2c.write_bytes_maximum_55bytes(0x89, [value])

    def unlock_module(self, level):
        pwlevel = {'Oplink_PWD_level': 0, 'Custom_PWD_level': 1, "MSA_PWD_level": 2}
        level_raw = list(pwlevel.values())[list(pwlevel.keys()).index(level)]
        for i in range(3):
            if level_raw == 0:
                self.my_i2c.write_bytes_maximum_55bytes(0x7A, [0xCF, 0xD0, 0xCC, 0xCB])
            elif level_raw == 1:
                self.my_i2c.write_bytes_maximum_55bytes(0x7A, [0xC3, 0xD5, 0xD3, 0xD4])
            elif level_raw == 2:
                self.my_i2c.write_bytes_maximum_55bytes(0x7A, [0x00, 0x00, 0x10, 0x11])
            time.sleep(1)
            self.page_select(0xE2)
            data = self.my_i2c.read_bytes_maximum_58bytes(0x81, 1)
            if data[0] in [2, 3]:
                return 'true'
        return 'fail'

    def tx_disable(self, state='ON'):
        if state == 'ON':
            self.page_select(0x10)
            val = self.my_i2c.read_bytes_maximum_58bytes(130, 1)[0] | 0x01
            self.my_i2c.write_bytes_maximum_55bytes(130, [val])
            time.sleep(1)
            start_time = time.time()
            while True:
                db_state = self.get_data_path_state()
                if db_state == 0x07:
                    break
                elif (time.time() - start_time) >= 10:
                    print('time out for tx disable operation, data path state is 0x' + '{:2d}'.format(db_state))
                    sys.exit()
                else:
                    time.sleep(1)
        elif state == 'OFF':
            self.page_select(0x10)
            val = self.my_i2c.read_bytes_maximum_58bytes(130, 1)[0] & 0xFE
            self.my_i2c.write_bytes_maximum_55bytes(130, [val])
            time.sleep(5)
            start_time = time.time()
            while True:
                db_state = self.get_data_path_state()
                module_state = self.get_module_state()[1]
                if db_state == 0x04 and module_state == 0x03:
                    break
                elif (time.time() - start_time) >= 180:
                    print('time out for tx enable operation, data path state is ' + '{:2d}'.format(
                        db_state) + ', module state is ' + '{:2d}'.format(module_state))
                    break
                else:
                    time.sleep(5)

    def lp_mode_set(self, state='ON'):
        if state == 'ON':
            buff = self.my_i2c.read_bytes_maximum_58bytes(0x1A, 1)[0]
            self.my_i2c.write_bytes_maximum_55bytes(0x1A, [(buff & 0xEF) | (1 << 4)])
            time.sleep(5)
            start_time = time.time()
            while True:
                if (self.get_data_path_state() == 0x01) and (self.get_module_state()[1] == 0x01):
                    break
                elif (time.time() - start_time) >= 60:
                    print('Timeout, data path state is ' + '{:02x}'.format(
                        self.get_data_path_state()) + ', module state is ' + '{:02x}'.format(
                        self.get_module_state()[1]))
                    sys.exit()
                else:
                    time.sleep(5)
        elif state == 'OFF':
            buff = self.my_i2c.read_bytes_maximum_58bytes(0x1A, 1)[0]
            self.my_i2c.write_bytes_maximum_55bytes(0x1A, [(buff & 0xEF) | (0 << 4)])
            time.sleep(5)
            start_time = time.time()
            while True:
                if (self.get_data_path_state() == 0x04) and (self.get_module_state()[1] == 0x03):
                    break
                elif (time.time() - start_time) >= 240:
                    print('Timeout, data path state is ' + '{:02x}'.format(
                        self.get_data_path_state()) + ', module state is ' + '{:02x}'.format(
                        self.get_module_state()[1]))
                    sys.exit()
                else:
                    time.sleep(10)
        else:
            print(state + ' is not supported.')

    def lowpwr_force(self, state='ON'):  # without checking module state
        if state == 'ON':
            buff = self.my_i2c.read_bytes_maximum_58bytes(0x1A, 1)[0]
            self.my_i2c.write_bytes_maximum_55bytes(0x1A, [(buff & 0xEF) | (1 << 4)])
        elif state == 'OFF':
            buff = self.my_i2c.read_bytes_maximum_58bytes(0x1A, 1)[0]
            self.my_i2c.write_bytes_maximum_55bytes(0x1A, [(buff & 0xEF) | (0 << 4)])
        else:
            print(state + ' is not supported.')

    def lowpwr(self, state='ON'):  # without checking module state
        if state == 'ON':
            buff = self.my_i2c.read_bytes_maximum_58bytes(0x1A, 1)[0]
            self.my_i2c.write_bytes_maximum_55bytes(0x1A, [(buff & 0xBF) | (1 << 6)])
        elif state == 'OFF':
            buff = self.my_i2c.read_bytes_maximum_58bytes(0x1A, 1)[0]
            self.my_i2c.write_bytes_maximum_55bytes(0x1A, [(buff & 0xBF) | (0 << 6)])
        else:
            print(state + ' is not supported.')

    def lowpwr_hw(self, state='ON'):
        if self.ch == 0:  ## QDD1
            if state == 'ON':
                self.my_i2c.gpio_set_evb(gpio_id=3, value=1)
            if state == 'OFF':
                self.my_i2c.gpio_set_evb(gpio_id=3, value=0)
        elif self.ch == 1:  ## QDD2
            if state == 'ON':
                self.my_i2c.gpio_set_evb(gpio_id=40, value=1)
            if state == 'OFF':
                self.my_i2c.gpio_set_evb(gpio_id=40, value=0)
        else:
            print('Current ch is' + str(self.ch) + ' can not be supported for lpmode hw pin.')

    def reset_sw(self, state='ON'):
        print('soft reset module')
        if state == 'ON':
            buff = self.my_i2c.read_bytes_maximum_58bytes(0x1A, 1)[0]
            self.my_i2c.write_bytes_maximum_55bytes(0x1A, [(buff & 0xF7) | (1 << 3)])
        elif state == 'OFF':
            buff = self.my_i2c.read_bytes_maximum_58bytes(0x1A, 1)[0]
            self.my_i2c.write_bytes_maximum_55bytes(0x1A, [(buff & 0xF7) | (0 << 3)])
        else:
            print('Current state is' + state + ' can not be supported')

    def reset_hw(self, state='ON'):
        if self.ch == 0:  ## QDD1
            if state == 'ON':
                self.my_i2c.gpio_set_evb(gpio_id=1, value=0)
            if state == 'OFF':
                self.my_i2c.gpio_set_evb(gpio_id=1, value=1)
        elif self.ch == 1:  ## QDD2
            if state == 'ON':
                self.my_i2c.gpio_set_evb(gpio_id=38, value=0)
            if state == 'OFF':
                self.my_i2c.gpio_set_evb(gpio_id=38, value=1)
        else:
            print('Current ch is' + str(self.ch) + ' can not be supported for reset hw pin.')

    def get_rx_los_flag_lane0(self):
        self.page_select(0x11)
        for i in range(2):  # read rx los flag two times since it's a latched flag
            buff = self.my_i2c.read_bytes_maximum_58bytes(147, 1)[0]
            time.sleep(1)
        if (buff & 0x01) == 0x01:
            return True
        elif (buff & 0x01) == 0x00:
            return False
        else:
            print(' los value is ' + str(buff))

    def check_dsp_status(self):
        self.page_select(0xE0)
        start_time = time.time()
        while True:
            dsp_status = self.my_i2c.read_bytes_maximum_58bytes(0x8D, 1)[0]
            print('DSP status is:' + hex(dsp_status))
            if dsp_status == 0xFF:
                return True
            elif (time.time() - start_time) >= 240:
                print('Timeout')
                return False
            else:
                time.sleep(10)

    def check_module_ready(self):
        time.sleep(5)
        start_time = time.time()
        while True:
            db_state = self.get_data_path_state()
            module_state = self.get_module_state()[1]
            print(
                'module module: data path state is ' + '{:02x}'.format(
                    db_state) + ', module state is ' + '{:02x}'.format(
                    module_state))
            if (db_state == 0x04) and (module_state == 0x03):
                print('it costs almost ' + '{:.2f}'.format(time.time() - start_time) + 's to stabilize module.')
                return True
            if (time.time() - start_time) >= 240:
                print('Timeout')
                return False
            else:
                time.sleep(10)
                continue

    # ===========================ITLA Operation=========================
    # MSA comply

    def itla_chn_num_set(self, itla_chn):
        self.page_select(0x12)
        if itla_chn < 0:
            itla_chn += 65536
        self.my_i2c.write_bytes_maximum_55bytes(0x88, [int(itla_chn) >> 8, int(itla_chn) & 0xFF])

    def itla_chn_num_get(self):
        self.page_select(0x12)
        chn_data = self.my_i2c.read_bytes_maximum_58bytes(0x88, 2)
        cur_chn = (chn_data[0] << 8 | chn_data[1])
        if cur_chn > 32767:
            cur_chn -= 65536
        return cur_chn

    def itla_freq_get(self, unit='thz'):
        self.page_select(0x12)
        fre_data = self.my_i2c.read_bytes_maximum_58bytes(0xA8, 4)
        cur_freq = (fre_data[0] << 8 | fre_data[1]) + (fre_data[2] << 8 | fre_data[3]) * 0.05 * 0.001
        if unit == 'thz':
            return cur_freq
        elif unit == 'ghz':
            return cur_freq * 1000
        else:
            print(unit + 'is invalid, only support thz or ghz')
            return None

    def itla_freq_set(self, freq_thz):
        residual_error = 0.001
        grid_ghz = self.itla_grid_spac_get()
        if (freq_thz - 193.1) / grid_ghz * 1000 < 0:
            itla_ch = int((freq_thz - 193.1) / grid_ghz * 1000 - residual_error)
        else:
            itla_ch = int((freq_thz - 193.1) / grid_ghz * 1000 + residual_error)
        self.itla_chn_num_set(itla_ch)  # default module is dut module
        print('Set frequency to ' + str(freq_thz) + 'Thz, CH is ' + '{:2d}'.format(itla_ch))
        return itla_ch

    def itla_status_progress_get(self):
        self.page_select(0x12)
        progress_data_raw = self.my_i2c.read_bytes_maximum_58bytes(0xDF, 1)
        return progress_data_raw[0] & 0x02

    def itla_status_waveunlocked_get(self):
        self.page_select(0x12)
        waveunlocked_data_raw = self.my_i2c.read_bytes_maximum_58bytes(0xDF, 1)
        return waveunlocked_data_raw[0] & 0x01

    def itla_status_summery_get(self):
        self.page_select(0x12)
        summary_data_raw = self.my_i2c.read_bytes_maximum_58bytes(0xE6, 1)
        return summary_data_raw[0] & 0x01

    def itla_latch_complete_get(self):
        self.page_select(0x12)
        complete_data_raw = self.my_i2c.read_bytes_maximum_58bytes(0xE7, 1)
        return complete_data_raw[0] & 0x01

    def itla_latch_unlocked_get(self):
        self.page_select(0x12)
        unlocked_data_raw = self.my_i2c.read_bytes_maximum_58bytes(0xE7, 1)
        return (unlocked_data_raw[0] >> 1 & 0x01)

    def itla_latch_channel_get(self):
        self.page_select(0x12)
        channel_data_raw = self.my_i2c.read_bytes_maximum_58bytes(0xE7, 1)
        return (channel_data_raw[0] >> 2 & 0x01)

    def itla_latch_busy_get(self):
        self.page_select(0x12)
        busy_data_raw = self.my_i2c.read_bytes_maximum_58bytes(0xE7, 1)
        return (busy_data_raw[0] >> 3 & 0x01)

    def itla_mask_complete_get(self):
        self.page_select(0x12)
        complete_data_raw = self.my_i2c.read_bytes_maximum_58bytes(0xEF, 1)
        return complete_data_raw[0] & 0x01

    def itla_mask_unlocked_get(self):
        self.page_select(0x12)
        unlocked_data_raw = self.my_i2c.read_bytes_maximum_58bytes(0xEF, 1)
        return (unlocked_data_raw[0] >> 1 & 0x01)

    def itla_mask_channel_get(self):
        self.page_select(0x12)
        channel_data_raw = self.my_i2c.read_bytes_maximum_58bytes(0xEF, 1)
        return (channel_data_raw[0] >> 2 & 0x01)

    def itla_mask_busy_get(self):
        self.page_select(0x12)
        busy_data_raw = self.my_i2c.read_bytes_maximum_58bytes(0xEF, 1)
        return (busy_data_raw[0] >> 3 & 0x08)

    def itla_pow_set(self, pow_set):
        pow_send = int(pow_set / 0.01)
        self.page_select(0x12)
        self.my_i2c.write_bytes_maximum_55bytes(0xC8, [pow_send >> 8, pow_send & 0xFF])

    def itla_pow_get(self):
        self.page_select(0x12)
        pow_data = self.my_i2c.read_bytes_maximum_58bytes(0xC8, 2)
        cur_pow = (pow_data[0] << 8 | pow_data[1]) * 0.01
        return cur_pow

    def itla_offset_set(self, pow_set):
        offset_send = int(pow_set / 0.001)
        if offset_send < 0:
            offset_send += 65536
        self.page_select(0x12)
        self.my_i2c.write_bytes_maximum_55bytes(0x98, [offset_send >> 8, offset_send & 0xFF])

    def itla_offset_get(self):
        self.page_select(0x12)
        offset_data = self.my_i2c.read_bytes_maximum_58bytes(0x98, 2)
        cur_offset = (offset_data[0] << 8 | offset_data[1])
        if cur_offset > 32767:
            cur_offset = cur_offset - 65536
        return cur_offset * 0.001

    def get_msa_version(self):
        return self.my_i2c.read_bytes_maximum_58bytes(0x01, 1)[0]

    def itla_grid_spac_get(self):  # return val is float type, [GHz]
        self.page_select(0x12)
        if self.get_msa_version() == 0x41:
            grid_spac_get_lut = {
                0: 3.125,
                1: 6.25,
                2: 12.5,
                3: 25,
                4: 50,
                5: 100,
                6: 33,
                7: 75
            }
        else:
            grid_spac_get_lut = {
                0: 3.125,
                1: 6.25,
                2: 12.5,
                3: 25,
                4: 50,
                5: 100,
                6: 75,
                7: 33
            }
        grd_data = self.my_i2c.read_bytes_maximum_58bytes(0x80, 1)
        return grid_spac_get_lut[(grd_data[0] & 0xF0) >> 4]

    def itla_grid_spac_set(self, grid):
        self.page_select(0x12)
        if self.get_msa_version() == 0x41:
            grid_spac_set_lut = {
                3.125: 0,
                6.25: 1,
                12.5: 2,
                25: 3,
                50: 4,
                100: 5,
                33: 6,
                75: 7
            }
        else:
            grid_spac_set_lut = {
                3.125: 0,
                6.25: 1,
                12.5: 2,
                25: 3,
                50: 4,
                100: 5,
                75: 6,
                33: 7
            }
        grd_data_org = self.my_i2c.read_bytes_maximum_58bytes(0x80, 1)
        grd_data_new = (grd_data_org[0] & 0x0F) | (grid_spac_set_lut[grid] << 4)
        self.my_i2c.write_bytes_maximum_55bytes(0x80, [grd_data_new])

    def itla_fine_enable_get(self):
        self.page_select(0x12)
        fine_enable_raw = self.my_i2c.read_bytes_maximum_58bytes(0x80, 1)
        return fine_enable_raw[0] & 0x01

    def itla_fina_enable_set(self, index, num):
        self.page_select(0x12)
        fine_enable_raw = self.my_i2c.read_bytes_maximum_58bytes(0x80, 1)
        fine_enable = self.my_i2c.set_onebit(fine_enable_raw[0], index, num)
        # fine_enable = (fine_enable_raw[0] & 0xFE | enable >> 7 )
        self.my_i2c.write_bytes_maximum_55bytes(0x80, [fine_enable])
        # self.my_i2c.write_bytes_maximum_55bytes(0x80 , [fine_enable])

    def save_itla_setting_to_eeprom(self):
        buff = []
        self.page_select(0x12)
        buff.append(self.my_i2c.read_bytes_maximum_58bytes(0x80, 1)[0])  # grid
        for val in self.my_i2c.read_bytes_maximum_58bytes(0x88, 2):  # channel number
            buff.append(val)
        for val in self.my_i2c.read_bytes_maximum_58bytes(0x98, 2):  # freq offset
            buff.append(val)
        for val in self.my_i2c.read_bytes_maximum_58bytes(0xA8, 4):  # freq
            buff.append(val)
        for val in self.my_i2c.read_bytes_maximum_58bytes(0xC8, 2):  # target power
            buff.append(val)
        buff[0] = buff[0] >> 4
        self.page_select(0xC0)
        self.my_i2c.write_bytes_maximum_55bytes(0x92, buff)

    def get_itla_setting_from_eeprom(self):
        self.page_select(0xC0)
        itla_set_info = {}
        buff = self.my_i2c.read_bytes_maximum_58bytes(0x92, 11)
        grid_spec = {
            0: 3.125,
            1: 6.25,
            2: 12.5,
            3: 25,
            4: 50,
            5: 100,
            6: 75,
            7: 33
        }
        itla_set_info.update(grid=grid_spec[buff[0]])
        itla_set_info.update(channel=buff[1] << 8 | buff[2])
        itla_set_info.update(freq_offset=(buff[3] << 8 | buff[4]) * 0.001)
        itla_set_info.update(freq_thz=(buff[5] << 8 | buff[6]) + (buff[7] << 8 | buff[8]) * 0.05 * 0.001)
        itla_set_info.update(power=(buff[9] << 8 | buff[10]) * 0.01)
        return itla_set_info

        # ===========================CSTAR Operation=========================

    # non-MSA

    # def mpd_get(self):  # equation wrong!
    #     Vref = 0.119  # [V}
    #     R163 = 40.2*1000  # [ohm]
    #     R175 = 48.7*1000  # [ohm]
    #     mpd_dict = {}
    #     mpd_data = []
    #
    #     self.page_select(0xE5)
    #     raw_mpd_data = self.my_i2c.read_bytes_maximum_58bytes(0x80, 12)
    #     for i in [0, 2, 4, 6, 8, 10]:
    #         mpd_data.append(raw_mpd_data[i] << 8 | raw_mpd_data[i+1])
    #
    #     mpd_tx_child = [((x/(2**14)*2.048) - Vref)/R163*10**6 for x in mpd_data[2:6:1]]  # [uA]
    #     mpd_tx_parent = [((x/(2**14)*2.048) - Vref)/R175*10**6 for x in mpd_data[0:2:1]]  # [uA]
    #
    #     mpd_dict.update({'tx_xi': mpd_tx_child[0]})
    #     mpd_dict.update({'tx_xq': mpd_tx_child[1]})
    #     mpd_dict.update({'tx_yi': mpd_tx_child[2]})
    #     mpd_dict.update({'tx_yq': mpd_tx_child[3]})
    #
    #     mpd_dict.update({'tx_x': mpd_tx_parent[0]})
    #     mpd_dict.update({'tx_y': mpd_tx_parent[1]})
    #
    #     return mpd_dict

    def tx_mpd_get(self, pcba_info='1831101381_ver1.01'):
        rx_mpd_tap_gain = self.Read_GPIO_value(0x84)[0] >> 1 & 0x01
        if pcba_info == '1831101381_ver1.01':
            self.page_select(0xE5)
            mpd_table_regs = self.my_i2c.read_bytes_maximum_58bytes(128, 42)
            data_u16 = []
            for msb, lsb in zip(mpd_table_regs[::2], mpd_table_regs[1::2]):
                data_u16.append(msb << 8 | lsb)
            mpd_dict = {}
            mpd_dict.update(TX_MPD_XPV_DC=data_u16[0] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_XPV_DC_DMC=(data_u16[0] * 2.048 / 16384 - 0.12) / 0.499 * 1000)
            mpd_dict.update(TX_MPD_XPV_AC=data_u16[1] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_XPV_AC_DMC=(data_u16[1] / 16384 * 2.048 - 1.024) / 0.56 / (1 + 20 / 3.16) * 1000)
            mpd_dict.update(TX_MPD_YPV_DC=data_u16[2] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_YPV_DC_DMC=(data_u16[2] * 2.048 / 16384 - 0.12) / 0.499 * 1000)
            mpd_dict.update(TX_MPD_YPV_AC=data_u16[3] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_YPV_AC_DMC=(data_u16[3] / 16384 * 2.048 - 1.024) / 0.499 / (1 + 20 / 3.16) * 1000)
            mpd_dict.update(TX_MPD_XOUT_DC=data_u16[4] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_XOUT_DC_DMC=(data_u16[4] * 2.048 / 16384 - 0.12) / 6.8 * 1000)
            mpd_dict.update(TX_MPD_XOUT_AC=data_u16[5] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_XOUT_AC_DMC=((data_u16[5] / 16384 * 2.048 - 1.024) / 6.8 / (1 + 48.7 / 3.16) * 1000))
            mpd_dict.update(TX_MPD_YOUT_DC=data_u16[6] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_YOUT_DC_DMC=(data_u16[6] * 2.048 / 16384 - 0.12) / 6.8 * 1000)
            mpd_dict.update(TX_MPD_YOUT_AC=data_u16[7] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_YOUT_AC_DMC=((data_u16[7] / 16384 * 2.048 - 1.024) / 6.8 / (1 + 48.7 / 3.16) * 1000))
            mpd_dict.update(RX_GC_AVG=data_u16[9] * 2.048 * 1.5 / 4096)
            mpd_dict.update(RX_GC_XI=data_u16[10] * 2.048 * 1.5 / 4096)
            mpd_dict.update(RX_GC_XQ=data_u16[11] * 2.048 * 1.5 / 4096)
            mpd_dict.update(RX_GC_YI=data_u16[12] * 2.048 * 1.5 / 4096)
            mpd_dict.update(RX_GC_YQ=data_u16[13] * 2.048 * 1.5 / 4096)
            mpd_dict.update(TX_PKD_XI=data_u16[14] * 2.048 * 1.5 / 4096)
            mpd_dict.update(TX_PKD_XQ=data_u16[15] * 2.048 * 1.5 / 4096)
            mpd_dict.update(TX_PKD_YI=data_u16[16] * 2.048 * 1.5 / 4096)
            mpd_dict.update(TX_PKD_YQ=data_u16[17] * 2.048 * 1.5 / 4096)
            mpd_dict.update(COSA_TEMP=data_u16[18] * 2.048 / 4096)
            try:
                mpd_dict.update(COSA_TEMP_DMC=1 / (log(
                    (2.5 / (2.5 - data_u16[18] / 4096 * 2.048) - 1) * 100 / 100) / 4250 + 1 / 298.15) - 273.15)
            except:
                mpd_dict.update(COSA_TEMP_DMC=float('-inf'))
            mpd_dict.update(RX_MPD_XYIN=data_u16[19] * 2.5 / 4096)
            if rx_mpd_tap_gain:
                mpd_dict.update(RX_MPD_XYIN_DMC=data_u16[19] / 4096 * 2.5 / 21.782 * 1000)  # RX_MPD_TAP_GAIN = high
            else:
                mpd_dict.update(RX_MPD_XYIN_DMC=data_u16[19] / 4096 * 2.048 / 2222 * 1000)
            mpd_dict.update(RX_PKD_XI=data_u16[20] * 2.5 / 4096)
            mpd_dict.update(RX_MPD_TAP_GAIN=rx_mpd_tap_gain)
            return mpd_dict, data_u16
        elif pcba_info == '1831101388_ver1.01' or pcba_info == '1831101391_ver1.01' or pcba_info == '1831101411_ver1.02':
            self.page_select(0xE5)
            mpd_table_regs = self.my_i2c.read_bytes_maximum_58bytes(128, 44)
            data_u16 = []
            for msb, lsb in zip(mpd_table_regs[::2], mpd_table_regs[1::2]):
                data_u16.append(msb << 8 | lsb)
            mpd_dict = {}
            mpd_dict.update(TX_MPD_XPV_DC=data_u16[0] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_XPV_DC_DMC=(data_u16[0] * 2.048 / 16384 - 0.12) / 4.3 * 1000)
            mpd_dict.update(TX_MPD_XPV_AC=data_u16[1] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_XPV_AC_DMC=(data_u16[1] / 16384 * 2.048 - 1.024) / 4.3 / (1 + 147 / 3.16) * 1000)
            mpd_dict.update(TX_MPD_YPV_DC=data_u16[2] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_YPV_DC_DMC=(data_u16[2] * 2.048 / 16384 - 0.12) / 4.3 * 1000)
            mpd_dict.update(TX_MPD_YPV_AC=data_u16[3] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_YPV_AC_DMC=(data_u16[3] / 16384 * 2.048 - 1.024) / 4.3 / (1 + 147 / 3.16) * 1000)
            mpd_dict.update(TX_MPD_XOUT_DC=data_u16[4] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_XOUT_DC_DMC=(data_u16[4] * 2.048 / 16384 - 0.12) / 20 * 1000)
            mpd_dict.update(TX_MPD_XOUT_AC=data_u16[5] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_XOUT_AC_DMC=((data_u16[5] / 16384 * 2.048 - 1.024) / 20 / (1 + 147 / 3.16) * 1000))
            mpd_dict.update(TX_MPD_YOUT_DC=data_u16[6] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_YOUT_DC_DMC=(data_u16[6] * 2.048 / 16384 - 0.12) / 20 * 1000)
            mpd_dict.update(TX_MPD_YOUT_AC=data_u16[7] * 2.048 / 16384)
            mpd_dict.update(TX_MPD_YOUT_AC_DMC=((data_u16[7] / 16384 * 2.048 - 1.024) / 20 / (1 + 147 / 3.16) * 1000))
            mpd_dict.update(RX_GC_AVG=data_u16[9] * 2.048 * 1.5 / 4096)
            mpd_dict.update(RX_GC_XI=data_u16[10] * 2.048 * 1.5 / 4096)
            mpd_dict.update(RX_GC_XQ=data_u16[11] * 2.048 * 1.5 / 4096)
            mpd_dict.update(RX_GC_YI=data_u16[12] * 2.048 * 1.5 / 4096)
            mpd_dict.update(RX_GC_YQ=data_u16[13] * 2.048 * 1.5 / 4096)
            mpd_dict.update(TX_PKD_XI=data_u16[14] * 2.048 * 1.5 / 4096)
            mpd_dict.update(TX_PKD_XQ=data_u16[15] * 2.048 * 1.5 / 4096)
            mpd_dict.update(TX_PKD_YI=data_u16[16] * 2.048 * 1.5 / 4096)
            mpd_dict.update(TX_PKD_YQ=data_u16[17] * 2.048 * 1.5 / 4096)
            mpd_dict.update(COSA_TEMP=data_u16[18] * 2.048 / 4096)
            try:
                mpd_dict.update(COSA_TEMP_DMC=1 / (log(
                    (2.5 / (2.5 - data_u16[18] / 4096 * 2.048) - 1) * 100 / 100) / 4320 + 1 / 298.15) - 273.15)
            except:
                mpd_dict.update(COSA_TEMP_DMC=float('-inf'))
            mpd_dict.update(RX_MPD_XYIN=data_u16[19] * 2.048 / 4096)
            if rx_mpd_tap_gain:
                mpd_dict.update(RX_MPD_XYIN_DMC=data_u16[19] / 4096 * 2.048 / 22 * 1000)  # RX_MPD_TAP_GAIN = high
            else:
                mpd_dict.update(RX_MPD_XYIN_DMC=data_u16[19] / 4096 * 2.048 / 2222 * 1000)
            if pcba_info == '1831101391_ver1.01' or pcba_info == '1831101411_ver1.02':
                mpd_dict.update(RX_PKD_XI=data_u16[21] * 2.048 * 1.5 / 4096)
            elif pcba_info == '1831101388_ver1.01':
                mpd_dict.update(RX_PKD_XI=data_u16[21] * 2.048 / 4096)
            mpd_dict.update(RX_MPD_TAP_GAIN=rx_mpd_tap_gain)
            return mpd_dict, data_u16

    def get_dac_setting(self, pcba_info='1831101391_ver1.01'):  # delete p1_1831101381_ver1.01 content
        self.page_select(0xE4)
        dac_list = self.my_i2c.read_bytes_maximum_58bytes(128, 50)
        data_u16 = []
        for msb, lsb in zip(dac_list[::2], dac_list[1::2]):
            data_u16.append(msb << 8 | lsb)
        dac_dict = {}
        dac_dict.update(TX_BIAS_XIP=data_u16[0] / 65536 * 5)
        dac_dict.update(TX_BIAS_XIN=data_u16[1] / 65536 * 5)
        dac_dict.update(TX_BIAS_XQP=data_u16[2] / 65536 * 5)
        dac_dict.update(TX_BIAS_XQN=data_u16[3] / 65536 * 5)
        dac_dict.update(TX_PHASE_XN=data_u16[5] / 65536 * 5)
        dac_dict.update(TX_PHASE_XP=data_u16[4] / 65536 * 5)
        dac_dict.update(TX_BIAS_YIP=data_u16[6] / 65536 * 5)
        dac_dict.update(TX_BIAS_YIN=data_u16[7] / 65536 * 5)
        dac_dict.update(TX_BIAS_YQP=data_u16[8] / 65536 * 5)
        dac_dict.update(TX_BIAS_YQN=data_u16[9] / 65536 * 5)
        dac_dict.update(TX_PHASE_YP=data_u16[10] / 65536 * 5)
        dac_dict.update(TX_PHASE_YN=data_u16[11] / 65536 * 5)
        dac_dict.update(RX_OA_XI=data_u16[12] / 4096 * 2.5)
        dac_dict.update(RX_OA_XQ=data_u16[13] / 4096 * 2.5)
        dac_dict.update(RX_OA_YI=data_u16[14] / 4096 * 2.5)
        dac_dict.update(RX_OA_YQ=data_u16[15] / 4096 * 2.5)
        dac_dict.update(TX_VG_XI=data_u16[16] / 4096 * 2.5)
        dac_dict.update(TX_VG_XQ=data_u16[17] / 4096 * 2.5)
        dac_dict.update(TX_VG_YI=data_u16[18] / 4096 * 2.5)
        dac_dict.update(TX_VG_YQ=data_u16[19] / 4096 * 2.5)
        dac_dict.update(TX_VOA_XP=data_u16[20] / 65536 * 5)
        dac_dict.update(TX_VOA_XN=data_u16[21] / 65536 * 5)
        dac_dict.update(TX_VOA_YP=data_u16[22] / 65536 * 5)
        dac_dict.update(TX_VOA_YN=data_u16[23] / 65536 * 5)
        if pcba_info == '1831101411_ver1.02':
            DAC_12B_ADJ = data_u16[24] / 4096 * 1.024
            dac_dict.update(DAC_12B_ADJ=DAC_12B_ADJ)
            dac_dict.update(DVDD_12B_ADJ=(1 - DAC_12B_ADJ) / 261 * 68.1 + 0.5)
        else:
            # print('current pcba:' + pcba_info + 'can not be supported.')
            dac_dict.update(DAC_12B_ADJ=0)
            dac_dict.update(DVDD_12B_ADJ=0)
        return dac_dict

    def get_tx_cor_all(self):
        self.page_select(0xE0)
        data_list = self.my_i2c.read_bytes_maximum_58bytes(0xD0, 12)
        data_u16 = []
        for msb, lsb in zip(data_list[::2], data_list[1::2]):
            data_u16.append(msb << 8 | lsb)
        tx_cor_dict = {}
        tx_cor_dict.update(TX_COR_XI=data_u16[0])
        tx_cor_dict.update(TX_COR_XQ=data_u16[1])
        tx_cor_dict.update(TX_COR_X=data_u16[2])
        tx_cor_dict.update(TX_COR_YI=data_u16[3])
        tx_cor_dict.update(TX_COR_YQ=data_u16[4])
        tx_cor_dict.update(TX_COR_Y=data_u16[5])
        return tx_cor_dict

    def Get_ABC_error(self):
        self.page_select(0xE0)
        abc_error_regs = self.my_i2c.read_bytes_maximum_58bytes(0xD0, 12)
        data_u16 = []
        for msb, lsb in zip(abc_error_regs[::2], abc_error_regs[1::2]):
            data_u16.append(msb << 8 | lsb)
        error_dict = {}
        error_dict.update(COR_XI=data_u16[0] / 1024)
        error_dict.update(COR_XQ=data_u16[1] / 1024)
        error_dict.update(COR_X=data_u16[2] / 1024)
        error_dict.update(COR_YI=data_u16[3] / 1024)
        error_dict.update(COR_YQ=data_u16[4] / 1024)
        error_dict.update(COR_Y=data_u16[5] / 1024)
        return error_dict

    def tx_heater_set(self, xip=None, xqp=None, xp=None, yip=None, yqp=None, yp=None, sweep_type=False, max_volt=None):
        full_scale = 65535
        Vref = 5
        Params = max_volt  # 20.25
        coeff = 0.5
        xip_addr = 128
        xin_addr = 130
        xqp_addr = 132
        xqn_addr = 134
        xp_addr = 136
        xn_addr = 138
        yip_addr = 140
        yin_addr = 142
        yqp_addr = 144
        yqn_addr = 146
        yp_addr = 148
        yn_addr = 150

        self.page_select(0xE4)
        if xip is not None:
            buff = int(full_scale * (xip ** coeff / Vref))
            self.my_i2c.write_bytes_maximum_55bytes(xip_addr, [(buff >> 8) & 0xFF, buff & 0xFF])
            if sweep_type:
                n_pole = 4
            else:
                n_pole = Params - xip
            buff1 = int((n_pole ** coeff / Vref * full_scale))
            self.my_i2c.write_bytes_maximum_55bytes(xin_addr, [(buff1 >> 8) & 0xFF, buff1 & 0xFF])
            print("xip:", '{:4.3f}'.format(xip ** coeff), " xin:", '{:4.3f}'.format(n_pole ** coeff))
            # time.sleep(0.5)
        if xqp is not None:
            buff = int(full_scale * (xqp ** coeff / Vref))
            self.my_i2c.write_bytes_maximum_55bytes(xqp_addr, [(buff >> 8) & 0xFF, buff & 0xFF])
            if sweep_type:
                n_pole = 4
            else:
                n_pole = Params - xqp
            buff1 = int((n_pole ** coeff / Vref * full_scale))
            self.my_i2c.write_bytes_maximum_55bytes(xqn_addr, [(buff1 >> 8) & 0xFF, buff1 & 0xFF])
            print("xqp:", '{:4.3f}'.format(xqp ** coeff), " xqn:", '{:4.3f}'.format(n_pole ** coeff))
            # time.sleep(0.5)
        if xp is not None:
            buff = int(full_scale * (xp ** coeff / Vref))
            self.my_i2c.write_bytes_maximum_55bytes(xp_addr, [(buff >> 8) & 0xFF, buff & 0xFF])
            if sweep_type:
                n_pole = 4
            else:
                n_pole = Params - xp
            buff1 = int((n_pole ** coeff / Vref * full_scale))
            self.my_i2c.write_bytes_maximum_55bytes(xn_addr, [(buff1 >> 8) & 0xFF, buff1 & 0xFF])
            print("xp:", '{:4.3f}'.format(xp ** coeff), " xn:", '{:4.3f}'.format(n_pole ** coeff))
            # time.sleep(0.5)
        if yip is not None:
            buff = int(full_scale * (yip ** coeff / Vref))
            self.my_i2c.write_bytes_maximum_55bytes(yip_addr, [(buff >> 8) & 0xFF, buff & 0xFF])
            if sweep_type:
                n_pole = 4
            else:
                n_pole = Params - yip
            buff1 = int((n_pole ** coeff / Vref * full_scale))
            self.my_i2c.write_bytes_maximum_55bytes(yin_addr, [(buff1 >> 8) & 0xFF, buff1 & 0xFF])
            print("yip:", '{:4.3f}'.format(yip ** coeff), " yin:", '{:4.3f}'.format(n_pole ** coeff))
            # time.sleep(0.5)
        if yqp is not None:
            buff = int(full_scale * (yqp ** coeff / Vref))
            self.my_i2c.write_bytes_maximum_55bytes(yqp_addr, [(buff >> 8) & 0xFF, buff & 0xFF])
            if sweep_type:
                n_pole = 4
            else:
                n_pole = Params - yqp
            buff1 = int((n_pole ** coeff / Vref * full_scale))
            self.my_i2c.write_bytes_maximum_55bytes(yqn_addr, [(buff1 >> 8) & 0xFF, buff1 & 0xFF])
            print("yqp:", '{:4.3f}'.format(yqp ** coeff), " yqn:", '{:4.3f}'.format(n_pole ** coeff))
            # time.sleep(0.5)
        if yp is not None:
            buff = int(full_scale * (yp ** coeff / Vref))
            self.my_i2c.write_bytes_maximum_55bytes(yp_addr, [(buff >> 8) & 0xFF, buff & 0xFF])
            if sweep_type:
                n_pole = 4
            else:
                n_pole = Params - yp
            buff1 = int((n_pole ** coeff / Vref * full_scale))
            self.my_i2c.write_bytes_maximum_55bytes(yn_addr, [(buff1 >> 8) & 0xFF, buff1 & 0xFF])
            print("yp:", '{:4.3f}'.format(yp ** coeff), " yn:", '{:4.3f}'.format(n_pole ** coeff))
            # time.sleep(0.5)

    def Write_Tuner_value(self, add, data):
        full_scale = 65535
        Vref = 5
        Params = 20.25
        coeff = 0.5

        self.page_select(0xE4)
        # data = data / 1.2
        buff = int(full_scale * (data / Vref))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def Write_Tuner1_value(self, add, data):
        full_scale = 65535
        Vref = 5
        Params = 20.25
        coeff = 0.5

        self.page_select(0xE4)
        # data = data / 1.2
        buff = (((Params - (data ** 2)) ** coeff) / Vref * full_scale)
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def Write_Tuner_TIA_BW(self, add, data):
        full_scale = 65535
        Vref = 2.5

        self.page_select(0xE4)
        data = data / 1.4
        buff = int(full_scale * (data / Vref))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def Write_Tuner_value_rxtia(self, add, data):

        self.page_select(0xE4)
        buff = int(4095 * (data / 2.5))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def Write_Rx_OA_value(self, add, data):
        self.page_select(0xE4)
        buff = int(4095 * (data / 2.5))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def Write_Rx_VOA_value(self, add, data):
        self.page_select(0xE4)
        buff = int(4095 * (data / 5))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def Write_Tuner_value_GC(self, add, data):

        self.page_select(0xE4)
        data = data / (-1.35)
        buff = int(4095 * (data / 2.5))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def Write_Tuner_value_EQ(self, add, data):

        self.page_select(0xE4)
        data = data / (-1.325)
        buff = int(4095 * (data / 2.5))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def Write_Tuner_value_vbos(self, add, data):

        self.page_select(0xE4)
        data = (data - 2.496) / -2.2
        buff = int(4095 * (data / 2.5))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def Write_RX_VOA(self, add, data):

        self.page_select(0xE4)
        data = data * 25.5 / 1000
        buff = int(4095 * (data / 2.5))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def Write_Tuner_value_txeq(self, add, data):
        self.page_select(0xE4)
        buff = int(4095 * (data / 2.5) / -1.325)  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.1)

    def Write_Tuner_value_txvb(self, add, data):
        self.page_select(0xE4)
        buff = int((4095 * (data / 2.5) / -2.2) - 2.496)  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.1)

    def Write_Tuner_value_txvoa(self, add, data):
        self.page_select(0xE4)
        data = data * 4.99 / 200
        buff = int(4095 * (data / 2.5))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def Write_DVDD_12B_ADJ_value(self, add, data):
        full_scale = 4096
        Vref = 1.024
        DAC = int(- (((data - 0.5) / 68.1 * 261 - 1) / Vref * full_scale))
        self.page_select(0xE4)
        self.my_i2c.write_bytes_maximum_55bytes(add, [DAC >> 8, DAC & 0xFF])
        time.sleep(0.01)

    def write_gpio_value(self, add, index, num):
        self.page_select(0xE6)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 1)
        print(buff)
        new_data = self.my_i2c.set_onebit(buff[0], index, num)
        print(new_data)
        self.my_i2c.write_bytes_maximum_55bytes(add, [new_data])

    def write_loop(self, table, add, index, num):
        self.page_select(table)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 1)
        print(buff)
        new_data = self.my_i2c.set_onebit(buff[0], index, num)
        print(new_data)
        self.my_i2c.write_bytes_maximum_55bytes(add, [new_data])

    def write_ra_value(self, add, data):
        self.page_select(0xE7)
        self.my_i2c.write_bytes_maximum_55bytes(add, [data & 0xFF, data >> 8])
        time.sleep(0.1)

    def read_ra_value(self, pageselect):
        full_scale = 16384
        Vref = 2.5
        Trans = 1.21

        self.page_select(pageselect)
        buff = self.my_i2c.read_bytes_maximum_128bytes(0x80, 128)
        mytable_int = [int(x) for x in buff]
        tar_list = []
        for j in range(0, 128, 4):
            element_list = []
            for i in range(4):
                temp0 = hex(mytable_int[i + j])[2:].zfill(2)
                element_list.append(str(temp0))
            tar_list.append(str(''.join(element_list)))
        # print(tar_list)
        mylist = []
        # mylist_dic = {}
        for i in range(len(tar_list)):
            mylist.append((self.my_i2c.convert(tar_list[i])) / full_scale * Vref * Trans)
        # print(mylist)
        # mylist_dic.update({'Vcol':mylist[0]})
        # mylist_dic.update({'Re':mylist[1]})
        # mylist_dic.update({'Im':mylist[2]})
        time.sleep(0.1)
        print(mylist)
        return mylist

    def Read_Tuner_value(self, add):
        full_scale = 65535
        Vref = 5  # 2.5

        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = (buff[0] << 8 | buff[1]) * Vref / full_scale  # Read data is FW value
        # data = data * 1.2
        # data1 = '% 4f' % data
        data1 = '{:6.4f}'.format(data)
        # print(data1)
        time.sleep(0.01)
        return data1

    def Read_RX_TIA(self, add):
        full_scale = 4095
        Vref = 2.5

        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = (buff[0] << 8 | buff[1]) * Vref / full_scale  # Read data is FW value
        # data1 = '% 4f' % data
        data1 = '{:6.4f}'.format(data)
        # print(data1)
        time.sleep(0.01)
        return data1

    def Read_RX_OA_value(self, add):
        full_scale = 4095
        Vref = 2.5
        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = (buff[0] << 8 | buff[1]) * Vref / full_scale  # Read data is FW value
        # data1 = '% 4f' % data
        data1 = '{:6.4f}'.format(data)
        # print(data1)
        time.sleep(0.01)
        return data1

    def Read_RX_VOA_value(self, add):
        full_scale = 4095
        Vref = 5
        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = (buff[0] << 8 | buff[1]) * Vref / full_scale  # Read data is FW value
        # data1 = '% 4f' % data
        data1 = '{:6.4f}'.format(data)
        # print(data1)
        time.sleep(0.01)
        return data1

    def Read_Tuner_TIA_BW(self, add):
        full_scale = 65535
        Vref = 2.5

        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = (buff[0] << 8 | buff[1]) * Vref / full_scale  # Read data is FW value
        data = data * 1.4
        # data1 = '% 4f' % data
        data1 = '{:6.4f}'.format(data)
        # print(data1)
        time.sleep(0.01)
        return data1

    def Read_Tuner_GC(self, add):
        full_scale = 4095
        Vref = 2.5

        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = (buff[0] << 8 | buff[1]) * Vref / full_scale  # Read data is FW value
        data = data * (-1.35)
        # data1 = '% 4f' % data
        data1 = '{:6.4f}'.format(data)
        # print(data1)
        time.sleep(0.01)
        return data1
        # time.sleep(0.01)

    def Read_Tuner_EQ(self, add):
        full_scale = 4095
        Vref = 2.5

        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = (buff[0] << 8 | buff[1]) * Vref / full_scale  # Read data is FW value
        data = data * (-1.325)
        # data1 = '% 4f' % data
        data1 = '{:6.4f}'.format(data)
        # print(data1)
        time.sleep(0.01)
        return data1
        # time.sleep(0.01)

    def Read_tx_vbos(self, add):
        full_scale = 4095
        Vref = 2.5

        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = (buff[0] << 8 | buff[1]) * Vref / full_scale  # Read data is FW value
        data = 2.496 - data * 2.2
        # data1 = '% 4f' % data
        data1 = '{:6.4f}'.format(data)
        # print(data1)
        time.sleep(0.01)
        return data1

    def Read_RX_VOA(self, add):
        full_scale = 4095
        Vref = 2.5

        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = (buff[0] << 8 | buff[1]) * Vref / full_scale  # Read data is FW value
        data = data * 1000 / 25.5
        # data1 = '% 4f' % data
        data1 = '{:6.4f}'.format(data)
        # print(data1)
        time.sleep(0.01)
        return data1

    def Read_Tuner_TX_VOA(self, add):
        full_scale = 65535
        Vref = 2.5

        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = (buff[0] << 8 | buff[1]) * Vref / full_scale  # Read data is FW value
        data = data * 200 / 4.9
        # data1 = '% 4f' % data
        data1 = '{:6.4f}'.format(data)
        # print(data1)
        time.sleep(0.01)
        return data1

    def Read_TxCtrol_status(self):
        self.page_select(0xE7)
        buff = self.my_i2c.read_bytes_maximum_58bytes(150, 2)
        print(buff[0])
        print(buff[1])
        data = buff[1] << 8 | buff[0]
        # data1 = '% 2f'% data
        # print(data1)
        time.sleep(0.01)
        return data

    # time.sleep(0.2)

    def Read_ModuleMonitor(self, add):
        self.page_select(0xE5)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = (buff[0] << 8 | buff[1])
        # data1 = '% d'% data
        time.sleep(0.01)
        return data

    # time.sleep(0.01)

    def Read_TxCtrol_Param(self, add):
        self.page_select(0xE7)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = buff[1] << 8 | buff[0]
        # data1 = '% 2f'% data
        time.sleep(0.01)
        return data

    def Write_TxCtrol_Parm(self, add, bitstart, bitend, newdata):
        self.page_select(0xE7)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = buff[1] << 8 | buff[0]
        # print(data)
        new_data = self.my_i2c.replace_bit(data, bitstart, bitend, newdata)
        self.my_i2c.write_bytes_maximum_55bytes(add, [new_data & 0xFF, new_data >> 8])
        print(new_data)
        time.sleep(0.01)

    def Write_TxCtrol_Parm2(self, PageNum, add, data):
        self.page_select(PageNum)
        self.my_i2c.write_bytes_maximum_55bytes(add, [data & 0xFF, data >> 8])
        time.sleep(0.01)

    def read_fa_value(self, pageselect, add):
        full_scale = 16384
        Vref = 2.5
        Trans = 1.21

        self.page_select(pageselect)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 4)
        # print(buff)
        mytable_int = [int(x) for x in buff]

        element_list = []
        for i in range(4):
            temp = hex(mytable_int[i])[2:]
            element_list.append(str(temp))
        mylist = self.my_i2c.convert(str(''.join(element_list))) / full_scale * Vref * Trans
        # print(mylist)
        return mylist

    def Read_GPIO_value(self, add):
        self.page_select(0xE6)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 1)
        # print(buff)
        return buff

    def abc_on_off(self, status):
        # self.my_i2c.write_bytes_maximum_55bytes(127, [0xE7])
        self.page_select(0xE7)
        if status == 'on':
            self.my_i2c.write_bytes_maximum_55bytes(160, [0xBB])
        else:
            if status == 'off':
                self.my_i2c.write_bytes_maximum_55bytes(160, [0xAA])
            else:
                print('Invalid ABC ON/OFF Ctrl cmd!')
        time.sleep(3)

    def fa_abc_pause_on_off(self, status):
        # self.my_i2c.write_bytes_maximum_55bytes(127, [0xE7])
        self.page_select(0xE7)
        if status == 'pause':
            self.my_i2c.write_bytes_maximum_55bytes(160, [0xCC])
        else:
            if status == 'resume':
                self.my_i2c.write_bytes_maximum_55bytes(160, [0xDD])
            else:
                print('Invalid ABC ON/OFF Ctrl cmd!')
        time.sleep(3)

    def Read_ADC_monitor(self):
        scale = 4095
        Vref = 2.5
        EVB_MCU = self.my_i2c.read_ADC()
        print("EVB_MCU:" + str(EVB_MCU))
        # QDD1_1SENSE_temp = (EVB_MCU[2] << 8 | EVB_MCU[3]) / scale * Vref / 0.2
        # QDD1_1SENSE = '% 4f' % QDD1_1SENSE_temp
        # QDD2_1SENSE_temp = (EVB_MCU[4] << 8 | EVB_MCU[5]) / scale * Vref / 0.2
        # QDD2_1SENSE = '% 4f' % QDD2_1SENSE_temp
        # Temp_Mcu_temp = ((EVB_MCU[13] << 8 | EVB_MCU[14]) / scale * Vref - 0.76) / Vref
        # Temp_Mcu = '% 4f' % Temp_Mcu_temp
        # QDD1_3V3_temp = (EVB_MCU[0] << 8 | EVB_MCU[1]) / scale * Vref * 0.2
        # QDD1_3V3 = '% 4f' % QDD1_3V3_temp
        # QDD2_3V3_temp = (EVB_MCU[6] << 8 | EVB_MCU[7]) / scale * Vref * 0.2
        # QDD2_3V3 = '% 4f' % QDD2_3V3_temp
        QDD1_3V3 = '{:.3f}'.format((EVB_MCU[1] << 8 | EVB_MCU[0]) / scale * Vref * 2)
        QDD1_ISENSE = '{:.3f}'.format((EVB_MCU[3] << 8 | EVB_MCU[2]) / scale * Vref / 0.2)
        QDD2_ISENSE = '{:.3f}'.format((EVB_MCU[5] << 8 | EVB_MCU[4]) / scale * Vref / 0.2)
        QDD2_3V3 = '{:.3f}'.format((EVB_MCU[7] << 8 | EVB_MCU[6]) / scale * Vref * 2)
        DUT_Vcc = '{:.3f}'.format((EVB_MCU[9] << 8 | EVB_MCU[8]) / scale * Vref * 2)
        Temp_Mcu = '{:.3f}'.format(((EVB_MCU[13] << 8 | EVB_MCU[12]) / scale * Vref - 0.76) * 1000 / Vref + 25)
        return [QDD1_ISENSE, QDD2_ISENSE, Temp_Mcu, QDD1_3V3, QDD2_3V3, DUT_Vcc]

    def Write_COSA_SPI_REG(self, add, data):
        self.page_select(0xC2)
        self.my_i2c.write_bytes_maximum_55bytes(add, [data])
        time.sleep(0.01)

    def Write_COSA_SPI_REG_8bit(self, add, bitstart, bitend, newdata):
        self.page_select(0xC2)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 1)
        new_data = self.my_i2c.replace_bit8(buff[0], bitstart, bitend, newdata)
        self.my_i2c.write_bytes_maximum_55bytes(add, [new_data])
        print(new_data)
        time.sleep(0.01)

    def write_COSA_SPI_REG_onebit(self, add, index, num):
        self.page_select(0xC2)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 1)
        print(buff)
        new_data = self.my_i2c.set_onebit(buff[0], index, num)
        print(new_data)
        self.my_i2c.write_bytes_maximum_55bytes(add, [new_data])

    def Read_COSA_SPI_REG(self, add):
        self.page_select(0xC2)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        # data = (buff[0] << 8 | buff[1]) # Read data is FW value
        time.sleep(0.01)
        return [buff]

    def get_tx_vg_slope(self):
        self.page_select(0xC1)
        dac_list = self.my_i2c.read_bytes_maximum_58bytes(128, 10)
        data_u16 = []
        for msb, lsb in zip(dac_list[::2], dac_list[1::2]):
            cur_offset = msb << 8 | lsb
            if cur_offset > 32767:
                cur_offset = cur_offset - 65536
            data_u16.append(cur_offset)
        dac_dict = {}
        dac_dict.update(Tuning_pre_cal_temperature=data_u16[0] / 256)
        dac_dict.update(TX_vg_xi_HT_slope=data_u16[1] / 10000)
        dac_dict.update(TX_vg_xq_HT_slope=data_u16[2] / 10000)
        dac_dict.update(TX_vg_yi_HT_slope=data_u16[3] / 10000)
        dac_dict.update(TX_vg_yq_HT_slope=data_u16[4] / 10000)
        dac_list = self.my_i2c.read_bytes_maximum_58bytes(178, 8)
        for msb, lsb in zip(dac_list[::2], dac_list[1::2]):
            cur_offset = msb << 8 | lsb
            if cur_offset > 32767:
                cur_offset = cur_offset - 65536
            data_u16.append(cur_offset)
        dac_dict.update(TX_vg_xi_LT_slope=data_u16[5] / 10000)
        dac_dict.update(TX_vg_xq_LT_slope=data_u16[6] / 10000)
        dac_dict.update(TX_vg_yi_LT_slope=data_u16[7] / 10000)
        dac_dict.update(TX_vg_yq_LT_slope=data_u16[8] / 10000)
        return dac_dict

    def get_tx_vg(self):
        self.page_select(0xC2)
        dac_list = self.my_i2c.read_bytes_maximum_58bytes(188, 10)
        # print(dac_list)
        data_u16 = []
        for msb, lsb in zip(dac_list[::2], dac_list[1::2]):
            data_u16.append(msb << 8 | lsb)
        # print(data_u16)
        dac_dict = {}
        dac_dict.update(TX_vg_xi=data_u16[0] / 4096 * 2.5)
        dac_dict.update(TX_vg_xq=data_u16[1] / 4096 * 2.5)
        dac_dict.update(TX_vg_yi=data_u16[2] / 4096 * 2.5)
        dac_dict.update(TX_vg_yq=data_u16[3] / 4096 * 2.5)
        return dac_dict

    def set_tx_vg_slope(self, add, data):
        self.page_select(0xC1)
        buff = int(data)
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def set_tx_vg(self, add, data):
        self.page_select(0xC2)
        buff = int(4095 * (data / 2.5))
        print(buff)
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def set_internal_temp(self, add, data):
        self.page_select(0xE5)
        buff = int(data)
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def set_Reg_offset(self, table, add, data):
        self.page_select(table)
        buff = int(data)
        self.my_i2c.write_bytes_maximum_55bytes(add, [buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def get_Reg_offset(self, table, add):
        self.page_select(table)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 2)
        data = buff[0] << 8 | buff[1]
        time.sleep(0.01)
        return data

    def set_Reg_slope(self, table, add, data):
        self.page_select(table)
        buff = struct.pack('f', float(data))
        buff_raw = [i for i in buff]
        buff_raw.reverse()
        self.my_i2c.write_bytes_maximum_55bytes(add, buff_raw)
        time.sleep(0.01)

    def get_Reg_slope(self, table, add):
        self.page_select(table)
        buff = self.my_i2c.read_bytes_maximum_58bytes(add, 4)
        time.sleep(0.01)
        buff_raw = struct.unpack('<f', bytearray([buff[3], buff[2], buff[1], buff[0]]))
        return buff_raw[0]

    def get_internal_temp_volt(self, pcba_info='1831101381_ver1.01'):
        self.page_select(0xE5)
        buff = self.my_i2c.read_bytes_maximum_58bytes(168, 44)
        data_u16 = [(msb << 8) | lsb for msb, lsb in zip(buff[::2], buff[1::2])]
        adc_info = {}
        if pcba_info == '1831101388_ver1.01' or pcba_info == '1831101391_ver1.01' or pcba_info == '1831101411_ver1.02':
            adc_info.update(MCU_P3V3=data_u16[0] / 4096 * 2.048 * 2)
        else:
            adc_info.update(MCU_P3V3=0)
        adc_info.update(Module_TEMP=(data_u16[11] / 256))
        if data_u16[12] < 0x8000:
            buff = data_u16[12] / 100
        else:
            buff = (data_u16[12] - 0x10000) / 100
        adc_info.update(COSA_TEMP=buff)
        if data_u16[13] < 0x8000:
            buff = data_u16[13] / 256
        else:
            buff = (data_u16[13] - 0x10000) / 256
        adc_info.update(ITLA_TEMP=buff)
        if data_u16[14] < 0x8000:
            buff = data_u16[14] / 256
        else:
            buff = (data_u16[14] - 0x10000) / 256
        adc_info.update(ISL91302B_TEMP=buff)
        if data_u16[15] < 0x8000:
            buff = data_u16[15] / 256
        else:
            buff = (data_u16[15] - 0x10000) / 256
        adc_info.update(AD5593_U5_TEMP=buff)
        if data_u16[16] < 0x8000:
            buff = data_u16[16] / 256
        else:
            buff = (data_u16[16] - 0x10000) / 256
        adc_info.update(DSP_TEMP=buff)
        if data_u16[19] < 0x8000:
            buff = data_u16[19] / 256
        else:
            buff = (data_u16[19] - 0x10000) / 256
        adc_info.update(AD5593_U27_TEMP=buff)
        if data_u16[20] < 0x8000:
            buff = data_u16[20] * 0.25
        else:
            buff = (data_u16[20] - 0x10000) * 0.25
        adc_info.update(ISL91302B_AUX_INPUT0=buff)
        if data_u16[21] < 0x8000:
            buff = data_u16[21] * 0.25
        else:
            buff = (data_u16[21] - 0x10000) * 0.25
        adc_info.update(ISL91302B_AUX_INPUT1=buff)
        return adc_info

    def get_isl91302_temp(self):
        buff = self.Read_ModuleMonitor(0xC4)
        if buff < 0x8000:
            buff = buff / 256
        else:
            buff = (buff - 0x10000) / 256
        return buff

    def get_isl91302_current(self):
        # self.page_select(0xE7)
        # buff = self.my_i2c.read_bytes_maximum_58bytes(0xB0, 2)
        # return (buff[0] << 8 | buff[1]) / 1000
        self.page_select(0xE5)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0xD4, 2)
        return (buff[0] << 8 | buff[1]) / 1000

    def get_isl91302_volt(self):
        self.page_select(0xE5)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0xD2, 2)
        return (buff[0] << 8 | buff[1]) / 1000

    def get_isl91302_set_volt(self):
        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0xC4, 2)
        return (buff[0] << 8 | buff[1]) / 1000

    def get_avs_volt(self):
        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0xC4, 2)
        return (buff[0] << 8 | buff[1]) / 1000

    def get_ad5593_u5_temp(self):
        buff = self.Read_ModuleMonitor(0xC6)
        if buff < 0x8000:
            buff = buff / 256
        else:
            buff = (buff - 0x10000) / 256
        return buff

    def get_ad5593_u27_temp(self):
        buff = self.Read_ModuleMonitor(0xCE)
        if buff < 0x8000:
            buff = buff / 256
        else:
            buff = (buff - 0x10000) / 256
        return buff

    def get_itla_temp(self):
        buff = self.Read_ModuleMonitor(0xC2)
        if buff < 0x8000:
            buff = buff / 256
        else:
            buff = (buff - 0x10000) / 256
        return buff

    def get_cosa_temp(self):
        buff = self.Read_ModuleMonitor(0xA4)
        try:
            cosa_temp = 1 / (log((2.5 / (2.5 - buff / 4096 * 2.048) - 1) * 100 / 100) / 4250 + 1 / 298.15) - 273.15
        except:
            cosa_temp = float('-inf')
        return cosa_temp

    def get_dsp_temp(self):
        buff = self.Read_ModuleMonitor(0xC8)
        if buff < 0x8000:
            buff = buff / 256
        else:
            buff = (buff - 0x10000) / 256
        return buff

    def get_aux0_input(self):
        buff = self.Read_ModuleMonitor(0xD0)
        if float(buff) < 0x8000:
            buff = float(buff) * 0.25
        else:
            buff = (float(buff) - 65536) * 0.25
        return buff

    def get_aux1_input(self):
        buff = self.Read_ModuleMonitor(0xD2)
        if float(buff) < 0x8000:
            buff = float(buff) * 0.25
        else:
            buff = (float(buff) - 65536) * 0.25
        return buff

    def get_mcu_p3v3(self, pcba_info='1831101381_ver1.01'):
        if pcba_info == '1831101388_ver1.01' or pcba_info == '1831101391_ver1.01' or pcba_info == '1831101411_ver1.02':
            buff = self.Read_ModuleMonitor(0xA8)
            return buff / 4096 * 2.048
        else:
            return 0

    def get_dsp_current(self):
        return self.Read_ModuleMonitor(0xD4)  # only get the original value

    def get_dsp_internal_status(self):
        self.page_select(0xE0)
        return self.my_i2c.read_bytes_maximum_58bytes(0x8D, 1)[0]

    def write_tx_vg_all(self, data):
        self.page_select(0xE4)
        buff = int(4095 * (data / 2.5))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(160, [buff >> 8, buff & 0xFF] * 4)

    def write_rx_oa_all(self, data):
        self.page_select(0xE4)
        buff = int(4095 * (data / 2.5))  # write data is FW value
        self.my_i2c.write_bytes_maximum_55bytes(152, [buff >> 8, buff & 0xFF] * 4)

    def write_cosa_spi_ctle_ctrl_all(self, data):
        self.page_select(0xC2)
        buff = self.my_i2c.read_bytes_maximum_58bytes(129, 1)[0]  # add 129 is the channel 1 for ctle_ctrl
        new_data = self.my_i2c.replace_bit8(buff, 0, 2, data)
        for add in [129, 133, 137, 141]:
            self.my_i2c.write_bytes_maximum_55bytes(add, [new_data])
            time.sleep(0.01)

    def write_cosa_spi_output_bias_all(self, data):
        # self.page_select(0xC2)
        # for add in [128, 132, 136, 140]:
        #     self.my_i2c.write_bytes_maximum_55bytes(add, [data])
        #     time.sleep(0.01)
        self.page_select(0xC2)
        for add in [128, 132, 136, 140]:
            self.my_i2c.write_bytes_maximum_55bytes(add, [data])
            time.sleep(0.01)
            buff = self.Read_COSA_SPI_REG(add)[0][1]
            self.my_i2c.write_bytes_maximum_55bytes(add + 1, buff)

    def tx_voa_x_p_set(self, data, display=False, pcba_info='1831101381_ver1.01'):
        if pcba_info == '1831101381_ver1.01':
            buff = int(4095 * (data / 5))  # write data is FW value
            self.page_select(0xE4)
            self.my_i2c.write_bytes_maximum_55bytes(168, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        elif pcba_info == '1831101388_ver1.01' or pcba_info == '1831101391_ver1.01' or pcba_info == '1831101411_ver1.02':
            buff = int(65536 * (data / 5))
            self.page_select(0xE4)
            self.my_i2c.write_bytes_maximum_55bytes(168, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        else:
            print('current PCBA' + pcba_info + "can't be supported.")
        if display:
            print('tx_voa_x_p:' + '{:.4f}'.format(data) + 'V')

    def save_eeprom_tx_voa_x_max(self, data, pcba_info='1831101381_ver1.01'):
        if pcba_info == '1831101381_ver1.01':
            self.page_select(0xC2)
            buff = int(4095 * (data / 5))  # write data is FW value
            self.my_i2c.write_bytes_maximum_55bytes(0xD0, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        elif pcba_info == '1831101388_ver1.01' or pcba_info == '1831101391_ver1.01' or pcba_info == '1831101411_ver1.02':
            self.page_select(0xC2)
            buff = int(65536 * (data / 5))  # write data is FW value
            self.my_i2c.write_bytes_maximum_55bytes(0xD0, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        else:
            print('current PCBA' + pcba_info + "can't be supported.")

    def save_eeprom_tx_voa_x_min(self, data, pcba_info='1831101381_ver1.01'):
        if pcba_info == '1831101381_ver1.01':
            self.page_select(0xC2)
            buff = int(4095 * (data / 5))  # write data is FW value
            self.my_i2c.write_bytes_maximum_55bytes(0xD8, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        elif pcba_info == '1831101388_ver1.01' or pcba_info == '1831101391_ver1.01' or pcba_info == '1831101411_ver1.02':
            self.page_select(0xC2)
            buff = int(65536 * (data / 5))  # write data is FW value
            self.my_i2c.write_bytes_maximum_55bytes(0xD8, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        else:
            print('current PCBA' + pcba_info + "can't be supported.")

    def tx_voa_y_p_set(self, data, display=False, pcba_info='1831101381_ver1.01'):
        if pcba_info == '1831101381_ver1.01':
            self.page_select(0xE4)
            buff = int(4095 * (data / 5))  # write data is FW value
            self.my_i2c.write_bytes_maximum_55bytes(172, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        elif pcba_info == '1831101388_ver1.01' or pcba_info == '1831101391_ver1.01' or pcba_info == '1831101411_ver1.02':
            self.page_select(0xE4)
            buff = int(65536 * (data / 5))  # write data is FW value
            self.my_i2c.write_bytes_maximum_55bytes(172, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        if display:
            print('tx_voa_y_p:' + '{:.4f}'.format(data) + 'V')

    def save_eeprom_tx_voa_y_max(self, data, pcba_info='1831101381_ver1.01'):
        if pcba_info == '1831101381_ver1.01':
            self.page_select(0xC2)
            buff = int(4095 * (data / 5))  # write data is FW value
            self.my_i2c.write_bytes_maximum_55bytes(0xD4, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        elif pcba_info == '1831101388_ver1.01' or pcba_info == '1831101391_ver1.01' or pcba_info == '1831101411_ver1.02':
            self.page_select(0xC2)
            buff = int(65536 * (data / 5))  # write data is FW value
            self.my_i2c.write_bytes_maximum_55bytes(0xD4, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        else:
            print('current PCBA' + pcba_info + "can't be supported.")

    def save_eeprom_tx_voa_y_min(self, data, pcba_info='1831101381_ver1.01'):
        if pcba_info == '1831101381_ver1.01':
            self.page_select(0xC2)
            buff = int(4095 * (data / 5))  # write data is FW value
            self.my_i2c.write_bytes_maximum_55bytes(0xDC, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        elif pcba_info == '1831101388_ver1.01' or pcba_info == '1831101391_ver1.01' or pcba_info == '1831101411_ver1.02':
            self.page_select(0xC2)
            buff = int(65536 * (data / 5))  # write data is FW value
            self.my_i2c.write_bytes_maximum_55bytes(0xDC, [buff >> 8, buff & 0xFF])
            time.sleep(0.01)
        else:
            print('current PCBA' + pcba_info + "can't be supported.")

    def get_eeprom_setting(self, pcba_info='1831101381_ver1.01'):
        eeprom_info = {}
        self.page_select(0xC2)
        buff = self.my_i2c.read_bytes_maximum_58bytes(208, 14)
        data_u16 = [(msb << 8) | lsb for msb, lsb in zip(buff[0::2], buff[1::2])]
        if pcba_info == '1831101381_ver1.01':
            eeprom_info.update(TX_VOA_XP_MAX=data_u16[0] / 4096 * 5)
            eeprom_info.update(TX_VOA_YP_MAX=data_u16[2] / 4096 * 5)
            eeprom_info.update(TX_VOA_XP_MIN=data_u16[4] / 4096 * 5)
            eeprom_info.update(TX_VOA_YP_MIN=data_u16[6] / 4096 * 5)
        elif pcba_info == '1831101388_ver1.01' or pcba_info == '1831101391_ver1.01' or pcba_info == '1831101411_ver1.02':
            eeprom_info.update(TX_VOA_XP_MAX=data_u16[0] / 65536 * 5)
            eeprom_info.update(TX_VOA_YP_MAX=data_u16[2] / 65536 * 5)
            eeprom_info.update(TX_VOA_XP_MIN=data_u16[4] / 65536 * 5)
            eeprom_info.update(TX_VOA_YP_MIN=data_u16[6] / 65536 * 5)
        else:
            print('current pcba_ver' + pcba_info + 'can not be supported.')
        return eeprom_info

    def Enable_Disable_tuningmode(self, mode=0x00):
        self.page_select(0xE4)
        self.my_i2c.write_bytes_maximum_55bytes(0xC0, [mode])

    def Read_RA_tuning_data(self):
        self.page_select(0xE2)
        rsp = self.my_i2c.read_bytes_maximum_128bytes(0x90, 96)
        slope_list = []
        ratio_list = []
        for i in range(0, 48, 4):
            t_slope = struct.unpack('<f', bytearray([rsp[i + 3], rsp[i + 2], rsp[i + 1], rsp[i]]))
            t_ratio = struct.unpack('<f', bytearray([rsp[48 + i + 3], rsp[48 + i + 2], rsp[48 + i + 1], rsp[48 + i]]))
            slope_list.append('{:.4f}'.format(t_slope[0]))
            ratio_list.append('{:.4f}'.format(t_ratio[0]))
        return ratio_list, slope_list

    # def Copy_RA_tuning_data(self):
    #     # self.page_select(0xE0)
    #     # Realtime_slope = self.my_i2c.read_bytes_maximum_58bytes(0xB8, 24)
    #     # #slope = self.my_i2c.read_bytes_maximum_58bytes(0xA0, 24)
    #     # self.page_select(0xC2)
    #     # self.my_i2c.write_bytes_maximum_55bytes(0x90, Realtime_slope)
    #     # self.my_i2c.write_bytes_maximum_55bytes(0xE0, [0xAA])
    #     self.page_select(0xE0)
    #     Realtime_slope = self.my_i2c.read_bytes_maximum_58bytes(0xB8, 24)
    #     # slope = self.my_i2c.read_bytes_maximum_58bytes(0xA0, 24)
    #     self.page_select(0xC2)
    #     self.my_i2c.write_bytes_maximum_55bytes(0x90, Realtime_slope[0:16])
    #     self.my_i2c.write_bytes_maximum_55bytes(0xA0, Realtime_slope[16:])

    def Copy_RA_tuning_data(self):
        self.page_select(0xE2)
        realtime_ratio = self.my_i2c.read_bytes_maximum_58bytes(0xC0, 48)
        self.page_select(0xC5)
        for i in range(6):
            self.my_i2c.write_bytes_maximum_55bytes(0x80 + i * 8, realtime_ratio[i * 8:i * 8 + 8])
            time.sleep(0.5)

    def get_abc_mode(self):
        self.page_select(0xC2)
        val = self.my_i2c.read_bytes_maximum_58bytes(0xE0, 1)[0]
        if val == 0x55:
            abc_mode = 'Normal'
        elif val == 0x00:
            abc_mode = 'Tuning'
        else:
            abc_mode = 'None'
        return abc_mode

    def set_abc_mode(self, mode='Normal'):
        self.page_select(0xC2)
        if mode == 'Normal':
            self.my_i2c.write_bytes_maximum_55bytes(0xE0, [0x55])
        if mode == 'Tuning':
            self.my_i2c.write_bytes_maximum_55bytes(0xE0, [0x00])

    def save_eeprom_rx_oa_all(self):
        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0x98, 8)
        self.page_select(0xC2)
        self.my_i2c.write_bytes_maximum_55bytes(0xC4, buff)

    def read_eeprom_rx_oa_all(self):
        self.page_select(0xC2)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0xC4, 8)
        data = []
        for msb, lsb in zip(buff[0::2], buff[1::2]):
            data.append((msb << 8 | lsb) * 2.5 / 4096)
        return data  # parameter sequence(XI, XQ, YI, YQ)

    def save_eeprom_tx_vg_all(self):
        # self.page_select(0xE4)
        # buff = self.my_i2c.read_bytes_maximum_58bytes(0xA0, 8)
        # self.page_select(0xC2)
        # self.my_i2c.write_bytes_maximum_55bytes(0xBC, buff)
        self.page_select(0xE4)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0xA0, 8)
        self.page_select(0xC2)
        reg_add = 0xBC
        for val in buff:
            self.my_i2c.write_bytes_maximum_55bytes(reg_add, [val])  # FW maybe need to update for fix this problem.
            reg_add += 1

    def read_eeprom_tx_vg_all(self):
        self.page_select(0xC2)
        buff = self.my_i2c.read_bytes_maximum_58bytes(0xBC, 8)
        data = []
        for msb, lsb in zip(buff[0::2], buff[1::2]):
            data.append((msb << 8 | lsb) * 2.5 / 4096)
        return data  # parameter sequence(XI, XQ, YI, YQ)

    def voa_set(self, val, timeout=90):
        # print('voa value:' + str(val))
        self.page_select(0x03)
        self.my_i2c.write_bytes_maximum_55bytes(0xF0, [val])
        time.sleep(5)
        start_time = time.time()
        while True:
            data = self.my_i2c.read_bytes_maximum_58bytes(0xF1, 1)[0]
            if data == 0xAA:
                # print('It costs almost ' + str(time.time() - start_time) + ' s to get voa status.')
                return True
            elif (time.time() - start_time) >= timeout:
                print('time out for getting voa status, status is 0x' + '{:02x}'.format(data))
                os._exit()
            else:
                time.sleep(5)

    #################################Calibration#############################################################################
    def Calibration_VG_slope(self, pcba_info, temp):
        buff = self.get_internal_temp_volt(pcba_info)
        Module_temp = buff['Module_TEMP']
        vg_info = self.get_tx_vg_slope()
        Tuning_Temp = vg_info['Tuning_pre_cal_temperature']
        temp_diff = float(Module_temp - Tuning_Temp)
        print(temp_diff)

        dac_info = self.get_dac_setting(pcba_info)
        tx_vg_xi = dac_info['TX_VG_XI']
        tx_vg_xq = dac_info['TX_VG_XQ']
        tx_vg_yi = dac_info['TX_VG_YI']
        tx_vg_yq = dac_info['TX_VG_YQ']

        vg_value = self.get_tx_vg()
        RT_txvg_xi = vg_value['TX_vg_xi']
        RT_txvg_xq = vg_value['TX_vg_xq']
        RT_txvg_yi = vg_value['TX_vg_yi']
        RT_txvg_yq = vg_value['TX_vg_yq']
        vg_diff = [(tx_vg_xi - RT_txvg_xi), (tx_vg_xq - RT_txvg_xq), (tx_vg_yi - RT_txvg_yi), (tx_vg_yq - RT_txvg_yq)]
        print(vg_diff)

        slop_vg = []
        add = 130
        if temp == 'HT':
            add = 130
        elif temp == 'LT':
            add = 178
        for vg in vg_diff:
            slop_vg_origin = float(vg / temp_diff)
            slop_vg.append(slop_vg_origin)  # tx_vg_slope = HT(vg)-RT(vg) / HT(cosa temp)- RT(temp cal)
            # tx_vg_LT_slope = LT(VG)-RT(VG)/ LT(COSA TEMP ) - RT(TEMP CAL)
            self.set_tx_vg_slope(add, slop_vg_origin * 10000)
            add += 2
        return slop_vg

    def loop_set(self, loop='TX_VG', state='ON'):
        self.page_select(0xC1)
        val = self.my_i2c.read_bytes_maximum_58bytes(0xF0, 1)[0]
        if loop == 'TX_VG':
            if state == 'ON':
                self.my_i2c.write_bytes_maximum_55bytes(0xF0, [val | 0x01])
            if state == 'OFF':
                self.my_i2c.write_bytes_maximum_55bytes(0xF0, [val & 0xFE])

    def get_loop_status(self):
        loop_info = {}
        self.page_select(0xC1)
        val = self.my_i2c.read_bytes_maximum_58bytes(0xF0, 1)[0]
        if (val & 0x01) == 0x01:
            status = 'ON'
        else:
            status = 'OFF'
        loop_info.update(TX_VG=status)  # bit0 for TX_VG loop
        if ((val & 0x04) >> 2) == 0x01:
            status = 'ON'
        else:
            status = 'OFF'
        loop_info.update(TX_VOA=status)  # bit2 for TX_VOA loop
        if ((val & 0x10) >> 4) == 0x01:
            status = 'ON'
        else:
            status = 'OFF'
        loop_info.update(RX_OA=status)
        return loop_info

    def get_rx_los_check_flag(self):
        self.page_select(0xC1)
        return self.my_i2c.read_bytes_maximum_58bytes(0xEE, 1)[0]

    def read_los_threshold(self):
        self.page_select(0xC0)
        val = self.my_i2c.read_bytes_maximum_58bytes(0xF8, 4)
        down_threshold = (val[0] << 8 | val[1])
        up_threshold = (val[2] << 8 | val[3])
        if down_threshold > 0x7FFF:
            down_threshold = down_threshold - 0x10000
        if up_threshold > 0x7FFF:
            up_threshold = up_threshold - 0x10000
        return down_threshold / 100, up_threshold / 100

    def set_los_threshold(self, gc_avg, threshold='down'):
        self.page_select(0xC0)
        if threshold == 'down':
            self.my_i2c.write_bytes_maximum_55bytes(0xF8, [gc_avg >> 8, gc_avg & 0xFF])
        elif threshold == 'up':
            self.my_i2c.write_bytes_maximum_55bytes(0xFA, [gc_avg >> 8, gc_avg & 0xFF])
        else:
            print('Threshold select error!')

    def Write_pcba_DAC(self, data):
        buff = int(data)
        self.my_i2c.write_bytes_PCBA_DAC([buff >> 8, buff & 0xFF])
        time.sleep(0.01)

    def get_op_step_data(self):
        rsp = self.send_cdb_lpl(0x9120, 96)
        op_data = []
        for i in range(3):
            step_data = [0] * 10
            step_data[0] = rsp[i * 24 + 1] * 256 + rsp[i * 24 + 0]
            step_data[1] = rsp[i * 24 + 3] * 256 + rsp[i * 24 + 2]
            step_data[2] = rsp[i * 24 + 5] * 256 + rsp[i * 24 + 4]
            step_data[3] = rsp[i * 24 + 7] * 256 + rsp[i * 24 + 6]
            step_data[4] = rsp[i * 24 + 9] * 256 + rsp[i * 24 + 8]
            step_data[5] = rsp[i * 24 + 13] * 256 + rsp[i * 24 + 12]
            step_data[6] = rsp[i * 24 + 15] * 256 + rsp[i * 24 + 14]
            step_data[7] = rsp[i * 24 + 17] * 256 + rsp[i * 24 + 16]
            step_data[8] = rsp[i * 24 + 19] * 256 + rsp[i * 24 + 18]
            step_data[9] = rsp[i * 24 + 21] * 256 + rsp[i * 24 + 20]
            op_data.append(step_data)
        return op_data[2]

    def set_inner_tuner_point(self, data):
        full_scale = 65535
        Vref = 5
        max_volt = 20.25
        self.tx_heater_set(xip=(data[0] / full_scale * Vref) ** 2, sweep_type=False,
                           max_volt=max_volt)  # xip is square of xip voltage
        self.tx_heater_set(xqp=(data[1] / full_scale * Vref) ** 2, sweep_type=False, max_volt=max_volt)
        self.tx_heater_set(yip=(data[2] / full_scale * Vref) ** 2, sweep_type=False, max_volt=max_volt)
        self.tx_heater_set(yqp=(data[3] / full_scale * Vref) ** 2, sweep_type=False, max_volt=max_volt)
