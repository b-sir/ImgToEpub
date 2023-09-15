#!/usr/bin/python3
import Util
from functools import cache
from genericpath import isdir
import os,sys
import uuid
from shutil import copyfile, rmtree
from typing import Text
from PIL import Image
import zipfile

#需要 pip3 install Pillow

#################-----Config-----###############
JPEG_QUILTY = 90      #图片压缩质量 1~100
MAX_CHAPTER = 5       #文件夹数量超过这个 会生成多个epub文件
SpliteImage = True    #切割宽比高大的图片为两张图片
ReadModeRight = True  #设置切割图片的阅读顺序 True为日漫右向左读(决定切割图片后左右哪个先)
#################-----Config-----###############

BOOK_TITLE = "书名"   #

CurrentDir = os.path.abspath(os.path.dirname(__file__))
SrcPath = os.path.join(CurrentDir, "Resources")
TgtPath = os.path.join(CurrentDir, "Output")

TmpPath = os.path.join(TgtPath, "Temp")
TextFolder = os.path.join(TmpPath, "OEBPS", "text")
ImgFolder = os.path.join(TmpPath, "OEBPS", "image")

def walk(folder, rootData, chaperData):
    fs = os.listdir(folder)
    for fl in fs:
        tmp_path = os.path.join(folder, fl)
        if not os.path.isdir(tmp_path):
            pFormat = fl[-4:]
            if pFormat == ".png" or pFormat == ".jpg":
                chaperData.append(tmp_path)
            else:
                print("异常文件 "+fl)
        else:
            newChapter = {}
            newChapter["name"] = fl
            newChapter["files"] = []
            newChapter["newTextfiles"] = []
            newChapter["newImagefiles"] = []
            rootData.append(newChapter)
            walk(tmp_path, rootData, newChapter["files"])
    chaperData.sort()

def walkAndGenBaseData(SrcPath):
    # 1.遍历目录，收集所有信息
    SrcData = []
    rootChapter = {}
    rootChapter["name"] = os.path.basename(SrcPath)
    rootChapter["files"] = []
    rootChapter["newTextfiles"] = []
    rootChapter["newImagefiles"] = []
    SrcData.append(rootChapter)
    walk(SrcPath, SrcData, rootChapter["files"])

    # 过滤空章节：通常是父文件夹或空文件夹
    newSrcData = []
    for iData in SrcData:
        if len(iData["files"]) > 0:
            newSrcData.append(iData)

    return SrcData

def PrintSrcData(srcData):
    print("\n----------------- 结构预览 --------------------")
    for iData in srcData:
        print("----- %s -----"%iData["name"])
        for fileName in iData["files"]:
            print(fileName)

textTempStr = Util.readFile(os.path.join(CurrentDir, "libs", "OEBPS", "text", "p_temp.xhtml"))
def genOEBPSTextFile(chapterID, subID, imageName, bookTitle, data):
    newTextStr = textTempStr.replace("###BOOK_TITLE###", bookTitle, 1)
    newTextStr = newTextStr.replace("###IMAGE_FILE###", imageName, 1)
    fileName = "p%03d_%05d"%(chapterID,subID)
    Util.writeFile(os.path.join(TextFolder, fileName+".xhtml"), newTextStr)

    data["newTextfiles"].append(fileName)
    data["newImagefiles"].append(imageName)

### 文件准备完毕，打zip包
def zipToFile(zipFile, folder, root):
    preLen = len(root)
    fs = os.listdir(folder)
    # 必须先处理文件、再处理文件夹
    for fl in fs:
        tmp_path = os.path.join(folder, fl)
        if not os.path.isdir(tmp_path):
            arcname = tmp_path[preLen:].strip(os.path.sep)
            zipFile.write(tmp_path, arcname)
    for fl in fs:
         tmp_path = os.path.join(folder, fl)
         if os.path.isdir(tmp_path):
            zipToFile(zipFile, tmp_path, root)

def reGenTempFolder():
    if not os.path.exists(TgtPath):
        os.mkdir(TgtPath)

    #临时目录
    if not os.path.exists(TmpPath):
        os.mkdir(TmpPath)

    # META-INF目录
    if not os.path.exists(os.path.join(TmpPath, "META-INF")):
        os.mkdir(os.path.join(TmpPath, "META-INF"))

    # OEBPS目录
    if not os.path.exists(os.path.join(TmpPath, "OEBPS")):
        os.mkdir(os.path.join(TmpPath, "OEBPS"))

    # OEBPS/image目录
    if not os.path.exists(ImgFolder):
        os.mkdir(ImgFolder)

    # OEBPS/style目录
    if not os.path.exists(os.path.join(TmpPath, "OEBPS", "style")):
        os.mkdir(os.path.join(TmpPath, "OEBPS", "style"))

    # OEBPS/text目录
    if not os.path.exists(TextFolder):
        os.mkdir(TextFolder)


