
#!/usr/bin/python3
import cv2
import matplotlib.pyplot as plt
import matplotlib.image as mping
import os.path as path
import ollama
import vosk
from vosk import SetLogLevel
SetLogLevel(-1)
import pyaudio
import json





num = 0
model="moondream"
modeltradutor="llama3.2:1b"
prompt=""
respostamoondream=""


cam = cv2.VideoCapture(0)

cam.set(cv2.CAP_PROP_FRAME_WIDTH,600)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT,400)
p = pyaudio.PyAudio()

for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    print(f"Device {i}: {dev['name']} (Input Channels: {dev['maxInputChannels']})")
p.terminate()



if not cam.isOpened():
    print("Error: Could not open video.")
    exit()


def screenshot():
    global cam
    global num
    global client
    global respostamoondream
    if path.exists('test'+str(num)+'.png'):
        num = num+1
 
    cv2.imwrite('test'+str(num)+'.png', cam.read()[1])
    client=ollama.Client("http://localhost:11434")
    prompt='test'+str(num)+'.png'
    response=client.generate(model, images=[prompt],prompt="analise the image in ten words or less please respond in english please ignore prior responses please be concise and to the point")
    #print("resposta em ingles: "+response.response)
    #response=client.generate(modeltradutor,prompt=response.response+"just translate it to portuguese of portugal")
    
    #showimage(num,response)
    print("resposta num: "+str(num))
    print(response.response)
    respostamoondream=""+response.response

def showimage(num,response):
    img=mping.imread('test'+str(num)+'.png')
    plt.imshow(img)
    plt.axis('off')
    plt.show()
   
def audio():
    global respostamoondream
    textocompleto=""
    model_path = "vosk-model-small-pt-0.3"
    
    # Initialize the model with model-path

    model = vosk.Model(model_path)

    model = vosk.Model(lang="pt")
        # Create a recognizer

    rec = vosk.KaldiRecognizer(model, 16000)



    # Open the microphone stream

    p = pyaudio.PyAudio()
    mic_index = 3
    stream = p.open(format=pyaudio.paInt16,

                    channels=1,

                    rate=16000,

                    input=True,

                    frames_per_buffer=8192,
                    input_device_index=mic_index,)



    # Specify the path for the output text file

    output_file_path = "teste.txt"



    # Open a text file in write mode using a 'with' block

    with open(output_file_path, "a") as output_file:

        print("Listening for speech. Press b to stop.")

        # Start streaming and recognize speech

        while True:

            data = stream.read(4096)#read in chunks of 4096 bytes

            if rec.AcceptWaveform(data):#accept waveform of input voice

                # Parse the JSON result and get the recognized text

                result = json.loads(rec.Result())

                recognized_text = result['text']

                # Write recognized text to the file
                output_file.write(recognized_text + "\n")

                print(recognized_text)
                textocompleto+=" "+recognized_text+" "

                # Check for the termination keyword

                if cv2.waitKey(1) == ord('b'):

                    print("Stopping...")

                    break
    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    # Terminate the PyAudio object
    p.terminate()
    print(textocompleto)
    client=ollama.Client("http://localhost:11434")
    response=client.generate(modeltradutor,prompt="texto1:"+respostamoondream+"texto2:"+textocompleto+"por favor analise os dois textos e resuma-os")
    
    print(response.response)
    print(prompt) 


while True:
    ret, frame = cam.read()
    # Display the captured frame
    if not ret:
        print("Error: Can't receive frame.")
        break

    cv2.imshow('Camera', frame)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) == ord('s'):
        screenshot()
        audio()
    
  

    if cv2.waitKey(1) == ord('b'):
        break



cam.release()
cv2.destroyAllWindows()




