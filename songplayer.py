#this program will play mp3s based on the name and maybe do other things idk
#DSG playlist: https://www.youtube.com/playlist?list=UUG6QEHCBfWZOnv7UVxappyw
import pygame, winreg, os, pyaudio, urllib.request, threading, urllib3, json, pypresence, time
from bs4 import BeautifulSoup
from librosa import load
from pyperclip import paste
from youtube_search import YoutubeSearch
from youtubesearchpython import SearchVideos
from struct import pack
from pafy import new
from warnings import filterwarnings
from math import ceil
import requests
def getDarkMode():
    key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize")
    i=0
    while True:
        try:
            value = winreg.EnumValue(key,i)
            if value[0] == "AppsUseLightTheme":
                return value[1]
            i+=1
        except WindowsError as e:
            break
    return 1
def getAccentColor():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\DWM")
    i = 0
    while True:
        try:
            value = winreg.EnumValue(key, i)
            if value[0] == "AccentColor":
                #hexAccent = str(hex(value[1]))[4:]
                hexAccent = [int(str(hex(value[1]))[4:][2 * i:2 * i + 2], 16) for i in range(3)][::-1]
                return hexAccent
            i += 1
        except WindowsError as e:
            break
    return 1
class mutableInt():
    def __init__(self,num):
        self.__num=[int(num)]
        self.number=int(num)
    def set(self,newNum):
        self.__num[0]=int(newNum)
        self.number=int(newNum)
class mutableFloat():
    def __init__(self,num):
        self.__num=[float(num)]
        self.number=float(num)
    def set(self,newNum):
        self.__num[0]=float(newNum)
        self.number=float(newNum)
filterwarnings('ignore')
pygame.font.init()
pygame.display.init()
volume=mutableFloat(0.5)
currentAudioData=b''
darkMode=getDarkMode()
baseColor=[255-191*(1-darkMode) for i in range(3)]
uiColor=[255-darkMode*255 for i in range(3)]
otherUiColor=[255-darkMode*255 for i in range(3)]
client_id = 737918274548924446
discordRunning=False
percentFinished=0
currentSong=None
try:
    client=pypresence.Presence(client_id)
    client.connect()
    discordRunning=True
except Exception:
    pass
if discordRunning:
    client.update(state="In the Main Menu",details="Adding Songs To Playlist",large_image="icon",large_text="Music Player",small_image="searchpresence",small_text="Choosing a Song")
http=urllib3.PoolManager()
portAudio = pyaudio.PyAudio()
stream=portAudio.open(format=portAudio.get_format_from_width(2),channels=2,rate=44100,output=True)
running=True
screenDim=(pygame.display.Info().current_w,pygame.display.Info().current_h)
dimensions=(int(round(screenDim[0]/2)),int(round(screenDim[1]/2)))
segoe=pygame.font.Font("Segoe UI Font/Segoe UI.ttf",int(dimensions[1]/20))
playlistSegoe=pygame.font.Font("Segoe UI Font/Segoe UI.ttf",int(dimensions[1]/40))
pygame.display.set_caption("Music Player")
os.environ['SDL_VIDEO_WINDOW_POS']='%f,%f'%(screenDim[0]/4,screenDim[0]/4)
WINDOW=pygame.display.set_mode(dimensions,pygame.RESIZABLE|pygame.DOUBLEBUF)
WINDOW.set_alpha(None)
pygame.display.set_icon(pygame.image.load("icon.png").convert())
topBarColor=getAccentColor()
songQueue=[]
pygame.key.set_repeat(200,30)
lower=['`','1','2','3','4','5','6','7','8','9','0','-','=','[',']','\\',';','\'',',','.','/']
upper=['~','!','@','#','$','%','^','&','*','(',')','_','+','{','}','|',':','"','<','>','?']
currentTitle=""
queueImages=[]
defaultImg=pygame.image.load("default.jpg")
songTitles=[]
songObjList=[]
audioIndex=mutableInt(0)
leftChannel=[]
rightChannel=[]
lookAheadTime=0
for i in os.listdir("Queue"):
    print(os.path.splitext("Queue/" + i))
    if os.path.splitext("Queue/" + i)[1] == ".jpg":
        if os.path.isfile("Queue/" + i):
            os.remove("Queue/" + i)
