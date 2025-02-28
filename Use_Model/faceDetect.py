import numpy as np
import cv2
import os
import torchvision.models as models
import torch.nn as nn
import torch
import torchvision
from torchvision import transforms

from PIL import Image

#directories
base_dir = os.path.dirname(__file__)
prototxt_path = os.path.join(base_dir + r'/model_data/deploy.prototxt')
faceDetect_path = os.path.join(base_dir + r'/model_data/faceDetect.caffemodel')
maskDetect_path = os.path.join(base_dir + r'/model_data/model.pth')

#loading face detection model and mask detection model
print("loading models")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

maskDetectModel = torch.load(maskDetect_path)
model=models.resnet50(pretrained=True)
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, 3)
model.load_state_dict(maskDetectModel)
model.eval()
faceDetectModel = cv2.dnn.readNetFromCaffe(prototxt_path, faceDetect_path)

#device = torch.device('cpu')
#maskDetectModel.to('cpu')
#function to detect face
def detect_face(image):
    (h, w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    faceDetectModel.setInput(blob)
    detections = faceDetectModel.forward()
    faces=[]
    positions=[]
    for i in range(0, detections.shape[2]):
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")
        (startX,startY)=(max(0,startX-15),max(0,startY-15))
        (endX,endY)=(min(w-1,endX+15),min(h-1,endY+15))
        confidence = detections[0, 0, i, 2]
        # If confidence > 0.5, show box around face
        if (confidence > 0.5):
            face = frame[startY:endY, startX:endX]
            faces.append(face)
            positions.append((startX,startY,endX,endY))
    return faces,positions

#function to detect mask
def detect_mask(faces):
    predictions = []
    image_transforms = transforms.Compose([transforms.Resize(size=(244,244)), transforms.ToTensor(),transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    if (len(faces)>0):
        for img in faces:
            img = Image.fromarray(img)
            img = image_transforms(img)
            img = img.unsqueeze(0)
            prob, prediction = torch.max(torch.exp(model(img.to(device))),dim=1)
            #prediction =model(img)
           # print(prediction.item())
            #prediction = prediction.argmax()
            #predictions.append(prediction.data)
            predictions=str(prediction.item())
            #print(predictions)
    return predictions
#video streaming
cap = cv2.VideoCapture(0)
while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()
    # Our operations on the frame come here
    (faces,postions) = detect_face(frame)
    predictions=detect_mask(faces)
    
    for(box,prediction) in zip(postions,predictions):
        (startX, startY, endX, endY) = box
        print(prediction)

        prediction=int(prediction)
        if prediction == 1:
            label="Incorrectly use the mask"
            color = (0, 255, 0)
            cv2.putText(frame, label, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.85, color, 2)
            cv2.rectangle(frame,(startX, startY),(endX, endY),color,2)
        elif prediction==2:
            label="Without Mask"
            color = (0, 0, 255)
            cv2.putText(frame, label, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.rectangle(frame,(startX, startY),(endX, endY),color,1)
        else:
            label="Using correctly  mask"
            color = (0, 255, 0)
       # color = (0, 255, 0) if label == "Mask" else (255,0,0)
            cv2.putText(frame, label, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.rectangle(frame,(startX, startY),(endX, endY),color,1)
    # Display the resulting frame
    cv2.imshow('frame',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()