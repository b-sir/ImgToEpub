#!/usr/bin/python3
import os,sys
import Util
from shutil import copyfile, rmtree

from pathlib import Path
from borb.pdf import Document
from borb.pdf import Page
from borb.pdf import SingleColumnLayout
from borb.pdf import Paragraph
from borb.pdf import PDF
from borb.pdf import Image as PdfImage
from decimal import Decimal

from PIL import Image

#需要 pip3 install borb -i https://pypi.tuna.tsinghua.edu.cn/simple
#需要 pip3 install Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple

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

def reGenTempFolder():
    if not os.path.exists(TgtPath):
        os.mkdir(TgtPath)

    #临时目录
    if not os.path.exists(TmpPath):
        os.mkdir(TmpPath)

    # OEBPS目录
    if not os.path.exists(os.path.join(TmpPath, "OEBPS")):
        os.mkdir(os.path.join(TmpPath, "OEBPS"))

    # OEBPS/image目录
    if not os.path.exists(ImgFolder):
        os.mkdir(ImgFolder)

def genOEBPSTextFile(chapterID, subID, imageName, bookTitle, data):
    data["newImagefiles"].append(imageName)

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
    
    # create an empty Document
    pdf = Document()

    for data in srcData:
        chapterID = data["chapterID"]

        for imageItem in data["newImagefiles"]:
            #pFormat = imageItem[-4:]
            #pFormatDesc = "image/png" if pFormat == ".png" else "image/jpeg"
            fullPath = os.path.join(ImgFolder, imageItem)
            img0 = Image.open(fullPath)
            w, h = img0.size

            # [595 842]的两倍大
            pageW = 1190
            pageH = 1190 * h / w
            # add an empty Page
            page = Page(
                width=Decimal(pageW+10),
                height=Decimal(pageH+10),
            )
            pdf.add_page(page)

            layout = SingleColumnLayout(page, Decimal(0), Decimal(0))
            img: PdfImage = PdfImage(
                Path(fullPath),
                width=Decimal(pageW),
                height=Decimal(pageH),
            )
            layout.add(img)

    print("\n压制中... => "+outFilename)
    with open(Path(os.path.join(TgtPath, outFilename)), "wb") as pdf_file_handle:
        PDF.dumps(pdf_file_handle, pdf)

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
    print("路径错误！请保证路径中没有空格")
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
        genBook(subData, title, title+".pdf")

        st = ed
        ed = min(st + MAX_CHAPTER, total)
else:
    genBook(SrcData, BOOK_TITLE, BOOK_TITLE+".pdf")

Util.saferemove(TmpPath)
if RemoveSrcPath:
    Util.saferemove(SrcPath)