def audioStreamData():
    global currentSong,songObjList,lookAheadTime,percentFinished,playingSong, songIndex, running, stream,songQueue,currentTitle, currentImg, audioIndex,leftChannel,rightChannel, musicPlayer, paused, queueImages, songTitles, discordRunning
    while running:
        time.sleep(0.01)
        if len(songObjList)>0 and playingSong==False:
            songIndex+=1
            if songIndex>=len(songObjList):
                songIndex=0
            notFunctional=True
            while notFunctional:
                try:
                    video = new(songObjList[songIndex].link)
                    notFunctional=False
                except Exception:
                    notFunctional=True
            successful=False
            while not(successful):
                try:
                    currentImg=songObjList[songIndex].image
                    currentTitle = songObjList[songIndex].title
                    successful=True
                except IndexError:
                    successful=False
            bestStream = video.getbestaudio()
            while True:
                #print('erase attempt')
                try:
                    if os.path.isfile('music.' + bestStream.extension):
                        os.remove('music.' + bestStream.extension)
                    break
                except PermissionError as e:
                    pass
            duration=video.length*44100
            def getPercent(total,recvd,ratio,rate,eta):
                global percentFinished
                percentFinished=ratio*100
            percentFinished=0
            bestStream.download(filepath="music." + bestStream.extension,callback=getPercent)
            currentSong=songObjList[songIndex]
            leftChannel=[None for i in range(duration)]
            rightChannel=[None for i in range(duration)]
            def fullAudio():
                global lookAheadTime, leftChannel, rightChannel
                lookAheadTime=10
                count=0
                while playingSong:
                    count+=1
                    #print('downloading '+str(count)+'...')
                    try:
                        ax, sr = load("music." + bestStream.extension, sr=44100, mono=False, offset=lookAheadTime, duration=10)
                        #print('downloaded '+str(lookAheadTime))
                        newLeftChannel,newRightChannel=ax
                        leftChannel[lookAheadTime*44100:lookAheadTime*44100+441000]=newLeftChannel
                        rightChannel[lookAheadTime*44100:lookAheadTime*44100+441000]=newRightChannel
                        if len(leftChannel)>duration or len(rightChannel)>duration:
                            leftChannel=leftChannel[:duration]
                            rightChannel=rightChannel[:duration]
                        lookAheadTime+=10
                    except ValueError:
                        pass
            yAx,sr=load("music."+bestStream.extension,sr=44100,mono=False,duration=10)
            leftChannel[0:441000] = list(yAx[0])
            rightChannel[0:441000] = list(yAx[1])
            playingSong = True
            newThread = threading.Thread(target=fullAudio)
            newThread.setDaemon(True)
            newThread.start()
            #print('loaded song...')
            '''if os.path.isfile('music.' + bestStream.extension):
                os.remove('music.' + bestStream.extension)'''
            if discordRunning:
                try:
                    client.update(state="Listening To Song", details=currentTitle, start=time.time(),large_image="icon",large_text="Music Player",small_image="playpresence",small_text="Playing "+currentTitle)
                except Exception:
                    discordRunning=False
            musicPlayer.resetSong(duration=duration)
            audioIndex=mutableInt(0)
            #print('playing song '+video.title)
        elif len(songObjList)>0 and playingSong==True:
            currentAudioData=b''
            if audioIndex.number<len(leftChannel):
                if not(paused):
                    if not(None in leftChannel[audioIndex.number:audioIndex.number+1024] or None in rightChannel[audioIndex.number:audioIndex.number+1024]) and len(leftChannel)-audioIndex.number>=44100:
                        for i in range(audioIndex.number,audioIndex.number+1024):
                            if i<len(leftChannel):
                                currentAudioData+=pack('h',normalize(int(leftChannel[i]*32767*volume.number),-32767,32767))
                                currentAudioData+=pack('h',normalize(int(rightChannel[i]*32767*volume.number),-32767,32767))
                        audioIndex.set(audioIndex.number+1024)
                    elif (None in leftChannel[audioIndex.number:audioIndex.number+1024] or None in rightChannel[audioIndex.number:audioIndex.number+1024]) and len(leftChannel)+44100-audioIndex.number>44100:
                        #audioIndex.set(audioIndex.number)
                        time.sleep(0.01)
                    elif len(leftChannel)-audioIndex.number<=44100:
                        audioIndex.set(audioIndex.number + 1024)
            else:
                percentFinished=0
                playingSong=False
            stream.write(currentAudioData)
audio=threading.Thread(target=audioStreamData,daemon=True)
audio.start()
def normalize(num,min,max):
    if num<min:
        return min
    elif num>max:
        return max
    else:
        return num
class TextBox(object):
    def __init__(self,position,dim,border=True):
        self.pos=position
        self.dim=dim
        self.rect=pygame.Rect(*self.pos,*self.dim)
        self.surf=pygame.Surface(self.dim)
        self.border=border
        self.typing=False
        self.font = pygame.font.Font("Segoe UI Font/Segoe UI.ttf", int(self.dim[1]*7/8))
        self.text=""
        self.on=True
        self.timer=pygame.time.Clock()
        self.tick=0
        self.notChars=['\b','\r','\n']
    def resize(self,position,dim):
        self.pos = position
        self.dim = dim
        self.rect = pygame.Rect(*self.pos, *self.dim)
        self.surf = pygame.Surface(self.dim)
        self.font = pygame.font.Font("Segoe UI Font/Segoe UI.ttf", int(self.dim[1] * 7 / 8))
    def update(self,surface,events):
        global upper, lower
        self.tick+=self.timer.tick()
        if self.tick>450:
            self.tick=0
            if self.on==True:
                self.on=False
            else:
                self.on=True
        #print(self.typing,self.rect.collidepoint(pygame.mouse.get_pos()))
        for event in events:
            if event.type==pygame.MOUSEBUTTONDOWN:
                #print(event.button)
                if event.button==1 and self.rect.collidepoint(pygame.mouse.get_pos()):
                    if self.typing==False:
                        self.typing=True
                elif event.button==1 and not(self.rect.collidepoint(pygame.mouse.get_pos())):
                    if self.typing==True:
                        self.typing=False
            if event.type==pygame.KEYDOWN and self.typing==True:
                try:
                    if not(chr(event.key) in self.notChars):
                        if not(pygame.key.get_pressed()[pygame.K_LSHIFT] or pygame.key.get_pressed()[pygame.K_RSHIFT]):
                            if not(chr(event.key)=='v' and (pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL])):
                                self.text+=chr(event.key)
                            else:
                                self.text+=paste()
                        else:
                            if not(chr(event.key) in lower):
                                self.text += chr(event.key).upper()
                            else:
                                self.text+=upper[lower.index(chr(event.key))]
                    else:
                        if chr(event.key)=='\b':
                            self.text=self.text[:len(self.text)-1]
                except ValueError:
                    pass
        self.draw(surface)
    def draw(self,surface):
        global segoeui, baseColor, uiColor, otherUiColor
        pygame.draw.rect(self.surf,baseColor,pygame.Rect(0,0,*self.dim))
        if self.font.size(self.text)[0]<self.dim[0]:
            drawPos=(0,int(-self.dim[1]/8))
            self.surf.blit(self.font.render(self.text,True,otherUiColor),drawPos)
        else:
            if self.typing:
                drawPos=(self.dim[0]-self.font.size(self.text)[0],int(-self.dim[1]/8))
                self.surf.blit(self.font.render(self.text,True,otherUiColor),drawPos)
            else:
                newText=self.text[::]
                while self.font.size(newText)[0]>=self.dim[0]:
                    newText=newText[:len(newText)-1]
                newText=newText[:len(newText)-2]
                newText+='...'
                drawPos=(0,int(-self.dim[1]/8))
                self.surf.blit(self.font.render(newText, True, otherUiColor), drawPos)
        if self.typing and self.on:
            pygame.draw.line(self.surf,otherUiColor,(drawPos[0]+self.font.size(self.text)[0]+int((dimensions[1]/2-dimensions[0]/40)/20),int(self.dim[1]*1/16)),(drawPos[0]+self.font.size(self.text)[0]+int((dimensions[1]/2-dimensions[0]/40)/20),int(self.dim[1]*15/16)))
        pygame.draw.rect(self.surf,uiColor,pygame.Rect(0,0,*self.dim),1)
        surface.blit(self.surf,self.pos)
        self.surf.fill(baseColor)
