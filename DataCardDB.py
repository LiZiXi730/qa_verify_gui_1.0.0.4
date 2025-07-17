import pymysql
from datetime import datetime


class DataCard:
    def __init__(self, partSN, wo_opcode):
        self.partSN = partSN
        self.wo_opcode = wo_opcode

    def fetch_test_records(self):
        db = pymysql.connect(host='gumvldacrd01.molex.com', user='ODBCREAD', password='ODBCREAD',
                             database='datacard')  # 打开datacard数据库连接
        db_rn = pymysql.connect(host='gumvldarun01.molex.com', user='ODBCREAD', password='ODBCREAD',
                                database='runcard')  # 打开runcard数据库连接
        cursor = db.cursor()  # 使用 cursor() 方法创建一个游标对象 cursor
        cursor_rn = db_rn.cursor()
        while True:
            sql_str = "SELECT lot_record.start_date,lot_record.end_date,part_record.part_id,lot_record.part_num," \
                      "lot_record.wo_id,lot_record.tester_id,lot_record.test_temp,part_record.result " \
                      "FROM lot_record INNER JOIN part_record ON lot_record.lot_i = part_record.lot_i " \
                      "WHERE part_record.part_id ='%s' AND lot_record.wo_opcode ='%s' " \
                      "ORDER BY lot_record.end_date ASC" % (self.partSN, self.wo_opcode)
            cursor.execute(sql_str)  # 使用 execute()  方法执行 SQL 查询
            data = cursor.fetchall()  # 使用 fetchall() 方法获取所有返回数据.
            if len(data):
                break
            # 如果获取的数据长度为0，则使用此New SN 去runcard查询 Old SN， 然后使用Old SN去查询测试数据
            sql_str = "SELECT inv_serial FROM wo_consumption WHERE serial = '%s'" % self.partSN
            cursor_rn.execute(sql_str)
            data_rn = cursor_rn.fetchall()
            if len(data_rn):
                self.partSN = data_rn[0][0]
            else:
                break
        db.close()      # 关闭datacard数据库连接
        db_rn.close()   # 关闭db_rn数据库连接
        return data

    def fetch_old_serial(self, partSN):
        db = pymysql.connect(host='gumvldarun01.molex.com', user='ODBCREAD', password='ODBCREAD',
                            database='runcard')  # 打开数据库连接
        cursor = db.cursor()  # 使用 cursor() 方法创建一个游标对象 cursor
        sql_str = "SELECT inv_serial FROM wo_consumption WHERE serial = '%s'" % (partSN)
        cursor.execute(sql_str)  # 使用 execute()  方法执行 SQL 查询
        data = cursor.fetchall()  # 使用 fetchall() 方法获取所有返回数据.
        db.close()  # 关闭数据库连接
        return data

    def get_3T_last_record(self):
        data_record = self.fetch_test_records()
        # for code in data_record:
            # print(code)
        default_enddate = datetime.strptime('2017-04-23 01:12:00', '%Y-%m-%d %H:%M:%S')  # set default datetime
        test_result = {'RT': [False, default_enddate], 'LT': [False, default_enddate],
                       'HT': [False, default_enddate]}  # 初始化3个温度Test_Result的Value, default_enddate
        # result = []
        for tempid in ['45', '0', '75']:
            if tempid == '0':
                tenvid = 'LT'
            elif tempid == '75':
                tenvid = 'HT'
            else:
                tenvid = 'RT'
            tenvid_datalist = []
            for mfg_record in data_record:
                if mfg_record[6] == tempid:
                    tenvid_datalist.append(mfg_record)
            if tenvid_datalist:  # 表示tenvid_datalist 为非空列表
                last_listno = 0
                last_enddate = tenvid_datalist[last_listno][1]  # 第一条记录的enddate
                for j in range(len(tenvid_datalist)):  # 搜寻同一温度下所有测试记录的最新记录
                    enddate = tenvid_datalist[j][1]
                    if last_enddate < enddate:
                        last_enddate = enddate
                        last_listno = j
                if tenvid_datalist[last_listno][7] == 1:
                    test_result[tenvid][0] = True
                test_result[tenvid][1] = tenvid_datalist[last_listno][1]  # 将该温度最新记录的enddate时间赋值给test_result下该温度的测试时间
        return test_result

def main():
    SN = 'G23320066'
    # SN = 'G23023Q0027'
    # SN = 'Z23061M2Q'
    opcode = 'T806'
    myDataCard = DataCard(SN, opcode)
    # result = myDataCard.fetch_old_serial('Z23061M2Q')
    # print(result)

    test_result = myDataCard.get_3T_last_record()
    test_type = 'All Channel'
    result = check_3T_result(test_result, test_type)
    print(test_result)
    print(result)


def check_3T_result(test_result, test_type):  # check 3T result sub function
    if test_result['RT'][0] and test_result['LT'][0] and test_result['HT'][0] and \
            (test_result['RT'][1] < test_result['LT'][1]) and (test_result['RT'][1] < test_result['HT'][1]):
        print('Pass: ' + test_type + ' 3T test result check passed. ')
        # self.text_info.insert(tkinter.END, 'Pass: ' + test_type + ' 3T test result check passed. \n')
        # self.text_frame.update()
        return True
    else:
        print('Fail: ' + test_type + ' 3T test result check failed. ')
        # self.text_info.insert(tkinter.END, 'Fail: ' + test_type + ' 3T test result check failed. \n')
        # self.text_frame.update()
        # self.fail_code.append('QA03')
        return False


if __name__ == '__main__':
    main()
