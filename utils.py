import cv2
import os
import requests
import pandas as pd
from datetime import datetime

from application.deep_sort import nn_matching
from application.deep_sort.tracker import Tracker
from application.deep_sort.tools import generate_detections as gdet


WIDTH = 1248
HEIGHT = 704

date = datetime.today().strftime("%d-%m-%Y")

"""
Returns initialized YOLOv4 model for vehicle detection and class names.
"""
def initYOLO():
    with open('./application/resources/coco.names', 'rt') as f:
        class_names = f.read().rstrip('\n').split('\n')

    net = cv2.dnn.readNetFromDarknet(
        './application/resources/yolov4.cfg', './application/resources/yolov4.weights')

    # Use GPU if available
    if cv2.cuda.getCudaEnabledDeviceCount() > 0:
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    model = cv2.dnn_DetectionModel(net)
    model.setInputParams(size=(WIDTH, HEIGHT), scale=1/255)

    return model, class_names

"""
Returns initialized Deep SORT tracker and encoder.
"""
def initDeepSort():
    model = './application/resources/mars-small128.pb'
    encoder = gdet.create_box_encoder(model, batch_size=1)
    metric = nn_matching.NearestNeighborDistanceMetric(
        "cosine", matching_threshold=0.5)
    tracker = Tracker(metric)

    return tracker, encoder


"""
Loads locally saved data from the current day.
"""
def loadData():
    try:
        df = pd.read_csv(
            './application/data/{0}.csv'.format(date), sep=';')
        data = df.values.tolist()
        print('Succesfully loaded data from {0}'.format(date))
        return data
    except:
        print('No data found, created an empty list.')
        data = []

    return data


"""
Saves vehicle data and position points to local storage as CSV.
"""
def saveData(data, points):
    # Vehicles
    df = pd.DataFrame(
        data, columns=['ID','Timestamp', 'Class', 'Origin', 'Exit', 'Points'])
    df.to_csv(
        './application/data/vehicles-{0}.csv'.format(date), sep=';')

    # Points
    df = pd.DataFrame(
        points, columns=['X_point', 'Y_point', 'VehicleID'])
    df.to_csv(
        './application/data/points-{0}.csv'.format(date), sep=';')    
        

"""
Returns title of the Youtube livestream if available, otherwise default value.
"""
def getTitle():
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={os.environ['CAM_URL']}&format=json"
        r = requests.get(oembed_url)
    except:
        return "Live view"
    
    if r.status_code == 200:
        result = r.json()        
        return result['title']
    else:
        return "Live view"
