#!/usr/bin/python
# -*- coding: UTF-8 -*-
# Author:Shengqiao  Time: 2022/5/13


import tkinter as tk


# 弹窗
class MyDialog(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title('Special Access')
        self.geometry('200x100+1000+650')
        self.userinfo = None
        self.setup_UI()

    def setup_UI(self):
        row1 = tk.Frame(self)
        row1.pack(fill="x")
        tk.Label(row1, text='Username：', width=10).pack(side=tk.LEFT)
        self.name = tk.StringVar()
        tk.Entry(row1, textvariable=self.name, width=20).pack(side=tk.LEFT)

        # 第二行
        row2 = tk.Frame(self)
        row2.pack(fill="x", ipadx=1, ipady=1)
        tk.Label(row2, text='Password：', width=10).pack(side=tk.LEFT)
        self.age = tk.StringVar()
        tk.Entry(row2, textvariable=self.age, width=20, show='*').pack(side=tk.LEFT)

        # 第三行
        row3 = tk.Frame(self)
        row3.pack(fill="x")
        tk.Button(row3, text="Cancel", command=self.cancel, width=6).pack(side=tk.RIGHT)
        tk.Button(row3, text="OK", command=self.ok, width=6).pack(side=tk.RIGHT)

    def ok(self):
        self.userinfo = [self.name.get(), self.age.get()]  # 设置数据
        self.destroy()  # 销毁窗口

    def cancel(self):
        self.userinfo = None  # 空！
        self.destroy()

