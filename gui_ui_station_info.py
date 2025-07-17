import tkinter
import os
import pandas as pd
from fusion_database import ActiveTestApi
import tkinter.font as tkFont
import tkinter.messagebox as msg
from RunCard import RunCard
import openpyxl



class Station:
    def __init__(self):
        self.exit_gui = True      # 初始化返回值，以避免在按窗口关闭按钮时出现错误
        self.setup_file = os.getcwd() + '\\config file\\production setting qaverify.xlsx'    # 本地配置文件路径与名称

    def on_create(self, root, data):
        self.root = root
        self.root.title('User Login')
        width = 300
        height = 300
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        self.root.geometry(str(width) + "x" + str(height) + '+' + str((screenwidth - width) // 2) + '+' + str(
            (screenheight - height) // 2))  # place UI in center of window
        self.root.resizable(False, False)
        self.data = data

        font = tkFont.Font(family='Arial', size=12)
        font1 = tkFont.Font(family='Arial', size=10)
        frame_root = tkinter.LabelFrame(root, text="")
        frame_root.grid(padx=10, pady=10, sticky=tkinter.W)

        tkinter.Label(frame_root, text=r'User Info\用户账号', font=font1).grid(column=0, row=0, columnspan=2, ipady=2)
        self.user_name = tkinter.StringVar()
        self.eny_user = tkinter.Entry(frame_root, width=16, textvariable=self.user_name, font=font)
        self.eny_user.grid(row=1, column=0, columnspan=2, ipady=2)
        self.eny_user.bind('<Return>', self.user_input)

        tkinter.Label(frame_root, text=r'Password\密码', font=font1).grid(column=0, row=2, columnspan=2)
        self.password = tkinter.StringVar()
        self.eny_password = tkinter.Entry(frame_root, width=16, textvariable=self.password, show='*', font=font)
        self.eny_password.grid(row=3, column=0, columnspan=2, ipady=2)
        self.eny_password.bind('<Return>', self.password_input)

        tkinter.Label(frame_root, text=r'Station Number\机台号', font=font1).grid(column=0, row=4, columnspan=2)
        self.station_num = tkinter.StringVar()
        self.eny_station = tkinter.Entry(frame_root, width=16, textvariable=self.station_num, font=font)
        self.eny_station.grid(row=5, column=0, columnspan=2, ipady=2)
        self.eny_station.bind('<Return>', self.station_input)

        tkinter.Label(frame_root, text=r'Resource\工位号', font=font1).grid(column=0, row=6, columnspan=2)
        self.resource = tkinter.StringVar()
        self.eny_resource = tkinter.Entry(frame_root, width=16, textvariable=self.resource, font=font)
        self.eny_resource.grid(row=7, column=0, columnspan=2, ipady=2)
        self.eny_resource.bind('<Return>', self.resource_input)

        self.get_site_info()
        self.loginbtn = tkinter.Button(frame_root, text=r'OK\确认', command=self.check_user_info, width=10, font=font1)
        self.loginbtn.grid(row=8, column=0, sticky=tkinter.W, padx=30, pady=20)
        # if self.data.pro_info_zh['']
        self.loginbtn.bind('<Return>', self.check_user_info)
        abortbtn = tkinter.Button(frame_root, text=r'Abort\放弃', command=self.quit, width=10, font=font1)
        abortbtn.grid(row=8, column=1, sticky=tkinter.W, padx=20, pady=20)

        self.eny_user.focus_set()

    def get_com_config(self):
        setup_file = self.data.folder_path + '\\config file\\production setting qaverify.xlsx'
        if os.path.exists(setup_file):
            df = pd.read_excel(setup_file, sheet_name='Com Config', names=['item', 'value'], index_col=0, dtype=str,
                               keep_default_na=False, usecols=[0, 1])
            for item in ['com_type', 'pid', 'vid', 'i2c_ch', 'auto_move']:
                self.data.com_config['dut'][item] = df['value'][item]
            return True
        else:
            print(setup_file + ' is not exist')
            return False

    def user_input(self, event=None):
        self.eny_password.focus_set()
        pass

    def password_input(self, event=None):
        self.eny_station.focus_set()

    def station_input(self, event=None):
        self. eny_resource.focus_set()

    def resource_input(self, event=None):
        self.loginbtn.focus_set()

    def string_format(self, data):
        return data.strip(' ' + '\n' + '\t')

    def get_site_info(self):
        try:
            if os.path.exists(self.setup_file):
                df = pd.read_excel(self.setup_file, sheet_name='Test info', names=['item', 'value'], index_col=0, dtype=str,
                           keep_default_na=False, usecols=[0, 1], skiprows=[1, 12, 15, 18, 19, 21, 22, 23, 24])
                site = df['value']['TEST_FACILITY']
                self.data.pro_info_zh.update({'site': site.upper()})
            else:
                self.data.pro_info_zh.update({'site': 'ZH'})
        except:
            self.data.pro_info_zh.update({'site': 'ZH'})
        self.root.title('User Login_' + self.data.pro_info_zh['site'])

    def check_user_info(self, event=None):
        if self.data.pro_info_zh['site'] == 'ZH':
            try:
                self.data.fusion_a = ActiveTestApi()                      # connect to fusion database for later use
            except:
                msg.showwarning('Warning', 'ActiveTest 数据库系统连接失败/connect database is failure')
                return
            if self.user_name.get() == '' or self.password.get() == '' or self.station_num.get() == '':
                print('Some input is blank, Please check logging info')
                return
            access_id = None
            try:
                access_id = self.data.fusion_a.check_user(self.user_name.get(), self.password.get())
            except:
                self.exit_gui = True
                print('User info is invalid, please check')
            if access_id is not None:
                if access_id in [1, 2, 5]:  # engineer authority
                    self.data.pwd_gui = "MOLEX"
                else:
                    self.data.pwd_gui = "operator"
                self.exit_gui = False

            if os.path.exists(self.setup_file):                           # 如果本地存在配置文件，则使用本地路径，否则使用服务器路径
                self.data.folder_path = os.getcwd()
            else:
                self.data.folder_path = r'\\zh-mfs-srv\\Active\\ACPDU\\' + self.station_num.get()
        else:                                                 # self.data.pro_info_zh['site'] == 'GUAD':
            if self.user_name.get().lower() == 'admin':
                self.data.pwd_gui = "MOLEX"
            else:
                if not self.check_user_GUAD():                # connect to RunCard, and check register name
                    return
                self.data.pwd_gui = "operator"
            self.exit_gui = False
            self.data.folder_path = os.getcwd()
        self.data.pro_info_zh.update({'operator': self.string_format(self.user_name.get()),
                                      'station': self.string_format(self.station_num.get()),
                                      'resource': self.string_format(self.resource.get())})
        if not self.exit_gui:
            if self.get_com_config():
                self.root.destroy()

    #### GUAD functions ####
    def check_user_GUAD(self, event=None):
        # user = self.user_name.get()
        myworkbook = openpyxl.load_workbook(self.setup_file)
        myworksheet = myworkbook.get_sheet_by_name('Test info')
        for cell in myworksheet['A']:
            if cell.value == "OPERATOR":
                myworksheet.cell(row=cell.row, column=2).value = self.user_name.get()
                break
        myworkbook.save(self.setup_file)
        myRunCard = RunCard()
        if not myRunCard.connect():
            msg.showerror(title="Error!", message="RunCard is disconnected! Please check network connection or address.")
            return False
        if not myRunCard.checkUserStatus():
            msg.showerror(title="Error!", message="Operator is not registered in RunCard. Please check.")
            return False
        return True

    def quit(self):
        self.exit_gui = True
        self.root.destroy()
