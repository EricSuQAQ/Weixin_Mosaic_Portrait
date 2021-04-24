import os
import PIL.Image
import numpy as np
from tkinter import *
from tkinter import filedialog
import itchat

def wechatLogin():
    itchat.login() #登录微信
    friends = itchat.get_friends(update=True) #截取好友名单
    base_folder = 'wechat' #建立名为wechat的文件夹
    folder = os.path.exists(base_folder)
    if folder == False:
        os.mkdir(base_folder)

    for item in friends:
        img = itchat.get_head_img(item['UserName'])

        # 使用用户昵称作为文件名
        path = os.path.join(base_folder, '{}.jpg'.format(item['NickName'].replace('/', '')))
        with open(path, 'wb') as f:
            f.write(img)
        print('{} input successful...'.format(item['NickName']))

#以上是微信导入头像步骤，现在头像已经全部保存在同根目录文件夹“wechat”之下


#将头像建立为库
def buildLib():
    imageLib = {}
    weightsLib = {}
    libos = os.getcwd() + '\wechat'
    picList = os.listdir(libos) #将同根目录下wechat文件夹所有图片导入picList中
    #print(picList)
    i = 0
    for each in picList:
        if (each[-4:].upper() == '.JPG'):
            path = os.path.join(libos, each)
            try:             
                im = PIL.Image.open(path).resize((40, 40), PIL.Image.ANTIALIAS) # 将lib中所有的图像的size都改成40*40
                q = im.convert('RGB')
                imageLib.setdefault(each,np.array(q))

                temp = np.array(im.convert('L').resize((8, 8), PIL.Image.ANTIALIAS)) #将RGB图像转换为灰度图.
                avg = temp.mean()
                weights = np.array([1 if temp[i, j] > avg else 0 for i in range(0,8) for j in range(0,8)]) # 8*8 
                weightsLib.setdefault(each,weights)
            except:
                print(each,"is not the correct format, it won't be used in lib")
                pass
    #print(imageLib)
    #print(weightsLib)
    print("成功建立图库")
    return imageLib,weightsLib #现已成功建立图库与权重库
    
def RGBMean(pic):
    Rmean = np.mean(pic[:, :, 0])
    Gmean = np.mean(pic[:, :, 1])
    Bmean = np.mean(pic[:, :, 2])
    val = np.array([Rmean, Gmean, Bmean]) # 在R,G,B中的数个平均值
    return val

def masaic(target):
    suffix = target[-3:].upper()
    if(suffix != 'JPG'):
        print("Error: you should pick an image with format 'JPG'.") #结尾必须是JPG格式
        return None

    im = PIL.Image.open(target)
    #print(im.mode)
    if(im.mode != 'RGB'):
        print("Error:you have to use RGB image as your target image.") #目标图像必须是RGB格式
        return None
    width, height = im.size
    print(width,height)

    newWidth = 4000 #Note : 新图像宽度，是可以修改的，但建议不小于4000(如果超过12000可能会卡成王八蛋但效果不错:3)
    newHeight = ((newWidth / width) * height // 40) * 40 # 由于图库中是40*40的图片，所以长和宽最好是40的倍数。
    picture = im.resize((int(newWidth), int(newHeight)), PIL.Image.ANTIALIAS)
    #print('width：%d,height：%d'%(picture.size[0],picture.size[1])) # 4000,2240 for skadi.jpg
    #picture.show()
    pictureArray = np.array(picture)

    imageLib,weightsLib = buildLib()
    for i in range(0,int(newWidth/40)):
        for j in range(0,int(newHeight/40)):
            box = pictureArray[j * 40:(j + 1) * 40, i * 40:(i + 1) * 40]
            boxMean = RGBMean(box)
            candidate = colorSimilarity(imageLib,boxMean) # 我们在库中得到了与方框颜色相似的图像候选数据.
            best = structureSimilarity(weightsLib,candidate,box.copy()) # 在候选中，选取最与图像结构形式的头像.
            pictureArray[j * 40:(j + 1) * 40, i * 40:(i + 1) * 40] = imageLib[best] #将该头像纳入大图位置中.
        print("still working...already finish: ", int(i*100/int(newWidth/40)), "%")
    newIm = PIL.Image.fromarray(pictureArray)
    newIm.show()
    newIm.save('mosaic.jpg') #大图已经被保存至mosaic.jpg
    print("Over, the mosaic image save in the path where target in named 'mosaic.jpg'.")
    return None

#第一次筛选时，颜色相似度前10名将晋级至到第二次筛选。
def colorSimilarity(imageLib,boxMean):
    candidate = {}
    for each in imageLib:
        euclideanDistance = np.linalg.norm((boxMean - RGBMean(imageLib[each])), ord=None, axis=None, keepdims=False) #计算库中每个图像到盒子的欧氏距离。
        candidate.setdefault(each,euclideanDistance)
    L = sorted(candidate.items(),key = lambda item:item[1],reverse = False) 
    Q = L[:10] # sort and pick top 10 to return, wait for second screening. 
    promotion = [] 
    for every in Q:
        promotion.append(every[0])
    return promotion

#第二次筛选，将前十名纳入结构筛选中,选取获胜者
def structureSimilarity(weightsLib,candidate,box):
    greyscaleBox = PIL.Image.fromarray(box).convert('L') # change the box into greyscale.
    temp = np.array(greyscaleBox.resize((8, 8), PIL.Image.ANTIALIAS))
    boxAvg = temp.mean()
    best = [None,65]
    boxWeights = np.array([1 if temp[i, j] > boxAvg else 0 for i in range(0,8) for j in range(0,8)]) # 8*8 
    count = 0
    for each in candidate:
        pick = weightsLib[each]
        hd = HammingDistance(boxWeights,pick)
        count += 1
        if(hd < best[1]):
            best = [each,hd]
    return best[0]

def HammingDistance(a,b): #汉明距离计算
    count = 0
    for i in range(0,64):
            if(a[i] != b[i]):
                count += 1
    return count
#------------------------- UI part ----------------------------
#这UI真的是丑的如同王八蛋_(:з」∠)_
def createWindows(): 
    getTarget = False
    root= Tk()
    root.wm_title('create Mosaic picture') 
    root.geometry('700x200') 
    
    
    Namelabel = Label(root)
    Namelabel['text'] = 'Combine the pictures in the specified folder into a giant mosaic picture'
    Namelabel['font'] = 14
    Namelabel['fg'] = 'black'   
    Namelabel.pack()


    def targetPick():
        target = filedialog.askopenfilename()
        print(target)
        #wechatLogin()
        masaic(target)
        Catlabel = Label(root)
        Catlabel['text'] = 'Already get the target!'
        Catlabel['font'] = 14
        Catlabel['fg'] = 'black'   
        Catlabel.pack()

    targetBtn = Button(root)
    targetBtn['text'] = 'Choose the target'
    targetBtn['font'] = 14
    targetBtn['fg'] = 'yellow'
    targetBtn['bg'] = 'green'
    targetBtn['padx'] = 15
    targetBtn['command'] = targetPick
    targetBtn.pack()

    noteLabel = Label(root)
    noteLabel['text'] = 'Note: you have to pick the file name which is end by .jpg - e.g. skadi.jpg'
    noteLabel['font'] = 14
    noteLabel['fg'] = 'blue'   
    noteLabel.pack()

    root.mainloop()
#------------------------- UI part ----------------------------


if __name__ == '__main__':
    createWindows()
    #buildLib()
    #masaic('skadi.jpg')
    os.system('pause')

