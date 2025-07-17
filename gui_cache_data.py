import re
import os


class Data:
	def __init__(self):
		self.osa_model = "osa20"
		self.osa_address = "GPIB0::10::INSTR"
		self.osa_default_setting = '100gosnr7.wdm'
		self.att1_GPIB_addr = 'GPIB0::5::INSTR'
		self.att2_GPIB_addr = 'GPIB0::4::INSTR'
		self.att3_GPIB_addr = 'GPIB0::3::INSTR'
		self.tof_model = "100A"
		self.pm_GPIB_address = 'GPIB0::12::INSTR'
		self.att3_idle = 10.0
		self.att2_idle = 1.0
		self.att123_default_lambda = 1550
		self.att123_default_offset = 0.0
		self.att1_ase_init_hi = 30.0
		self.att1_ase_init_lo = 3.0
		self.osnr_err_max = 0.05
		self.slope_delta_osnr_delta_att1_ase = 3.0
		self.osnr_now = 0.0
		self.tof_bw = 0.6
		self.osa_bw = 5.0
		self.pm3_chn = '3'
		self.pm2_chn = '2'
		self.pm23_reading_digit = 3
		self.pm3_offset = 9.769
		self.pm2_offset = 9.223
		self.data_file_name = 'osnr_pin_sweep_try.txt'
		self.itla_chn = 90
		self.osnr_lo = 13.0
		self.osnr_hi = 16.0
		self.osnr_step = 1.0
		self.pow_lo = -15.0
		self.pow_hi = -13.0
		self.pow_step = 1.0

		self.instrument_file = 'osnr_instruments.txt'
		self.setting_file = 'test_setting.txt'
		self.Calibration_config = 'Calibration_config.txt'

		self.dut_pcba = '1831101381_ver1.01'
		self.dut_port = 'com4'
		self.ref_obj = None
		self.sig_ref_obj = False
		self.dut_cur = None  # object for current dut module
		self.station = 'HQ'
		self.evb_type = 'Dual/Single QDD'
		self.osnrstation = None
		self.pwd_gui = 'MOLEX'
		self.sig_pwd_gui = False
		self.dut_i2c_ch = {}
		self.dut_5593_ch = {}
		self.lot_record = {'dut1': {}, 'dut2': {}, 'dut3': {}, 'dut4': {}}
		self.report_header = {'dut1': {}, 'dut2': {}, 'dut3': {}, 'dut4': {}}
		self.test_temp = []
		self.version = ''
		self.test_spec = ''
		self.sig_cal = True

		self.pro_info_zh = {item: '' for item in ['site', 'operator', 'station', 'resource']}
		self.fusion_a = None
		self.folder_path = ''
		self.com_config = {'dut': {}, 'ref_dut': {}}
		self.dut_obj = None                     # object for selected module, it maybe reference module or dut module