def genBook(srcData, bookTitle, outFilename):
    if os.path.exists(os.path.join(TgtPath, outFilename)):
        print("跳过：已存在电子书 "+outFilename)
        return

    if os.path.exists(TmpPath):
        rmtree(TmpPath)
    reGenTempFolder()

    print("开始生成电子书："+bookTitle)
    chapterID = 0
    for data in srcData:
        print("生成章节："+data["name"])
        chapterID = chapterID + 1
        data["chapterID"] = chapterID
        subID = 1
        subLens = len(data["files"])

        for file in data["files"]:
            #print("\r[%d/%d]  %s"%(subID, subLens, os.path.basename(file)), end="", flush=True)
            print("[%4d/%4d]  %s"%(subID, subLens, os.path.basename(file)) )
            try:
                img0 = Image.open(file)
                w, h = img0.size
                if SpliteImage and w > h: #宽>高 需要切隔为两张图片
                    box1 = (w-w//2, 0, w, h)
                    box2 = (0, 0, w//2, h)
                    if not ReadModeRight:
                        box1 = (0, 0, w//2, h)
                        box2 = (w-w//2, 0, w, h)
                    newImg1 = img0.crop(box1).convert("RGB")
                    newImg2 = img0.crop(box2).convert("RGB")

                    name1 = "i%03d_%05d.jpg"%(chapterID,subID)
                    newImg1.save(os.path.join(ImgFolder, name1), "jpeg", quality=JPEG_QUILTY)
                    genOEBPSTextFile(chapterID,subID,name1,bookTitle,data)
                    subID = subID + 1
                    name2 = "i%03d_%05d.jpg"%(chapterID,subID)
                    newImg2.save(os.path.join(ImgFolder, name2 ), "jpeg", quality=90)
                    genOEBPSTextFile(chapterID,subID,name2,bookTitle,data)
                    subID = subID + 1

                    subLens = subLens + 1
                else:
                    pFormat = file[-4:]
                    name = "i%03d_%05d%s"%(chapterID,subID,pFormat)
                    copyfile(file, os.path.join(ImgFolder, name))
                    genOEBPSTextFile(chapterID,subID,name,bookTitle,data)
                    subID = subID + 1
            except KeyboardInterrupt: #手动Ctrl+C退出
                sys.exit()
            except:
                print("\n\n文件异常 无法处理 跳过："+file+"\n\n")

    #封面图片处理
    coverSrcFile = os.path.join(ImgFolder, srcData[0]["newImagefiles"][0])
    coverFormat = coverSrcFile[-4:]
    coverFileName = "cover"+coverFormat 
    copyfile(coverSrcFile, os.path.join(ImgFolder, coverFileName))

    #print("图片处理结束，请打开")
    #print("https://github.com/wing-kai/epub-manga-creator")
    #print("https://wing-kai.github.io/epub-manga-creator/")

    # mimetype固定文件
    copyfile(os.path.join(CurrentDir, "libs", "mimetype"), os.path.join(TmpPath, "mimetype"))

    # 固定内容 指向standard.opf
    copyfile(os.path.join(CurrentDir, "libs", "META-INF", "container.xml"), os.path.join(TmpPath, "META-INF", "container.xml"))

    # css固定文件(对漫画不重要)
    copyfile(os.path.join(CurrentDir, "libs", "OEBPS", "style", "fixed-layout-jp.css"), os.path.join(TmpPath, "OEBPS", "style", "fixed-layout-jp.css"))


    # 生成opf文件内容
    coverFormatDesc = "image/png" if coverFormat == ".png" else "image/jpeg"
    itemsStr = '<item id="cover" href="image/%s" media-type="%s" properties="cover-image"></item>\n'%(coverFileName, coverFormatDesc)
    itemsStr += '<item id="p_cover" href="text/p_cover.xhtml" media-type="application/xhtml+xml" properties="svg" fallback="cover"></item>\n'
    itemRefStr = ""
    dictStr = ""

    isInLeft = False
    for data in srcData:
        chapterID = data["chapterID"]

        dictStr = dictStr + '<li><a href="text/p%03d_00001.xhtml">%s</a></li>\n'%(chapterID, data["name"])

        for imageItem in data["newImagefiles"]:
            pFormat = imageItem[-4:]
            pFormatDesc = "image/png" if pFormat == ".png" else "image/jpeg"
            
            itemsStr = itemsStr + '<item id="%s" href="image/%s" media-type="%s"></item>\n'%(imageItem[:-4], imageItem, pFormatDesc)

        for i in range(len(data["newTextfiles"])):
            textItem = data["newTextfiles"][i]
            imageItem = data["newImagefiles"][i]
            
            itemsStr = itemsStr + '<item id="%s" href="text/%s.xhtml" media-type="application/xhtml+xml" properties="svg" fallback="%s"></item>\n'%(textItem, textItem, imageItem[:-4])
            
            properties = "page-spread-left" if isInLeft else "page-spread-right"
            itemRefStr = itemRefStr + '<itemref linear="yes" idref="%s" properties="%s"></itemref>\n'%(textItem, properties)
            isInLeft = not isInLeft

    opfTempStr = Util.readFile(os.path.join(CurrentDir, "libs", "OEBPS", "standard.opf"))
    newOpfStr = opfTempStr.replace("###BOOK_TITLE###", bookTitle)
    newOpfStr = newOpfStr.replace("###BOOK_ID###", str(uuid.uuid1()))
    newOpfStr = newOpfStr.replace("###BOOK_ITEMS###", itemsStr)
    newOpfStr = newOpfStr.replace("###BOOK_ITEMREFS###", itemRefStr)

    Util.writeFile(os.path.join(TmpPath, "OEBPS", "standard.opf"), newOpfStr)


    # 生成 navigation-documents.xhtml 内容

    docTempStr = Util.readFile(os.path.join(CurrentDir, "libs", "OEBPS", "navigation-documents.xhtml"))
    newDocStr = docTempStr.replace("###BOOK_DICT###", dictStr)
    Util.writeFile(os.path.join(TmpPath, "OEBPS", "navigation-documents.xhtml"), newDocStr)


    print("\n压制中... => "+outFilename)
    bookFile = zipfile.ZipFile(os.path.join(TgtPath, outFilename), "w")
    zipToFile(bookFile, TmpPath, TmpPath)

    if os.path.exists(TmpPath):
        rmtree(TmpPath)

if len(sys.argv) == 2:
    SrcPath = sys.argv[1]
elif(len(sys.argv) <= 1):
    print("请输入图片所在最上层目录 路径，如：")
    print(SrcPath)
    SrcPath = input("请输入(或拖入)路径:")
else:
    print("参数错误！")
    pause = input("按任意键关闭")
    sys.exit()

if SrcPath.startswith("\"") and SrcPath.endswith("\""):
    SrcPath = SrcPath[1:len(SrcPath)-1]

if not os.path.exists(SrcPath):
    print(SrcPath)
    print("路径错误！请保证路径中没有特殊字符")
    pause = input("按任意键关闭")
    sys.exit()

RemoveSrcPath = False
#如果输入的是zip文件，解压缩
if os.path.isfile(SrcPath):
    baseName = os.path.basename(SrcPath)
    baseFolder = SrcPath[0:len(SrcPath)-len(baseName)-1]
    if baseName.endswith(".zip"):
        bName = baseName[0:len(baseName)-4]
        Util.unzipToDir(SrcPath, baseFolder, bName)
        SrcPath = os.path.join(baseFolder, bName)
        RemoveSrcPath = True
    else:
        print("路径错误！不支持的文件")
        pause = input("按任意键关闭")
        sys.exit()

TgtPath = os.path.join(SrcPath, "..")
TmpPath = os.path.join(TgtPath, "Temp")
TextFolder = os.path.join(TmpPath, "OEBPS", "text")
ImgFolder = os.path.join(TmpPath, "OEBPS", "image")

BOOK_TITLE = os.path.basename(SrcPath)
SrcData = walkAndGenBaseData(SrcPath)

PrintSrcData(SrcData)
print("\n请浏览和确认以上信息，主要确认文件排序是否正确")
if(len(sys.argv) <= 1):
    pause = input("确认正确后，输入任意内容继续：")

if (len(SrcData) > MAX_CHAPTER):
    total = len(SrcData)
    st = 0
    ed = 5

    while st < total:
        subData = SrcData[st:ed]
        title = "%s%d-%d"%(BOOK_TITLE, (st+1), ed)
        genBook(subData, title, title+".epub")

        st = ed
        ed = min(st + MAX_CHAPTER, total)
else:
    genBook(SrcData, BOOK_TITLE, BOOK_TITLE+".epub")

Util.saferemove(TmpPath)
if RemoveSrcPath:
    Util.saferemove(SrcPath)