class Button(object):
    def __init__(self,pos,dim,text,color,method):
        self.pos=pos
        self.dim=dim
        self.rect=pygame.Rect(*self.pos,*self.dim)
        self.text=text
        self.color=color
        self.method=method
        self.click=False
        self.hover=False
        self.surf=pygame.Surface(self.dim)
        self.font=pygame.font.Font('Segoe UI Font/Segoe UI Bold.ttf',int(self.dim[1]/3))
    def update(self,surface,events,params,newColor=None):
        if newColor!=None:
            self.color=newColor
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            self.hover=True
        else:
            self.hover=False
        for event in events:
            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button==1 and self.rect.collidepoint(pygame.mouse.get_pos()):
                    self.method(*params)
                    self.click=True
            elif event.type==pygame.MOUSEBUTTONUP:
                if event.button==1:
                    self.click=False
        self.draw(surface)
    def resize(self,pos,dim):
        self.pos = pos
        self.dim = dim
        self.rect = pygame.Rect(*self.pos, *self.dim)
        self.surf = pygame.Surface(self.dim)
        self.font = pygame.font.Font('Segoe UI Font/Segoe UI Bold.ttf', int(self.dim[1]/3))
    def draw(self,surface):
        textPos=[0,0]
        textPos[0]=int(self.dim[0]/2-self.font.size(self.text)[0]/2)
        textPos[1] = int(self.dim[1] / 2 - self.font.size(self.text)[1] / 2)
        drawColor=list(self.color)
        if self.hover and not(self.click):
            for index,i in enumerate(drawColor):
                drawColor[index]+=(255-i)/2
        elif self.click:
            for index,i in enumerate(drawColor):
                drawColor[index]+=(255-i)*0.75
        drawColor=[int(i) for i in drawColor]
        self.surf.fill(drawColor)
        self.surf.blit(self.font.render(self.text,True,[((sum(self.color)/3)<128)*255 for i in range(3)]),textPos)
        surface.blit(self.surf,self.pos)
class ImageButton(object):
    def __init__(self,pos,dim,images,method,toggle=True):
        self.pos=[int(i) for i in pos]
        self.dim=[int(i) for i in dim]
        self.rect=pygame.Rect(*self.pos,*self.dim)
        self.images=images
        self.method=method
        self.click=False
        self.hover=False
        self.on=False
        self.mask=pygame.Surface(self.dim)
        self.mask.fill((0,1,0))
        self.mask.set_colorkey((255,255,255))
        pygame.draw.circle(self.mask,(255,255,255),(int(self.dim[0]/2),int(self.dim[1]/2)),int(self.dim[0]/2))
        self.surf=pygame.Surface(self.dim)
        self.surf=self.surf.convert_alpha()
        self.surf.set_colorkey((0,1,0))
        self.toggle=toggle
        self.currentImage=pygame.image.load(self.images[0]).convert_alpha()
        self.surf.blit(pygame.transform.scale(self.currentImage,self.dim),(0,0))
        self.surf.blit(self.mask,(0,0))
        self.darken=pygame.Surface(self.dim)
        self.darken.convert_alpha()
        self.darken.fill((0,0,0))
    def update(self,surface,events,params,toggleVar=None,offset=(0,0)):
        newPos = [self.pos[i] + offset[i] for i in range(2)]
        newRect=pygame.Rect(*newPos,*self.dim)
        if self.toggle:
            self.on=toggleVar
        if newRect.collidepoint(pygame.mouse.get_pos()):
            self.hover=True
        else:
            self.hover=False
        for event in events:
            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button==1 and newRect.collidepoint(pygame.mouse.get_pos()):
                    self.method(*params)
                    self.click=True
            elif event.type==pygame.MOUSEBUTTONUP:
                if event.button==1:
                    self.click=False
        self.draw(surface,offset)
    def resize(self,pos,dim):
        self.pos = [int(i) for i in pos]
        self.dim = [int(i) for i in dim]
        self.rect = pygame.Rect(*self.pos, *self.dim)
        self.mask = pygame.Surface(self.dim)
        self.mask.fill((0, 1, 0))
        self.mask.set_colorkey((255, 255, 255))
        pygame.draw.circle(self.mask, (255, 255, 255), (int(self.dim[0] / 2), int(self.dim[1] / 2)),
                           int(self.dim[0] / 2))
        self.surf = pygame.Surface(self.dim)
        self.surf.convert_alpha()
        self.surf.set_colorkey((0, 1, 0))
        self.currentImage = pygame.image.load(self.images[0]).convert_alpha()
        self.surf.blit(pygame.transform.scale(self.currentImage, self.dim), (0, 0))
        self.surf.blit(self.mask, (0, 0))
        self.darken = pygame.Surface(self.dim)
        self.darken.convert_alpha()
        self.darken.fill((0, 0, 0))
    def draw(self,surface,offset):
        newPos=[self.pos[i]+offset[i] for i in range(2)]
        if self.toggle:
            if self.on==False:
                self.currentImage = pygame.image.load(self.images[0]).convert_alpha()
                self.surf.blit(pygame.transform.scale(self.currentImage, self.dim), (0, 0))
            else:
                self.currentImage = pygame.image.load(self.images[1]).convert_alpha()
                self.surf.blit(pygame.transform.scale(self.currentImage, self.dim), (0, 0))
        else:
            self.currentImage = pygame.image.load(self.images[0]).convert_alpha()
            self.surf.blit(pygame.transform.scale(self.currentImage, self.dim), (0, 0))
        if self.hover and not(self.click):
            self.darken.fill((0, 0, 0))
            self.darken.set_alpha(64)
        elif self.click:
            self.darken.fill((0, 0, 0))
            self.darken.set_alpha(128)
        else:
            self.darken.fill((0, 0, 0))
            self.darken.set_alpha(0)
        surf=self.surf.copy()
        surf.set_colorkey((0,1,0))
        surf.convert_alpha()
        surf.blit(self.darken,(0,0))
        surf.blit(self.mask, (0, 0))
        surface.blit(surf,newPos)
        self.surf.fill((0,1,0))
