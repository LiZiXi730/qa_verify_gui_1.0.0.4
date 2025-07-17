from GDK_200_09282019_Ye import GDK_200
import json
import os


class CreateDut:
    # def __init__(self, config_file):
    #     self.config_file = os.getcwd() + '//config_file//' + config_file
    #     if os.path.exists(self.config_file):
    #         self._load_config()  # Don't need to load configure file when communicate with module. Modified by lili

    # def _load_config(self):
    #     with open(self.config_file) as f:
    #         self.config = json.load(f)

    def get_i2c_ch_burn_in(self):
        dut_idx_5593_burn_in = {'A1': 0, 'A2': 1, 'B1': 2, 'B2': 3, 'C1': 4, 'C2': 5}  # key means I2C CH, value means 5593 channel
        dut_idx_burn_in = {'A2': 0, 'A1': 1, 'B2': 2, 'B1': 3, 'C1': 4, 'C2': 5}  # key means skill print
        dut_i2c_ch = {}
        dut_5593_ch = {}
        for dut, name in zip(['dut1', 'dut2', 'dut3', 'dut4'], [self.config['dut1_footprint'], self.config['dut2_footprint'], self.config['dut3_footprint'], self.config['dut4_footprint']]):
            if name:
                dut_i2c_ch.update({dut: dut_idx_burn_in.get(name)})
                dut_5593_ch.update({dut: dut_idx_5593_burn_in.get(name)})
        return dut_i2c_ch, dut_5593_ch

    def _create_dut(self, vid=0x0486, pid=0x5750, i2c_ch=2, i2c_drv=1):
        self.dut = GDK_200(vendor_id=vid, product_id=pid, ch=i2c_ch, addr=0xA0, i2c_drv=i2c_drv)
        print('400G Design Kit has been created!')
