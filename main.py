import os, string, random, io, subprocess, time
from google.cloud import vision

global ffmpegPr
global arecordPr

def startRecording(fileID):
    # Start FFMPEG and ARECORD
    cmd = ["ffmpeg", "-hide_banner","-loglevel", "panic", "-f","v4l2", "-framerate","30", "-video_size","640x480", "-i","/dev/video2", fileID +".mp4"]
    ffmpegPr = subprocess.Popen(cmd).pid
    print("Recording video.")
    cmd = ["arecord", "-D","hw:3,0", "-f","S16_LE", "-r","41000", "-c","1", fileID + ".wav"]
    arecordPr = subprocess.Popen(cmd).pid
    print("Recording audio")

def stopRecording():
    #stop ffmpeg and that
    os.system("pkill arecord")
    os.system("pkill ffmpeg")
    print("Recording stopped.")

def encodeVideo(fileID):
    print("Encoding video, please wait...")
    subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'panic', '-i', fileID +'.mp4', '-i', fileID +'.wav', '-c:v', 'copy', '-c:a', 'aac', fileID +' complete.mp4'])

def detect_text(path):
    print("I am here!")
    client = vision.ImageAnnotatorClient.from_service_account_json(
        '/home/ed/gcloudcred.json')

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print("I am here 2")
    print('Texts:')

    return texts[0].description

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

def getDateInfoStartOfTape():
    # Used to get date info at the start of a tape
    key = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)]) # random string
    print("Capturing frame")
    os.system("ffmpeg -f v4l2 -framerate 30 -video_size 640x480 -t 1 -i /dev/video2 "+ key +".mp4") # capture 1 sec of video, has to be done to establish resolution
    os.system("ffmpeg -i "+ key +".mp4 -ss 00:00:00.500 -vframes 1 "+ key +".png") # grab freezefram

    print("Running OCR")
    os.system("convert -colorspace gray -fill white -negate "+ key +".png "+ key +".jpg") # Convert to a black and white image
    dateStr = detect_text(key +".jpg")
    # Clean up
    os.remove(key + ".jpg")
    os.remove(key + ".png")
    os.remove(key + ".mp4")
    print("\n\n\n\n\n") # add a break
    return dateStr

def processDateStr(dateStr):
    # used to process ocr string
    dateInfo = dateStr.replace("S", "5").split("\n")[0].split(" ")
    if len(dateInfo) < 3:
        # Not all data is here
        return "NODATA" # exit
    else:
        print(dateStr)
        # we can continue
        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        year = dateInfo[2]
        month = months[int(dateInfo[1])]
        day = dateInfo[0]
        print("Year: "+ year)
        print("Month: "+ month)
        print("Day: "+ day)
        timeInfo = dateStr.replace("S", "5").split("\n")[1].split(":")
        print("Time: "+ timeInfo[0] + ":" + timeInfo[1])
        return day + "/" + month + "/" + year + "/" + timeInfo[0] + ":" + timeInfo[1]

while True:
    print("""
Welcome.
You are now starting a new tape.

REWIND TO THE START, press play until the start of first clip and press STOP. Ensure date is visible and press ENTER.
    """)
    input()
    #try:
    initResult = processDateStr(getDateInfoStartOfTape())
    #except:
    #    print("OCR failed.")
     #   initResult = "NODATA"
    
    if (initResult == "NODATA"):
        # failed
        print("!!! The tape wasn't parsed. Ensure it is on a blue screen, i.e you pushed STOP. !!!")
        # loop back round
    else:
        # we good
        dateInfo = initResult.split("/")
        print("----------READY----------")
        print("Tape Beggining "+ dateInfo[3] + " on the "+ dateInfo[0] + " " + dateInfo[1] + " " + dateInfo[2])
        print("\n\n READY TO RECORD. Press ENTER then hit play immediately.")
        input()
        # Real recording now
        startRecording("Tape "+ dateInfo[3] + " on the "+ dateInfo[0] + " " + dateInfo[1] + " " + dateInfo[2]) # post process on other comp
        print("RECORDING. Push CTRL-C to stop.")
        try:
            time.sleep(3800) # wait one hour and a bit as it is minidv tape length
        except:
            print("recording ended.")
        stopRecording()
        time.sleep(2)
        encodeVideo("Tape "+ dateInfo[3] + " on the "+ dateInfo[0] + " " + dateInfo[1] + " " + dateInfo[2]) # join video and audio together
        print("TAPE COMPLETE. INSERT NEW TAPE AND PRESS ENTER.")
        input()