class MusicSlider(object):
    def __init__(self,start,end,duration=0):
        self.start=start
        self.end=end
        self.duration=duration
        self.timeElapsed="0:00"
        self.songLength="0:00"
        self.elapsed=0
        self.circlePos=self.start
        self.dragging=False
    def update(self,surface,events,currentTime):
        global dimensions, lookAheadTime, discordRunning
        if self.dragging==True:
            newTime=(normalize(pygame.mouse.get_pos()[0],self.start[0],self.end[0])-self.start[0])/(self.end[0]-self.start[0])*self.duration
            currentTime.set(newTime)
            lookAheadTime=int(newTime/44100)-10
            if discordRunning:
                try:
                    client.update(state="Listening To Song", details=currentTitle,
                                  start=time.time() - audioIndex.number / 44100, large_image="icon",
                                  large_text="Music Player", small_image="playpresence",
                                  small_text="Playing " + currentTitle)
                except Exception:
                    discordRunning = False
        self.elapsed=currentTime.number
        self.songLength = str(int(self.duration / 44100 / 60)) + ":" + str(int(self.duration/ 44100) % 60).zfill(2)
        self.timeElapsed = str(int(self.elapsed / 44100 / 60)) + ":" + str(int(self.elapsed / 44100) % 60).zfill(2)
        if self.duration != 0:
            self.circlePos=(
                self.start[0] + self.elapsed / self.duration * (self.end[0]-self.start[0]),
                self.end[1])
        self.circleRect=pygame.Rect(self.circlePos[0]-int(dimensions[1]/60),self.circlePos[1]-int(dimensions[1]/60),int(dimensions[1]/30),int(dimensions[1]/30))
        for event in events:
            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button==1:
                    if self.circleRect.collidepoint(pygame.mouse.get_pos()):
                        self.dragging=True
            elif event.type==pygame.MOUSEBUTTONUP:
                if event.button==1:
                    if self.circleRect.collidepoint(pygame.mouse.get_pos()):
                        try:
                            if discordRunning:
                                if paused==False:
                                    try:
                                        client.update(state="Listening To Song", details=songTitles[songIndex], start=time.time()-currentTime.number/44100,large_image="icon",large_text="Music Player",small_image="playpresence",small_text="Playing "+songTitles[songIndex])
                                    except Exception:
                                        discordRunning=False
                        except Exception:
                            pass
                    self.dragging=False
        self.draw(surface)
    def draw(self,surface):
        global playlistSegoe,segoe,dimensions,baseColor,uiColor,otherUiColor
        pygame.draw.line(surface, uiColor, self.start, self.end)
        pygame.draw.circle(surface, uiColor, self.circlePos,int(dimensions[1]/60))
        pygame.draw.circle(surface, otherUiColor, self.circlePos,int(dimensions[1]/60), 1)
        surface.blit(playlistSegoe.render(self.songLength, True, uiColor), (self.end[0] + int(dimensions[1] / 60),self.end[1] -playlistSegoe.size(self.songLength)[1] / 2))
        surface.blit(playlistSegoe.render(self.timeElapsed, True, uiColor), (
            self.start[0] - int(dimensions[1] / 60) - playlistSegoe.size(self.timeElapsed)[0],self.start[1] -
            playlistSegoe.size(self.songLength)[1] / 2))
    def resetSong(self,duration):
        self.duration=duration
        self.elapsed=0
    def resize(self,start,end):
        self.start = start
        self.end = end
class Song(object):
    def __init__(self,link,image,title):
        global dimensions,baseColor,uiColor
        self.link=link
        self.image=image
        self.title=title
        self.surf=pygame.Surface((int(dimensions[0]/2),int(dimensions[0]/12)))
        self.surf.fill((0,0,1))
        self.surf.set_colorkey((0,0,1))
        surfHeight=self.surf.get_height()
        self.nameFont = pygame.font.Font("Segoe UI Font/Segoe UI.ttf", int(surfHeight/6))
        self.surf.blit(pygame.transform.scale(self.image,(int(int(surfHeight*2/3)*4/3),int(surfHeight*2/3))),(int(surfHeight/6),int(surfHeight/6)))
        self.surf.blit(self.nameFont.render(self.title,True,uiColor),(int(dimensions[0]/4)-int(self.nameFont.size(self.title)[0]/2),int(surfHeight*2.5/6)))
    def resizeSurf(self):
        global dimensions
        self.__init__(self.link,self.image,self.title)
