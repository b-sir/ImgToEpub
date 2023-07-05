#! python3

import os,sys
import shutil
import zipfile

CurrentDir = os.path.abspath(os.path.dirname(__file__)).replace('\\', '/')


def saferemove(path):
    if path and os.path.exists(path):
        if os.path.isdir(path):
            # shutil.rmtree(path, ignore_errors=True)
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
        else:
            print("Unknown file type: " + path)


def writeFile(path, str):
    fp = open(path, 'w', encoding='UTF-8')
    fp.write(str)
    fp.close()

def readFile(path):
    fp = open(path, 'r', encoding='UTF-8')
    str = fp.read()
    fp.close()
    return str

def zipDir(dirpath,outFullName):
    zip = zipfile.ZipFile(outFullName,"w",zipfile.ZIP_DEFLATED)
    for path,dirnames,filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath,'')

        for filename in filenames:
            zip.write(os.path.join(path,filename),os.path.join(fpath,filename))
    zip.close()

def unzipToDir(filePath, outPath, newDirName):
    os.chdir(outPath)
    if newDirName != None:
        saferemove(os.path.join(outPath, newDirName))
        os.mkdir(newDirName)
    os.chdir(os.path.join(outPath, newDirName))
    zip = zipfile.ZipFile(filePath)
    zip.extractall()
    zip.close()