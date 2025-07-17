from __future__ import division, with_statement, print_function
from totalphase.aardvark_py import *
from ctypes import *


class IIC_R_W:
    def __init__(self, port=0, bit_rate=400, timeout=150, ch=0x00, addr=0xA0):
        self.port = port
        self.bit_rate = bit_rate
        self.timeout = timeout
        self.myHandle = aa_open(self.port)
        self.ch = ch
        self.addr = addr

        aa_configure(self.myHandle, AA_CONFIG_SPI_I2C)
        aa_i2c_pullup(self.myHandle, AA_I2C_PULLUP_BOTH)
        aa_i2c_bitrate(self.myHandle, bit_rate)
        aa_i2c_bus_timeout(self.myHandle, self.timeout)

    def close(self):
        aa_close(self.myHandle)

    def i2c_read(self, offset, length):
        # response = self.read_max_128bytes(dev_addr, offset, length)
        aa_i2c_write(self.myHandle, self.addr >> 1, AA_I2C_NO_STOP, array('B', [offset & 0xff]))
        (count, data_in) = aa_i2c_read(self.myHandle, self.addr >> 1, AA_I2C_NO_FLAGS, length)
        # print("count:", count)
        # print("data_in:\n", data_in)
        return data_in

    def i2c_write(self, offset, data):
        length = len(data)
        data_out = array('B', [0 for i in range(1 + length)])

        data_out[0] = offset & 0xff

        for i in range(length):
            data_out[1 + i] = data[i] & 0xFF

        aa_i2c_write(self.myHandle, self.addr >> 1, AA_I2C_NO_FLAGS, data_out)

    def i2c_write_page(self, page, data):
        self.i2c_write(0x7F, [page])
        self.i2c_write(0x80, data)

    def write_bytes_maximum_55bytes(self, offset, data):
        self.i2c_write(offset, data)

    def write_bytes_maximum_128bytes(self, offset, data):
        self.i2c_write(offset, data)

    def read_bytes_maximum_58bytes(self, offset, length):
        return self.i2c_read(offset, length)

    def read_bytes_maximum_128bytes(self, offset, length):
        return self.i2c_read(offset, length)

    def read_ADC(self):
        # dummy EVB ADC result
        rx_buffer = [0]*24
        return rx_buffer[5:5+18]

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