class Playlist(object):
    def __init__(self):
        self.scroll=0
        self.moving=None
        self.expandQueue=False
        self.selected=None
        self.finishedSurf=pygame.Surface(dimensions)
        self.startSelect=False
        self.removedCurrent=False
        self.currentIndex=0
        self.darkenTrack=pygame.Surface((int(dimensions[0] / 2),int(dimensions[0] / 12)))
        self.darkenTrack.set_alpha(128)
        self.darkenTrack.fill((0,0,0))
        self.allSongs=[]
        self.moveDrawPlaying=0
        self.queueTransition=-1
        self.timer=pygame.time.Clock()
        self.transTime=0
        self.transSpeed=500
    def blitPlaylist(self,pos):
        global currentSong,darken, WINDOW, dimensions, songIndex, songObjList, songQueue, baseColor, uiColor, otherUiColor, queueImages, songTitles
        pygame.draw.rect(WINDOW, baseColor,
                         pygame.Rect(pos[0]+int(dimensions[0]*1/40), pos[1],
                                     int(dimensions[0] / 2), dimensions[1]))
        pygame.draw.rect(WINDOW, topBarColor,
                         pygame.Rect(pos[0], pos[1],
                                     int(dimensions[0] / 40), dimensions[1]))
        playlist = pygame.Surface(
            (pos[0]+int(dimensions[0]*1/40),
             int(dimensions[1] - segoe.size("Your Playlist")[1] * 2)+pos[1]))
        playlist.fill(baseColor)
        lighten=pygame.Surface((int(dimensions[0] / 2),int(dimensions[0] / 12)))
        lighten.set_alpha(64)
        lighten.fill(topBarColor)
        self.darkenTrack = pygame.Surface((int(dimensions[0] / 2), int(dimensions[0] / 12)))
        self.darkenTrack.set_alpha(128)
        self.darkenTrack.fill((0, 0, 0))
        for index, song in enumerate(songObjList):
            if index*int(dimensions[0]/12)+self.scroll<dimensions[1]-segoe.size("Your Playlist")[1]:
                if songIndex==index:
                    playlist.blit(lighten,(0,self.scroll+index*int(dimensions[0]/12)))
                playlist.blit(song.surf,(0,index*int(dimensions[0]/12)+self.scroll))
                pygame.draw.rect(playlist,uiColor,pygame.Rect(0,index*int(dimensions[0]/12)+self.scroll,int(dimensions[0]/2),int(dimensions[0]/12)),2)
                if songIndex==index:
                    playlist.blit(song.nameFont.render("--Now Playing--",True,uiColor),(int(dimensions[0]/4)-int(song.nameFont.size("--Now Playing--")[0]/2),self.scroll+index*int(dimensions[0]/12)+int(song.surf.get_height()/6)))
        WINDOW.blit(playlist,(pos[0]+int(dimensions[0]*1/40),pos[1]+segoe.size("Your Playlist")[1]))
        pygame.draw.rect(WINDOW, (baseColor),
                         pygame.Rect(pos[0]+int(dimensions[0]*1/40), pos[1],
                                     int(dimensions[0] / 2),
                                     segoe.size("Your Playlist")[1]))
        pygame.draw.rect(WINDOW, (baseColor),
                         pygame.Rect(pos[0]+int(dimensions[0]*1/40),
                                     dimensions[1] - segoe.size("Your Playlist")[1]+pos[1],
                                     int(dimensions[0] / 2),
                                     segoe.size("Your Playlist")[1]))
        WINDOW.blit(segoe.render("Your Playlist", True, uiColor),
                    (int(int(dimensions[0] * 3 / 4 - segoe.size("Your Playlist")[0] / 2) + pos[0]-int(dimensions[0]*19/40)), pos[1]))
    def update(self,events):
        global darken,WINDOW,dimensions,songIndex,songObjList,songQueue,baseColor,uiColor,otherUiColor,queueImages,songTitles
        tick=self.timer.tick()
        if self.queueTransition==1:
            self.transTime+=tick
            if self.transTime<self.transSpeed:
                x=(1-(self.transTime/self.transSpeed))**4
                #print(x)
                darken.set_alpha((self.transTime/self.transSpeed)*128)
                WINDOW.blit(darken, (0, 0))
                self.blitPlaylist(((int(dimensions[0] * 19 / 40) + int(dimensions[0] * 21 / 40) * x,0)))
            else:
                darken.set_alpha(128)
                #WINDOW.blit(darken, (0, 0))
                self.expandQueue=True
                self.queueTransition=-1
        elif self.queueTransition==0:
            self.transTime += tick
            if self.transTime < self.transSpeed:
                x = (1-(1 - (self.transTime / self.transSpeed)) ** 4)
                #print((self.transTime / self.transSpeed) * 128)
                darken.set_alpha((1-(self.transTime / self.transSpeed)) * 128)
                WINDOW.blit(darken, (0, 0))
                self.blitPlaylist(((int(dimensions[0] * 19 / 40) + int(dimensions[0] * 20 / 40) * x, 0)))
            else:
                darken.set_alpha(0)
                WINDOW.blit(darken, (0, 0))
                pygame.draw.rect(WINDOW, topBarColor,
                                 pygame.Rect(int(dimensions[0] * 39 / 40), 0, int(dimensions[0] / 40), dimensions[1]))
                self.expandQueue = False
                self.queueTransition = -1
        if self.expandQueue == False and self.queueTransition==-1:
            self.selected=None
            self.startSelect=False
            pygame.draw.rect(WINDOW, topBarColor,
                             pygame.Rect(int(dimensions[0] * 39 / 40), 0, int(dimensions[0] / 40), dimensions[1]))
            if pygame.Rect(int(dimensions[0] * 39 / 40), 0, int(dimensions[0] / 40), dimensions[1]).collidepoint(
                    pygame.mouse.get_pos()):
                self.queueTransition = 1
                self.transTime=0
        elif self.expandQueue == True and self.queueTransition==-1:
            for event in allEvents:
                if event.type==pygame.MOUSEWHEEL:
                    #print(event.y,self.scroll, -(len(songObjList)*int(dimensions[0]/12))+(dimensions[1]-segoe.size("Your Playlist")[1]*2))
                    if (-event.y>0 and self.scroll>-(len(songObjList)*int(dimensions[0]/12))+(dimensions[1]-segoe.size("Your Playlist")[1]*2)) or (-event.y<0 and self.scroll<0):
                        self.scroll+=event.y*10
                    else:
                        if -event.y>0:
                            self.scroll=-(len(songObjList)*int(dimensions[0]/12))+(dimensions[1]-segoe.size("Your Playlist")[1]*2)
                        elif -event.y<0:
                            self.scroll=0
                if event.type==pygame.MOUSEBUTTONUP:
                    if event.button==1:
                        print(int((pygame.mouse.get_pos()[1]-self.scroll-segoe.size("Your Playlist")[1])/int(dimensions[0]/12)))
            darken.set_alpha(128)
            WINDOW.blit(darken, (0, 0))
            self.blitPlaylist(((int(dimensions[0] * 19 / 40),0)))
            if pygame.Rect(0, 0, int(dimensions[0] * 19 / 40), dimensions[1]).collidepoint(pygame.mouse.get_pos()):
                self.queueTransition=0
                self.transTime=0
class VolumeSlider(object):
    def __init__(self,x,y1,y2,startPos,sliderDim):
        self.x=x
        self.yRange = [y1,y2]
        self.pos=startPos
        self.selected=False
        self.sliderDim=sliderDim
        self.sliderRect=pygame.Rect(self.x-sliderDim[0]/2,((1-self.pos)*(y2-y1))+y1-sliderDim[1]/2,*sliderDim)
    def lockPos(self,lower,upper,val):
        if val<=lower:
            return lower
        elif val>=upper:
            return upper
        else:
            return val
    def update(self,allevents,varMod):
        for event in allevents:
            if event.type==pygame.MOUSEBUTTONDOWN:
                if self.sliderRect.collidepoint(pygame.mouse.get_pos()):
                    self.selected=True
            elif event.type==pygame.MOUSEBUTTONUP:
                self.selected=False
        if self.selected==True:
            self.pos=1-(self.lockPos(self.yRange[0],self.yRange[1],pygame.mouse.get_pos()[1]+self.sliderDim[1]/2)-self.yRange[0])/(self.yRange[1]-self.yRange[0])
        varMod.set(self.pos)
        self.sliderRect = pygame.Rect(self.x - self.sliderDim[0] / 2,((1- self.pos) * (self.yRange[1] - self.yRange[0])) + self.yRange[0] - self.sliderDim[1] / 2, *self.sliderDim)
    def draw(self,surface):
        pygame.draw.line(surface, uiColor, [self.x, self.yRange[0]], [self.x, self.yRange[1]], 3)
        pygame.draw.rect(surface, (255, 255, 255), self.sliderRect)
        pygame.draw.rect(surface, (0,0,0), self.sliderRect,3)
    def resize(self,x,y1,y2,sliderDim):
        self.x = x
        self.yRange = [y1, y2]
        self.sliderDim = sliderDim
        self.sliderRect = pygame.Rect(self.x - sliderDim[0] / 2, ((1 - self.pos) * (y2 - y1)) + y1 - sliderDim[1] / 2,
                                      *sliderDim)
