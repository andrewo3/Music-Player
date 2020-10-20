import pyaudio,librosa
from struct import pack
from warnings import filterwarnings
#put music in "Test Audio" folder
filterwarnings('ignore')
whatFile=input('What file to play? ')
def isFile(arg):
    try:
        librosa.load("Test Audio/"+arg, mono=False, sr=44100)
        return True
    except FileNotFoundError:
        return False
while not(isFile(whatFile)):
    whatFile=input('Invalid File. What file to play? ')
playbackSpeed=input('Playback Speed? ')
def isFloat(arg):
    try:
        float(arg)
        return True
    except ValueError:
        return False
while not(isFloat(playbackSpeed)):
    playbackSpeed=input('Invalid Speed. Playback Speed? ')
y, sr = librosa.load("Test Audio/"+whatFile, mono=False, sr=44100)
l=y[0]
r=y[1]
listAudioL=[x for x in l]
listAudioR=[x for x in r]
p=pyaudio.PyAudio()
stream=p.open(format=p.get_format_from_width(2),rate=sr,channels=2,output=True)
index=0
t=float(playbackSpeed)
while index-1024<len(l):
    try:
        data=[]
        for i in range(int(index),int(index)+1024):
            data.append(int(listAudioL[i]*32767))
            data.append(int(listAudioR[i]*32767))
        bytesData=b''
        for i in range(1024*2):
            bytesData+=pack('h',data[i])
        stream.write(bytesData)
        index+=1024*t
    except Exception:
        index+=1024*t