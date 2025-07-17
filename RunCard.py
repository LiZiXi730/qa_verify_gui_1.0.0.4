# for python 3
# using pip install suds-py3
from suds.client import Client
import pandas as pd
import os


#URL = "http://gumvldarun04.molex.com/runcard/soap?wsdl"

class RunCard:

    def __init__(self):
        production_file = os.getcwd() + '\\config file\\' + 'production setting qaverify.xlsx'
        df = pd.read_excel(production_file, sheet_name='Test info', names=['item', 'value'], index_col=0, dtype=str,
                           keep_default_na=False, usecols=[0, 1], skiprows=[1, 12, 15, 18, 19, 21, 22, 23, 24])
        self.URL = df['value']['GUAD RunCard Server']
        print('RunCard URL is: ', self.URL)
        self.username = df['value']['OPERATOR']


    def connect(self):
        #global code_list
        #code_list = ["A704-00", "A704-01", "A704-02"]
        try:
            self.runcard = Client(self.URL)
            print('RunCard is connected.')
            return True
        except Exception as e:
            print(e)
            return False
    # SOAP is still an HTTP request, which is stateless. Each request will start a whole new connection, re-auth, etc.
    # Browsers kind of short circuit that with cookies, but SOAP doesn't.
    # So, you don't need to close the connection, it's already closed by the time suds returns your data back to you.


    def get_unit_status(self, SN):
        response = self.runcard.service.getUnitStatus(SN)
        # print("RESPONSE: ", response)
        if response['error'] == 0:
            lotnum = response[0]['lotnum']
            workorder = response[0]['workorder']
            partnum = response[0]['partnum']
            status = response[0]['status']
            seqnum = response[0]['seqnum']
            opcode = response[0]['opcode']
            result = [lotnum, workorder, partnum, status, seqnum, opcode]
            return result
        else:
            return False


    def get_partnum(self, SN):
        response = self.runcard.service.getUnitStatus(SN)
        # print("RESPONSE: ", response)
        if response['error'] == 0:
            partnum = response[0]['partnum']
            return partnum
        else:
            return False


    def get_lotnum(self, SN):
        response = self.runcard.service.getUnitStatus(SN)
        # print("RESPONSE: ", response)
        if response['error'] == 0:
            lotnum = response[0]['lotnum']
            return lotnum
        else:
            return False


    def get_workorder(self, SN):
        response = self.runcard.service.getUnitStatus(SN)
        # print("RESPONSE: ", response)
        if response['error'] == 0:
            wo = response[0]['workorder']
            return wo
        else:
            return False


    def get_opcode(self, SN):
        response = self.runcard.service.getUnitStatus(SN)
        # print("RESPONSE: ", response)
        if response['error'] == 0:
            opcode = response[0]['opcode']
            return opcode
        else:
            return False


    def get_seqnum(self, SN):
        response = self.runcard.service.getUnitStatus(SN)
        # print("RESPONSE: ", response)
        if response['error'] == 0:
            seqnum = response[0]['seqnum']
            return seqnum
        else:
            return False


    def get_status(self, SN):
        response = self.runcard.service.getUnitStatus(SN)
        # print("RESPONSE: ", response)
        if response['error'] == 0:
            status = response[0]['status']
            return status
        else:
            return False


    def checkUserStatus(self):
        response = self.runcard.service.checkUserStatus(self.username)
        if response['error'] == 0:
            print('Username %s is registered.' % self.username)
            return True
        else:
            print('Username %s is NOT registered.' % self.username)
            return False


    def transactUnit(self, SN, action, defect_code=None): #username has to be registered in the RunCard, otherwise it will show error.
        work_order = self.get_workorder(SN)
        step = self.get_seqnum(SN)
        opcode = self.get_opcode(SN)
        if action in ['start', 'advance', 'release']:
            transact_info = {"username": self.username, "transaction": action, "workorder": work_order, "serial": SN, "seqnum": step, "opcode": opcode}
        elif action in ['scrap']:
            transact_info = {"username": self.username, "transaction": "scrap", "workorder": work_order, "serial": SN,
                             "seqnum": step, "opcode": opcode, "warehousebin": "SCRAP", "warehouseloc": "SCRAP", "defect_code": defect_code}
        elif action in ['update', 'hold']:
            transact_info = {"username": self.username, "transaction": action, "workorder": work_order, "serial": SN, "seqnum": step, "opcode": opcode, "defect_code": defect_code}
        inputData = ''
        inputBOM = ''
        result = self.runcard.service.transactUnit(transact_info, inputData, inputBOM)
        print(result['msg'])
        if result['error'] == 0:
            return True
        else:
            return False


    def start_test(self, SN):
        action = 'start'
        if self.transactUnit(SN, action):
            return True
        else:
            return False


    def pass_test(self, SN):
        action = 'advance'
        if self.transactUnit(SN, action):
            return True
        else:
            return False


    def hold_after_test(self, SN, defect_code):
        error_counts = 0
        action = 'hold'
        print('Defect code is: ', defect_code[0])
        if not self.transactUnit(SN, action, defect_code[0]):
            error_counts += 1
        if len(defect_code) > 1:
            action ='update'
            for code in defect_code[1:]:
                print('Defect code is: ', code)
                if not self.transactUnit(SN, action, defect_code):
                    error_counts += 1
        # print('Total error count is: ', error_counts)
        if error_counts == 0:
            return True
        else:
            return False


    def release_after_hold(self, SN):
        action = 'release'
        if self.transactUnit(SN, action):
            return True
        else:
            return False


    def scrap_after_test(self, SN, defect_code):
        error_counts = 0
        action = 'scrap'
        print('Defect code is: ', defect_code[0])
        if not self.transactUnit(SN, action, defect_code[0]):
            error_counts += 1
        if len(defect_code) > 1:
            action ='update'
            for code in defect_code[1:]:
                print('Defect code is: ', code)
                if not self.transactUnit(SN, action, defect_code):
                    error_counts += 1
        # print('Total error count is: ', error_counts)
        if error_counts == 0:
            return True
        else:
            return False


'''
def main():
    URL = "http://gumvldarun04.molex.com/runcard/soap?wsdl"
    SN = 'G22192Q0002'

    myRunCard = RunCard()
    myRunCard.connect()
    opcode = myRunCard.get_opcode(SN)
    print('OP code is: ', opcode)
    date = myRunCard.get_unit_status(SN)
    print(date)
    code_list = ["A704-00", "A704-01", "A704-02", "A704-03"]
    #username = "jjiang"
    myRunCard = RunCard()
    myRunCard.connect()
    myRunCard.checkUserStatus()
    lot_num = myRunCard.get_lotnum(SN)
    print('Lot number is: ', lot_num)
    workorder = myRunCard.get_workorder(SN)
    print('Work order is: ', workorder)
    opcode = myRunCard.get_opcode(SN)
    print('OP code is: ', opcode)
    seqnum = myRunCard.get_seqnum(SN)
    print('Step is: ', seqnum)
    status = myRunCard.get_status(SN)
    print('Status is: ', status)

    #global code_list
    status = myRunCard.hold_after_test(SN, code_list)
    # status = myRunCard.release_after_hold(SN)
    # status = myRunCard.pass_test(SN)
    # status = myRunCard.start_test(SN)
    # status = myRunCard.scrap_after_test(SN, code_list)

    if status:
        print(status, 'Passed...')
    else:
        print(status, 'Failed...')

if __name__ == '__main__':
    # pass
    main()
'''