def addPlaylist(videos):
    global songQueue,queueImages, defaultImg
    for i in os.listdir("Queue"):
        print(os.path.splitext("Queue/" + i))
        if os.path.splitext("Queue/" + i)[1] == ".jpg":
            if os.path.isfile("Queue/" + i):
                os.remove("Queue/" + i)
    for link in videos:
        if not(link in songQueue):
            successful = False
            attempts=0
            while not (successful):
                try:
                    video = new(link)
                    successful = True
                except Exception as e:
                    attempts+=1
                    successful = False
                    if attempts>15:
                        successful=True
            if attempts>15:
                pass
            else:
                songQueue.append(link)
                newTitle = video.title
                for index, x in enumerate(newTitle):
                    #print(ord(x))
                    if ord(x) > 65535:
                        listTitle = list(newTitle)
                        listTitle[index] = "\u25a1"
                        newTitle = "".join(listTitle)
                songTitles.append(newTitle)
                urllib.request.urlretrieve(video.bigthumbhd, "Queue/video" + str(len(songQueue)).zfill(4) + ".jpg")
                if os.path.isfile('Queue/video' + str(len(songQueue)).zfill(4) + '.jpg'):
                    queueImages.append(pygame.image.load("Queue/video" + str(len(songQueue)).zfill(4) + ".jpg"))
                    songObjList.append(Song(link, pygame.image.load("Queue/video" + str(len(songQueue)).zfill(4) + ".jpg"), newTitle))
                else:
                    queueImages.append(defaultImg)
                    songObjList.append(Song(link, defaultImg, newTitle))
