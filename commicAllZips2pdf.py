#!/usr/bin/python3
import os,sys
import Util
from shutil import copyfile, rmtree

CurrentDir = os.path.abspath(os.path.dirname(__file__))
SrcPath = os.path.join(CurrentDir, "Resources")

def walk(folder):
    fs = os.listdir(folder)
    for fl in fs:
        tmp_path = os.path.join(folder, fl)
        if not os.path.isdir(tmp_path):
            pFormat = fl[-4:]
            if pFormat == ".zip":
                print("python ./commicImg2pdf.py \"" + tmp_path + "\"")
                os.system("python ./commicImg2pdf.py \"" + tmp_path + "\"")



print("将1个目录下所有zip文件转为pdf")
print("请输入所在目录 路径，如：")
print(SrcPath)
SrcPath = input("请输入(或拖入)路径:")

if SrcPath.startswith("\"") and SrcPath.endswith("\""):
    SrcPath = SrcPath[1:len(SrcPath)-1]

if not os.path.exists(SrcPath):
    print(SrcPath)
    print("路径错误！请保证路径中没有特殊字符")
    pause = input("按任意键关闭")
    sys.exit()

walk(SrcPath)