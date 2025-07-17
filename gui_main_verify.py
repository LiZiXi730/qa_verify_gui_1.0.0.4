'''
9/18/2019 Ye Wang
this this the gui for eng/cal purpose, this gui has access to modify setting of the module;
gui_main_test is test gui, it can only read and do tests, couldn't access any module internal info,
nor change module settings.
'''


import tkinter
import logging
import signal
from tkinter import ttk, VERTICAL, HORIZONTAL, N, S, E, W, WORD
from gui_ui_dutselect import DutSelectUi
from gui_cache_data import Data
from gui_ui_qa_verify import QA_Verify
from gui_ui_station_info import Station


def main():
    logging.basicConfig(level=logging.INFO)

    station_root = tkinter.Tk()
    Obj_station.on_create(station_root, Obj_Data)
    station_root.mainloop()
    if Obj_station.exit_gui:
        return False

    root = tkinter.Tk()
    if Obj_Data.pro_info_zh['site'] == 'GUAD':
        size = '1000x800+200+20'
    else:
        size = '850x760+200+20'           # width：850， height:770, posX:200, posY: 20
    root.geometry(size)
    root.resizable(True, True)
    app = GUI_Platform(root)
    app.root.mainloop()


class GUI_Platform:
    def __init__(self, root):
        self.root = root
        gui_ver = 'ver1.0.0.4'
        root.title('400G QA Verify GUI_' + gui_ver + '_' + Obj_Data.pro_info_zh['site'])
        #root.columnconfigure(0, weight=1)
        #root.rowconfigure(0, weight=1)
        root.resizable(False, False)
        Obj_Data.version = gui_ver

        dut_select_frame = ttk.Labelframe(root, text="DUT")
        dut_select_frame.rowconfigure(0, weight=0)
        dut_select_frame.grid(column=0, row=0, padx=8, pady=4, sticky=tkinter.W)
        '''
        Label1 = ttk.Labelframe(root, text="Rev: 1.0.0.1")
        dut_select_frame.rowconfigure(0, weight=0)
        Label1.grid(column=15, row=0, padx=8, pady=4, sticky=tkinter.E)
        '''
        qa_verify_frame = ttk.Labelframe(root, text='QA Verify')
        qa_verify_frame.rowconfigure(0, weight=0)
        qa_verify_frame.grid(column=0, row=1, padx=8, pady=4, sticky=tkinter.NW)

        Obj_DutSelectUi.on_create(dut_select_frame, Obj_Data)
        Obj_qa_verify.on_create(qa_verify_frame, Obj_Data, Obj_DutSelectUi, root)

        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.root.bind('<Control-q>', self.quit)
        signal.signal(signal.SIGINT, self.quit)

    def quit(self):
        self.root.destroy()


Obj_Data = Data()              # declare or define Device information or other parameters
Obj_station = Station()
Obj_DutSelectUi = DutSelectUi()
Obj_qa_verify = QA_Verify()

if __name__ == '__main__':
    main()