playlistAddThread=None
hrefs=None
def search(query):
    global songQueue, songMenu, hrefs, searchMenu,queueImages,defaultImg,songTitles, music,http, playlistAddThread
    print(query)
    added=False
    playlist=False
    for i in range(5):
        if not(added):
            print('Attempt ' + str(i + 1) + '...')
            try:
                if len(query)>32:
                    if query[0:32]=="https://www.youtube.com/watch?v=":
                        link=query
                    else:
                        if len(query) > 38:
                            if query[0:38] == "https://www.youtube.com/playlist?list=":
                                playlist=True
                                print('playlist')
                                web=requests.get(query)
                                bs = BeautifulSoup(web.text,'html.parser')
                                hrefs = bs.find_all(href=True)
                                jsonResponse=json.loads(web.text[web.text.index('window["ytInitialData"]')+26:web.text[web.text.index('window["ytInitialData"]'):].index('\n')+web.text.index('window["ytInitialData"]')-1])
                                content=jsonResponse['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['playlistVideoListRenderer']['contents']
                                videos=[]
                                for i in content:
                                    videos.append("https://www.youtube.com/watch?v="+i['playlistVideoRenderer']['videoId'])
                                playlistAddThread=threading.Thread(target=addPlaylist,args=[videos],daemon=True)
                                playlistAddThread.start()

                            else:
                                results = json.loads(SearchVideos(query, max_results=1).result())['search_result']
                                print(results)
                                link = results[0]['link']
                        else:
                            results = json.loads(SearchVideos(query, max_results=1).result())['search_result']
                            print(results)
                            link = results[0]['link']
                else:
                    results = json.loads(SearchVideos(query, max_results=1).result())['search_result']
                    print(results, query)
                    link = results[0]['link']
                if not(playlist):
                    for i in os.listdir("Queue"):
                        print(os.path.splitext("Queue/" + i))
                        if os.path.splitext("Queue/" + i)[1] == ".jpg":
                            if os.path.isfile("Queue/" + i):
                                os.remove("Queue/" + i)
                    songQueue.append(link)
                    successful=False
                    while not (successful):
                        try:
                            video = new(link)
                            successful = True
                        except Exception as e:
                            successful = False
                    newTitle = video.title
                    for index, x in enumerate(newTitle):
                        # print(ord(x))
                        if ord(x) > 65535:
                            listTitle = list(newTitle)
                            listTitle[index] = "\u25a1"
                            newTitle = "".join(listTitle)
                    urllib.request.urlretrieve(video.bigthumbhd, "Queue/video" + str(len(songObjList) + 1).zfill(4) + ".jpg")
                    if os.path.isfile('Queue/video' + str(len(songObjList) + 1).zfill(4) + '.jpg'):
                        queueImages.append(pygame.image.load("Queue/video" + str(len(songObjList) + 1).zfill(4) + ".jpg"))
                        songObjList.append(
                            Song(link, pygame.image.load("Queue/video" + str(len(songObjList) + 1).zfill(4) + ".jpg"), newTitle))
                    else:
                        queueImages.append(defaultImg)
                        songObjList.append(Song(link, defaultImg, newTitle))
                songMenu=True
                searchMenu=False
                added=True
            except Exception as e:
                print(e)
                pass
    if not(added):
        print('No song named '+query+' found.')
        music.text=""
    else:
        print('found song')
        songMenu=True
        searchMenu=False
def goToSearch():
    global songMenu, searchMenu
    if songMenu==True:
        searchMenu=True
        songMenu=False
def togglePause():
    global paused,discordRunning
    if paused:
        if discordRunning:
            try:
                client.update(state="Listening To Song", details=currentTitle, start=time.time()-audioIndex.number/44100,large_image="icon",large_text="Music Player",small_image="playpresence",small_text="Playing "+currentTitle)
            except Exception:
                discordRunning=False
        paused=False
    else:
        if discordRunning:
            try:
                client.update(state="Paused Song", details=currentTitle,large_image="icon",large_text="Music Player",small_image="pausepresence",small_text="Paused")
            except Exception:
                discordRunning=False
        paused=True
def skip():
    global audioIndex,leftChannel
    audioIndex.set(len(leftChannel))
def rewind():
    global audioIndex, songIndex, leftChannel
    songIndex-=2
    audioIndex.set(len(leftChannel))
def resizeFunc():
    global mainMenu, trackMenu, darken, musicPlayer, songObjList,dimensions, music, segoe, searchButton, backButton, skipButton,rewindButton,playlistSegoe,pauseButton,volumeSlider
    music.resize((int(dimensions[0] / 4), int(dimensions[1] / 2 - dimensions[0] / 40)),
                 (int(dimensions[0] / 2), int(dimensions[0] / 10)))
    searchButton.resize((int(dimensions[0] * 3 / 8), int(dimensions[1] / 2 + dimensions[0] / 10)),
                        (int(dimensions[0] / 4), int(dimensions[0] / 12)))
    backButton.resize((0, 0), (dimensions[0] / 10, dimensions[0] / 30))
    skipButton.resize((dimensions[0] / 2 + dimensions[0] / 8 - dimensions[0] / 40,
                       int(dimensions[1] / 10) + int(dimensions[0] / 4) + int(segoe.size(currentTitle)[1] * 2.5) + int(
                           dimensions[1] / 20) + int(dimensions[0] / 20 - dimensions[0] / 30)),
                      (dimensions[0] / 15, dimensions[0] / 15))
    rewindButton.resize((dimensions[0] / 2 - dimensions[0] / 8 - dimensions[0] / 40,
                         int(dimensions[1] / 10) + int(dimensions[0] / 4) + int(
                             segoe.size(currentTitle)[1] * 2.5) + int(dimensions[1] / 20) + int(
                             dimensions[0] / 20 - dimensions[0] / 30)), (dimensions[0] / 15, dimensions[0] / 15))
    segoe = pygame.font.Font("Segoe UI Font/Segoe UI.ttf", int(dimensions[1] / 20))
    playlistSegoe = pygame.font.Font("Segoe UI Font/Segoe UI.ttf", int(dimensions[1] / 40))
    pauseButton.resize((dimensions[0] / 2 - dimensions[0] / 20,
                        int(dimensions[1] / 10) + int(dimensions[0] / 4) + int(segoe.size(currentTitle)[1] * 2.5) + int(
                            dimensions[1] / 20)), (dimensions[0] / 10, dimensions[0] / 10))
    volumeSlider.resize(dimensions[0] / 2 + dimensions[0] / 8 + dimensions[0] / 15,
                        int(dimensions[1] / 10) + int(dimensions[0] / 4) + int(segoe.size(currentTitle)[1] * 2.5) + int(
                            dimensions[1] / 20) + int(dimensions[0] / 20 - dimensions[0] / 20),
                        int(dimensions[1] / 10) + int(dimensions[0] / 4) + int(segoe.size(currentTitle)[1] * 2.5) + int(
                            dimensions[1] / 20) + int(dimensions[0] / 20 + dimensions[0] / 30),
                        [dimensions[0] / 45, dimensions[0] / (90)])
    darken = pygame.Surface(dimensions)
    darken.set_alpha(128)
    darken.fill((0, 0, 0))
    musicPlayer.resize((int(dimensions[0] / 4),
                        int(dimensions[1] / 10) + int(dimensions[0] / 4) + int(segoe.size(currentTitle)[1] * 2.5)), (
                       int(dimensions[0] * 3 / 4),
                       int(dimensions[1] / 10) + int(dimensions[0] / 4) + int(segoe.size(currentTitle)[1] * 2.5)))
    for song in songObjList:
        song.resizeSurf()
    mainMenu = pygame.Surface(dimensions)
    trackMenu = pygame.Surface(dimensions)
paused=False
music=TextBox((int(dimensions[0]/4),int(dimensions[1]/2-dimensions[0]/20)),(int(dimensions[0]/2),int(dimensions[0]/10)))
searchButton=Button((int(dimensions[0]*3/8),int(dimensions[1]/2+dimensions[0]/10)),(int(dimensions[0]/4),int(dimensions[0]/12)),"Search",topBarColor,search)
backButton=Button((0,0),(dimensions[0]/10,dimensions[0]/30),"Back",topBarColor,goToSearch)
mainMenu=pygame.Surface(dimensions)
songIndex=-1
playingSong=False
searchMenu=True
songMenu=False
trackMenu=pygame.Surface(dimensions)
expandQueue=False
darken=pygame.Surface(dimensions)
darken.set_alpha(128)
darken.fill((0,0,0))
musicPlayer=MusicSlider((int(dimensions[0]/4),int(dimensions[1]/10)+int(dimensions[0]/4)+int(segoe.size(currentTitle)[1]*2.5)),(int(dimensions[0]*3/4),int(dimensions[1]/10)+int(dimensions[0]/4)+int(segoe.size(currentTitle)[1]*2.5)))
pauseButton=ImageButton((dimensions[0]/2-dimensions[0]/20,int(dimensions[1]/10)+int(dimensions[0]/4)+int(segoe.size(currentTitle)[1]*2.5)+int(dimensions[1]/20)),(dimensions[0]/10,dimensions[0]/10),["pause.png","play.png"],togglePause)
skipButton=ImageButton((dimensions[0]/2+dimensions[0]/8-dimensions[0]/30,int(dimensions[1]/10)+int(dimensions[0]/4)+int(segoe.size(currentTitle)[1]*2.5)+int(dimensions[1]/20)+int(dimensions[0]/20-dimensions[0]/30)),(dimensions[0]/15,dimensions[0]/15),["skip.png"],skip,toggle=False)
rewindButton=ImageButton((dimensions[0]/2-dimensions[0]/8-dimensions[0]/30,int(dimensions[1]/10)+int(dimensions[0]/4)+int(segoe.size(currentTitle)[1]*2.5)+int(dimensions[1]/20)+int(dimensions[0]/20-dimensions[0]/30)),(dimensions[0]/15,dimensions[0]/15),["rewind.png"],rewind,toggle=False)
volumeSlider=VolumeSlider(dimensions[0]/2+dimensions[0]/8+dimensions[0]/15,int(dimensions[1]/10)+int(dimensions[0]/4)+int(segoe.size(currentTitle)[1]*2.5)+int(dimensions[1]/20)+int(dimensions[0]/20-dimensions[0]/20),int(dimensions[1]/10)+int(dimensions[0]/4)+int(segoe.size(currentTitle)[1]*2.5)+int(dimensions[1]/20)+int(dimensions[0]/20+dimensions[0]/30),volume.number,[dimensions[0]/45,dimensions[0]/(45*2)])
drawPlaylist=Playlist()
currentImg=pygame.image.load('default.jpg')
volumeIcons=['Volume Slider/mute.png','Volume Slider/low.png','Volume Slider/mid.png','Volume Slider/high.png']
volumeIcons=[[pygame.image.load(x) for x in (i,i[:len(i)-4]+"Dark.png")] for i in volumeIcons]
while running:
    #print(len(songObjList))
    #print(volume.number)
    darkMode = getDarkMode()
    baseColor = [255 - 191 * (1 - darkMode) for i in range(3)]
    uiColor = [255 - darkMode * 255 for i in range(3)]
    otherUiColor = [255 - darkMode * 255 for i in range(3)]
    topBarColor = getAccentColor()
    if not(discordRunning):
        try:
            client = pypresence.Presence(client_id)
            client.connect()
            discordRunning = True
            if searchMenu:
                client.update(state="In the Main Menu", details="Adding Songs To Playlist", large_image="icon",
                              large_text="Music Player", small_image="searchpresence", small_text="Choosing a Song")
            elif songMenu:
                client.update(state="Listening To Song", details=currentTitle,
                              start=time.time() - audioIndex.number / 44100, large_image="icon",
                              large_text="Music Player", small_image="playpresence",
                              small_text="Playing " + currentTitle)
        except Exception:
            pass
    allEvents=pygame.event.get()
    if searchMenu==True:
        music.update(mainMenu,allEvents)
        searchButton.update(mainMenu,allEvents,[music.text],topBarColor)
    elif songMenu==True:
        songImg=pygame.transform.scale(currentImg,(int(dimensions[0]/3),int(dimensions[0]/4)))
        trackMenu.blit(songImg,(int(dimensions[0]/3),int(dimensions[1]/20)))
        if playingSong:
            trackMenu.blit(segoe.render("Now Playing:", True, uiColor), (
            int(dimensions[0] / 2 - segoe.size("Now Playing:")[0] / 2),
            int(dimensions[1] / 10) + int(dimensions[0] / 4)))
        else:
            trackMenu.blit(segoe.render("Downloading... ["+str(round(percentFinished,2))+"%]", True, uiColor), (
                int(dimensions[0] / 2 - segoe.size("Downloading... ["+str(round(percentFinished,2))+"%]")[0] / 2),
                int(dimensions[1] / 10) + int(dimensions[0] / 4)))
        backButton.update(trackMenu,allEvents,[],topBarColor)
        trackMenu.blit(segoe.render(currentTitle,True,uiColor),(int(dimensions[0]/2-segoe.size(currentTitle)[0]/2),int(dimensions[1]/10)+int(dimensions[0]/4)+segoe.size(currentTitle)[1]))
        if drawPlaylist.expandQueue == False:
            pauseButton.update(trackMenu,allEvents,[],paused)
            skipButton.update(trackMenu,allEvents,[])
            rewindButton.update(trackMenu, allEvents, [])
            musicPlayer.update(trackMenu, allEvents, audioIndex)
            volumeSlider.update(allEvents, volume)
            volumeSlider.draw(trackMenu)
            trackMenu.blit(pygame.transform.scale(volumeIcons[int(ceil(volume.number * 3))][darkMode],(int(dimensions[0] / 45), int(dimensions[0] / 45))), (dimensions[0] / 2 + dimensions[0] / 8 + dimensions[0] / 15 - int(dimensions[0] / 90),int(dimensions[1] / 10) + int(dimensions[0] / 4) + int(segoe.size(currentTitle)[1] * 2.5) + int(dimensions[1] / 20) + int(dimensions[0] / 20 + dimensions[0] / 40) + int(dimensions[0] / 90)))
        else:
            pauseButton.update(trackMenu, [], [], paused)
            skipButton.update(trackMenu, [], [])
            rewindButton.update(trackMenu, [], [])
            musicPlayer.update(trackMenu, [], audioIndex)
            volumeSlider.update([], volume)
            volumeSlider.draw(trackMenu)
            trackMenu.blit(pygame.transform.scale(volumeIcons[int(ceil(volume.number * 3))][darkMode],(int(dimensions[0] / 45), int(dimensions[0] / 45))), (dimensions[0] / 2 + dimensions[0] / 8 + dimensions[0] / 15 - int(dimensions[0] / 90),int(dimensions[1] / 10) + int(dimensions[0] / 4) + int(segoe.size(currentTitle)[1] * 2.5) + int(dimensions[1] / 20) + int(dimensions[0] / 20 + dimensions[0] / 40) + int(dimensions[0] / 90)))
    if searchMenu==True:
        WINDOW.blit(mainMenu,(0,0))
    elif songMenu==True:
        WINDOW.blit(trackMenu,(0,0))
    pygame.draw.rect(WINDOW, topBarColor, pygame.Rect(0, dimensions[1] - 40, dimensions[0], 40))
    drawPlaylist.update(allEvents)
    pygame.display.update()
    mainMenu.fill(baseColor)
    trackMenu.fill(baseColor)
    WINDOW.fill(baseColor)
    for event in allEvents:
        if event.type==pygame.QUIT:
            pygame.quit()
            running=False
        if event.type==pygame.KEYDOWN:
            if event.type==pygame.KEYDOWN:
                if event.key==1073742085:
                    togglePause()
                elif event.key==1073742083:
                    rewind()
                elif event.key==1073742082:
                    skip()
        if event.type==pygame.VIDEORESIZE:
            #print('resize',event.size,event.w,event.h)
            dimensions=(event.w,event.h)
            resizeThread=threading.Thread(target=resizeFunc,daemon=True)
            resizeThread.start()
stream.close()
if discordRunning:
    client.clear()
    client.close()