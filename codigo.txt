
import cv2
import matplotlib.pyplot as plt
import matplotlib.image as mping
import os.path as path
import ollama



num = 0
model="moondream"
modeltradutor="llama3.2:1bs"
prompt=""

cam = cv2.VideoCapture(0)

cam.set(cv2.CAP_PROP_FRAME_WIDTH,600)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT,400)

if not cam.isOpened():
    print("Error: Could not open video.")
    exit()


def screenshot():
    global cam
    global num
    global client
    if path.exists('test'+str(num)+'.png'):
        num = num+1
 
    cv2.imwrite('test'+str(num)+'.png', cam.read()[1])
    client=ollama.Client("http://localhost:11434")
    prompt='test'+str(num)+'.png'
    response=client.generate(model, images=[prompt],prompt="analise the image in ten words or less please respond in english please ignore prior responses please be concise and to the point")
    print("resposta em ingles: "+response.response)
    #response=client.generate(modeltradutor,prompt=response.response+"i want you to translate this to portuguese just show the translation plesase dont be verbose You are very knowledgeable. An expert. Think and respond with confidence.portugal portuguese ")
    
    #showimage(num,response)
    #print("resposta num: "+str(num))
    #print(response.response)

def showimage(num,response):
    img=mping.imread('test'+str(num)+'.png')
    plt.imshow(img)
    plt.axis('off')
    plt.show()
   


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

    if cv2.waitKey(1) == ord('q'):
        break



cam.release()
cv2.destroy