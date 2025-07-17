import tkinter
from CreateDut import CreateDut
# from tkinter import ttk
import tkinter.font as tkFont



class DutSelectUi:
    def on_create(self, frame, data):
        self.frame = frame
        self.data = data

        tkinter.Label(self.frame, text="I2C_DRV").grid(column=0, row=0, sticky=tkinter.E)
        self.i2c_drv_str = tkinter.StringVar()
        self.all_i2c_drvs = {'USB_HID': 1, 'TOTAL_PHASE': 2}
        self.i2c_drvs_pop = tkinter.OptionMenu(self.frame, self.i2c_drv_str, *self.all_i2c_drvs.keys())
        # self.i2c_drv_str.set('USB_HID')  # default value
        if data.com_config['dut']['com_type'] == '1':
            self.i2c_drv_str.set('USB_HID')
        else:
            self.i2c_drv_str.set('TOTAL_PHASE')
        self.i2c_drvs_pop.grid(column=1, row=0, sticky=tkinter.E, columnspan=2)
        self.i2c_drvs_pop.config(width=18, state='disable')

        tkinter.Label(self.frame, text="HID_VID").grid(column=0, row=1, sticky=tkinter.E)
        self.vid_str = tkinter.StringVar()
        # self.vid_str.set('0x0486')
        self.vid_str.set(data.com_config['dut']['vid'])
        self.entry_vid = tkinter.Entry(self.frame, width=10, textvariable=self.vid_str)
        self.entry_vid.grid(column=1, row=1, sticky=tkinter.E, columnspan=2)
        self.entry_vid.config(width=18, state='disable')

        label1 = tkinter.Label(self.frame, text="HID_PID").grid(column=0, row=2, sticky=tkinter.E)
        self.pid_str = tkinter.StringVar()
        # self.pid_str.set('0x5750')
        self.pid_str.set(data.com_config['dut']['pid'])
        self.entry_pid = tkinter.Entry(self.frame, width=10, textvariable=self.pid_str)
        self.entry_pid.grid(column=1, row=2, sticky=tkinter.E, columnspan=2)
        self.entry_pid.config(width=18, state='disable')

        self.lb1_i2c_ch = tkinter.Label(self.frame, text="DUT_I2C_CH:")
        self.lb1_i2c_ch.grid(column=0, row=3, sticky=tkinter.E)
        self.lb1_i2c_ch_str = tkinter.StringVar()
        self.all_i2c_chs = {'QDD1': 0, 'QDD2': 1}
        self.lb1_i2c_ch_pop = tkinter.OptionMenu(self.frame, self.lb1_i2c_ch_str, *self.all_i2c_chs.keys())
        # self.lb1_i2c_ch_str.set('QDD1')  # default value
        if data.com_config['dut']['i2c_ch'] == '0':
            self.lb1_i2c_ch_str.set('QDD1')
        else:
            self.lb1_i2c_ch_str.set('QDD2')
        self.lb1_i2c_ch_pop.grid(column=1, row=3, sticky=tkinter.W, columnspan=2)
        self.lb1_i2c_ch_pop.config(width=18, state='disable')

        ft = tkFont.Font(family='Arial', size=50, weight=tkFont.BOLD)
        self.label_result = tkinter.Label(self.frame, text='Welcome', font=ft, fg='blue')
        self.label_result.grid(column=3, row=0, rowspan=4, pady=5, padx=40)

        # self.btn_display = tkinter.Button(self.frame, text="Connect", command=self.connect_dut, width=8)
        # self.btn_display.grid(column=3, row=1, rowspan=2, sticky=tkinter.W, pady=10, padx=20)

    def connect_dut(self):
        self.mydut = CreateDut()  # file names shouldn't be changed, linked to json_write script
        self.mydut._create_dut(pid=int(self.pid_str.get(), 16), vid=int(self.vid_str.get(), 16),
                               i2c_ch=self.all_i2c_chs[self.lb1_i2c_ch_str.get()],
                               i2c_drv=self.all_i2c_drvs[self.i2c_drv_str.get()])
        self.data.dut_obj = self.mydut.dut




