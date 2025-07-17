from usb_hid_i2c.USB_HID_class_v2 import HidCommunicate
import time
from math import ceil
import numpy as np
from ctypes import *


class IIC_R_W:
    def __init__(self, vendor_id=0x0486, product_id=0x5750, ch=0x00, addr=0xA0):
        self.vid = vendor_id
        self.pid = product_id
        self.myhid = HidCommunicate(self.vid, self.pid)
        self.ch = ch
        self.addr = addr

    def close(self):
        self.close()

    def read_bytes_maximum_58bytes(self, offset, length):
        if length > 58:
            raise ("number of read length is" + str(length) + ",exceeds 58bytes.")
            return None
        else:
            buffer = [0x00] * 65  # 65 = report size + 1 byte (report id)
            buffer[0] = 0x00  # report id
            buffer[1] = 0x55
            buffer[2] = 0x49
            buffer[3] = 0x01
            buffer[4] = length
            buffer[5] = self.ch
            buffer[6] = self.addr
            buffer[7] = offset

            sum = 0x00
            for value in buffer:
                sum += value
            buffer[64] = (sum & 0xFF)
            self.myhid.send(buffer)
            time.sleep(0.1)
            return self.myhid.rx_buffer[5:5 + length]

    def write_bytes_maximum_55bytes(self, offset, data=[]):
        write_len = len(data)
        if write_len > 55:
            raise ("number of data length is" + str(write_len) + ",exceeds 55bytes.")
        else:
            buffer = [0x00] * 65  # 65 = report size + 1 byte (report id)
            buffer[0] = 0x00  # report id
            buffer[1] = 0x55
            buffer[2] = 0x49
            buffer[3] = 0x02
            buffer[4] = write_len
            buffer[5] = self.ch
            buffer[6] = self.addr
            buffer[7] = offset
            buffer[8:8 + write_len] = data

            sum = 0x00
            for value in buffer:
                sum += value
            buffer[64] = (sum & 0xFF)
            self.myhid.send(buffer)
            time.sleep(0.02)
        return None

    def read_bytes_maximum_128bytes(self, offset, length):
        if length > 128:
            print("number of read length is" + str(length) + ",exceeds maximum length 128.")
            return None
        else:
            len_remainder = length
            cur_offset = offset
            rx_data = []
            # rx_data = np.array([])
            read_range = int((length + 57) / 58)
            for i in range(0, read_range):
                if len_remainder > 58:
                    # cur_rx = np.array(self.read_bytes_maximum_58bytes(cur_offset, 58))
                    cur_rx = self.read_bytes_maximum_58bytes(cur_offset, 58)
                    len_remainder -= 58
                    cur_offset += 58
                else:
                    # cur_rx = np.array(self.read_bytes_maximum_58bytes(cur_offset, len_remainder))
                    cur_rx = self.read_bytes_maximum_58bytes(cur_offset, len_remainder)
                rx_data += cur_rx
                # rx_data = np.hstack([rx_data, cur_rx])
            return rx_data

    def write_bytes_maximum_128bytes(self, offset, data):
        if len(data) > 128:
            raise ("length of written data is" + str(len(data)) + ",exceeds maximum length 128.")
        else:
            remain_data = data
            cur_offset = offset
            write_range = int((len(data) + 54)/55)
            for i in range(0, write_range):
                if len(remain_data) >= 55:
                    cur_data = remain_data[0:55]
                    self.write_bytes_maximum_55bytes(cur_offset, cur_data)
                    remain_data = remain_data[55:]
                    cur_offset += 55
                else:
                    self.write_bytes_maximum_55bytes(cur_offset, remain_data)

    def write_bytes_PCBA_DAC(self, data=[]):
        buffer = [0x00] * 65  # 65 = report size + 1 byte (report id)
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x44
        buffer[3] = 0x01
        buffer[4] = 0x02
        if self.ch == 0:  # for QDD1(I2C channel is 0, which means DAC channel is 0x01)
            buffer[5] = 0x01
        else:
            print(' DAC set function only support QDD1')
        buffer[6] = 0x0
        buffer[7] = data[1]
        buffer[8] = data[0]
        sum = 0x00
        for value in buffer:
            sum += value
        buffer[64] = (sum & 0xFF)
        print(buffer)
        self.myhid.send(buffer)
        time.sleep(0.02)
        return None

    """
    def i2c_read(self, offset, length):
        response = self.read_bytes_maximum_128bytes(offset, length)
        return response

    def i2c_write(self, offset, data):
        self.write_bytes_maximum_128bytes(offset, data)
"""
    def i2c_write_page(self, page, data):
        self.write_bytes_maximum_55bytes(0x7F, [page])
        self.write_bytes_maximum_128bytes(offset=0x80, data=data)

    def read_ADC(self):
        buffer = [0x00] * 65  # 65 = report size + 1 byte (report id)
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x41
        buffer[3] = 0x01
        buffer[4] = 0x00
        sum = 0x00
        for value in buffer:
            sum += value
        buffer[64] = (sum & 0xFF)
        self.myhid.send(buffer)
        time.sleep(0.1)
        return (self.myhid.rx_buffer[5:5+18])

    def read_EVB_FW_Ver(self):
        buffer = [0x00] * 65  # 65 = report size + 1 byte (report id)
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x56
        buffer[3] = 0x01
        buffer[4] = 0x00
        sum = 0x00
        for value in buffer:
            sum += value
        buffer[64] = (sum & 0xFF)
        self.myhid.send(buffer)
        time.sleep(0.1)
        return (self.myhid.rx_buffer[5:5+14])

    def gpio_set_evb(self, gpio_id=81, value=0):
        buffer = [0x00] * 65  # 65 = report size + 1 byte (report id)
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x47
        buffer[3] = 0x02
        buffer[4] = 0x01
        buffer[5] = gpio_id
        buffer[6] = value
        sum = 0x00
        for value in buffer:
            sum += value
        buffer[64] = (sum & 0xFF)
        self.myhid.send(buffer)

    def gpio_get_evb(self, gpio_id=81):
        buffer = [0x00] * 65  # 65 = report size + 1 byte (report id)
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x47
        buffer[3] = 0x01
        buffer[4] = 0x01
        buffer[5] = gpio_id
        sum = 0x00
        for value in buffer:
            sum += value
        buffer[64] = (sum & 0xFF)
        self.myhid.send(buffer)
        time.sleep(0.1)
        return self.myhid.rx_buffer[5]

    def convert(self,hex):
        i = int(hex, 16)  # convert from hex to a Python int
        cp = pointer(c_int(i))  # make this into a c integer
        fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
        return fp.contents.value

    def replace_bit(self,data,star, end, new):
        a = (data >> end + 1) & 0xFFFF
        print(a)
        b = (data << (16 - star) & 0xFFFF) >> (16 - star)
        print(b)
        new_num = (a << end + 1) & 0xFFFF | (new << star | b)
        return new_num

    def replace_bit8(self,data, star, end, new):
        a = (data >> end + 1) & 0xFF
        print(a)
        b = (data << (8 - star) & 0xFF) >> (8 - star)
        print(b)
        new_num = (a << end + 1) & 0xFF | (new << star | b)
        return new_num

    def set_onebit(self,v, index, x):
        """Set the index:th bit of v to 1 if x is truthy, else to 0, and return the new value."""
        mask = 1 << index  # Compute mask, an integer with just bit 'index' set.
        print(mask)
        v &= ~mask  # Clear the bit indicated by the mask (if x is False)
        print(v)
        if x:
            v |= mask  # If x was True, set the bit indicated by the mask.
        return v

    def sel_ch_9548(self, ch=0):
        buffer = [0x00] * 65
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x49
        buffer[3] = 0x02
        buffer[4] = 0x00
        buffer[5] = 0x00
        buffer[6] = 0xE0
        sum = 0x00
        if ch in range(0, 7):
            for i in range(3):  # try 3 times
                buffer[7] = (1 << int(ch))
                for value in buffer:
                    sum += value
                buffer[64] = (sum & 0xFF)
                self.myhid.send(buffer)
                rx_ch = self.get_ch_9548()
                if rx_ch == 1 << int(ch):
                    return True
                elif i == 2:
                    print('select dut failed, set channel is ' + str(ch) + ', actual channel is ' + str(rx_ch))
                    return False
        else:
            print('ch info' + str(ch) + ' is invalid for 9548')
            return False

    def get_ch_9548(self):
        buffer = [0x00] * 65
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x49
        buffer[3] = 0x03
        buffer[4] = 0x01
        buffer[5] = 0x00
        buffer[6] = 0xE0
        sum = 0x00
        for value in buffer:
            sum += value
        buffer[64] = (sum & 0xFF)
        self.myhid.send(buffer)
        time.sleep(0.1)
        return self.myhid.rx_buffer[5]  # channel is the current bit

    def init_5593(self):
        self.sel_ch_9548(6)
        self.enable_buffer_5593()
        self.set_ref_volt_5593()
        self.config_adc_5593()

    def enable_buffer_5593(self):
        buffer = [0x00] * 65
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x49
        buffer[3] = 0x02
        buffer[4] = 0x02
        buffer[5] = 0x00
        buffer[6] = 0x20
        buffer[7] = 0x03
        buffer[8] = 0x00
        buffer[9] = 0x00
        sum = 0x00
        for value in buffer:
            sum += value
        buffer[64] = (sum & 0xFF)
        self.myhid.send(buffer)

    def set_ref_volt_5593(self):
        buffer = [0x00] * 65
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x49
        buffer[3] = 0x02
        buffer[4] = 0x02
        buffer[5] = 0x00
        buffer[6] = 0x20
        buffer[7] = 0x0B
        buffer[8] = 0x02
        buffer[9] = 0x00
        sum = 0x00
        for value in buffer:
            sum += value
        buffer[64] = (sum & 0xFF)
        self.myhid.send(buffer)

    def config_adc_5593(self):
        buffer = [0x00] * 65
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x49
        buffer[3] = 0x02
        buffer[4] = 0x02
        buffer[5] = 0x00
        buffer[6] = 0x20
        buffer[7] = 0x04
        buffer[8] = 0x00
        buffer[9] = 0x3F
        sum = 0x00
        for value in buffer:
            sum += value
        buffer[64] = (sum & 0xFF)
        self.myhid.send(buffer)

    def sel_ch_adc_5593(self, ch=0):
        buffer = [0x00] * 65
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x49
        buffer[3] = 0x02
        buffer[4] = 0x02
        buffer[5] = 0x00
        buffer[6] = 0x20
        buffer[7] = 0x02
        sum = 0x00
        if ch in range(0, 6):
            buffer[9] = (1 << int(ch))
            for value in buffer:
                sum += value
            buffer[64] = (sum & 0xFF)
            self.myhid.send(buffer)
            #print(buffer)
        else:
            print('ch info' + str(ch) + ' is invalid for 5593')

    def get_i_sense_5593(self):
        buffer = [0x00] * 65  # 65 = report size + 1 byte (report id)
        buffer[0] = 0x00  # report id
        buffer[1] = 0x55
        buffer[2] = 0x49
        buffer[3] = 0x01
        buffer[4] = 0x02
        buffer[5] = 0x00
        buffer[6] = 0x20
        buffer[7] = 0x40
        sum = 0x00
        for value in buffer:
            sum += value
        buffer[64] = (sum & 0xFF)
        self.myhid.send(buffer)
        time.sleep(0.1)
        return (self.myhid.rx_buffer[5] << 8) | self.myhid.rx_buffer[6]

    def read_adc_5593(self, ch=0):
        self.sel_ch_9548(6)
        self.sel_ch_adc_5593(ch)
        time.sleep(1)
        sense_u16 = self.get_i_sense_5593()
        return (sense_u16 & 0x0FFF) / 4095 * 2.5 / 0.2




