import os
from shutil import copyfile
from PIL import Image

#需要 pip3 install Pillow
#需要 

CurrentDir = os.path.abspath(os.path.dirname(__file__))
SrcPath = os.path.join(CurrentDir, "Resources")
TgtPath = os.path.join(CurrentDir, "Output")

ReadModeRight = True #设置切割图片的阅读顺序 True为日漫右向左读

if not os.path.exists(TgtPath):
    os.mkdir(TgtPath)

def walk(folder, rootData, chaperData):
    fs = os.listdir(folder)
    for fl in fs:
        tmp_path = os.path.join(folder, fl)
        if not os.path.isdir(tmp_path):
            pFormat = fl[-4:]
            if pFormat == ".png" or pFormat == ".jpg":
                chaperData.append(tmp_path)
        else:
            newChapter = {}
            newChapter["name"] = fl
            newChapter["files"] = []
            rootData.append(newChapter)
            walk(tmp_path, rootData, newChapter["files"])

srcData = []
rootFiles = []
walk(SrcPath, srcData, rootFiles)

TmpPath = os.path.join(TgtPath, "Temp")
if not os.path.exists(TmpPath):
    os.mkdir(TmpPath)

print("----------开始处理原始图片，并迁移到临时目录-----------")
for data in srcData:
    tmpFolder = os.path.join(TmpPath, data["name"])
    if not os.path.exists(tmpFolder): #创建对应章节的临时文件夹
        os.mkdir(tmpFolder)
    
    print("处理章节："+data["name"])

    index = 1
    for file in data["files"]:
        img0 = Image.open(file)
        w, h = img0.size
        if w > h: #宽>高 需要切隔为两张图片
            box1 = (w-w//2, 0, w, h)
            box2 = (0, 0, w//2, h)
            if not ReadModeRight:
                box1 = (0, 0, w//2, h)
                box2 = (w-w//2, 0, w, h)
            newImg1 = img0.crop(box1)
            newImg2 = img0.crop(box2)

            newImg1.save(os.path.join(tmpFolder, ("%04d.png"%index)), "png")
            index = index + 1
            newImg2.save(os.path.join(tmpFolder, ("%04d.png"%index)), "png")
            index = index + 1
        else:
            pFormat = file[-4:]
            copyfile(file, os.path.join(tmpFolder, ("%04d"%index) + pFormat))
            index = index + 1