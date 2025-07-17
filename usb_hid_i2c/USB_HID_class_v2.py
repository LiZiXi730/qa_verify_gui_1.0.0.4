import time
from pywinusb import hid


class HidCommunicate:
    def __init__(self, vendor_id=0x0486, product_id=0x5750):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.filter = hid.HidDeviceFilter(vendor_id=self.vendor_id, product_id=self.product_id)
        self.hid_device = self.filter.get_devices()[0]
        self.hid_device.open()
        self.rx_buffer = 0  # default value

        def readdata(data):
            self.rx_buffer = data
            return None

        self.hid_device.set_raw_data_handler(readdata)

    def send(self, tx_buffer):
        counter = 0
        for i in range(0, 3):
            try:
                self.hid_device.send_output_report(tx_buffer)
                time.sleep(0.1)  # this is very important!! wait at least 0.08s
            except:
                self.filter = hid.HidDeviceFilter(vendor_id=self.vendor_id, product_id=self.product_id)
                self.hid_device = self.filter.get_devices()[0]
                self.hid_device.open()
                print('HID communication error occurs, try to reopen HID device.')
            else:
                break
            counter += 1
        if counter >= 3:

            print('HID communication still fails after has been tried three times.')



    def close(self):
        self.hid_device.close()


""" below is verification of the above class definition,
     can be used as template 
"""
"""
buffer = [0x00] * 65  # 65 = report size + 1 byte (report id)
buffer[0] = 0x00  # report id
buffer[1] = 0x55
buffer[2] = 0x49
buffer[3] = 0x01
buffer[4] = 0x01
buffer[5] = 0x02
buffer[6] = 0xA0
buffer[64] = 0x42

myhid = HidCommunicate()
myhid.send(buffer)  # data to be sent is stored in buffer
print(myhid.rx_buffer)  # received data is stored in myhid.rx_buffer
myhid.close()
"""

