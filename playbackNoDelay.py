import pyaudio,librosa,time, threading
from struct import pack
from warnings import filterwarnings
#put music in "Test Audio" folder
filterwarnings('ignore')
whatFile="PANDA EYES - LOST.mp3"
def isFile(arg):
    try:
        return True
    except FileNotFoundError:
        return False
while not(isFile(whatFile)):
    whatFile=input('Invalid File. What file to play? ')
playbackSpeed='1'
def isFloat(arg):
    try:
        float(arg)
        return True
    except ValueError:
        return False
while not(isFloat(playbackSpeed)):
    playbackSpeed=input('Invalid Speed. Playback Speed? ')
print('bruh1')
l=[]
r=[]
sr=44100
def getChunk():
    global l,r,sr
    t = 0
    while True:
        try:
            y, sr = librosa.load("Test Audio/" + whatFile, mono=False, sr=sr, offset=t, duration=10)
            print('downloaded')
            for i in y[0]:
                l.append(i)
            for i in y[1]:
                r.append(i)
            t+=10
        except ValueError:
            return False
print('bruh')
newThread=threading.Thread(target=getChunk)
newThread.setDaemon(True)
newThread.start()
'''l=y[0]
r=y[1]'''
while len(l)==0:
    pass
p=pyaudio.PyAudio()
stream=p.open(format=p.get_format_from_width(2),rate=sr,channels=2,output=True)
index=0
t=float(playbackSpeed)
while index-1024<len(l):
    try:
        data=[]
        for i in range(int(index),int(index)+1024):
            data.append(int(l[i]*32767))
            data.append(int(l[i]*32767))
        bytesData=b''
        for i in range(1024*2):
            bytesData+=pack('h',data[i])
        stream.write(bytesData)
        index+=1024*t
    except Exception:
        index+=1024*t