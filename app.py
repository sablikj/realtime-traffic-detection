import dash
import cv2
import dotenv
import json
import numpy as np
from flask import Flask, Response
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import html, dcc

from layout import layout
from database import *
from utils import *
from detection import detectVehicles, trackVehicles, getRoutesLen


# Params
WIDTH = 1248 # 640
HEIGHT = 704 # 352
USE_DB = True
SHOW_LABELS = True
ALLOWED_CLASSES = ['car', 'bus', 'truck']
FPS = 0

options = {
    "STREAM_RESOLUTION": '480p',
    "STREAM_PARAMS": {"nocheckcertificate": True},
    "CAP_PROP_FPS": 30
}

"""
Class working with video stream.
"""
class VideoStream():
    def __init__(self):
        self.stream = cv2.VideoCapture(os.getenv('CAM_URL'))

    def __del__(self):
        self.stream.stop()

    def getFrame(self):
        ret, img = self.stream.read()
        if ret:
            img = cv2.resize(img, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA)
            return img
        else:
            return None

"""
Main loop for the frame processing.
"""
def run(stream):
    global data, points, frame, FPS
    prevTime = 0
    frameCount = 0
    while True:       
        frame = stream.getFrame()
        frameCount += 1

        if frameCount == 1:            
            cv2.imwrite('./application/resources/canvas_bg.png', frame)

        # Processing every third frame for better performance      
        if frameCount % 3 != 0:
            prevTime = time.time()
            continue

        # Detect vehicles in a frame
        classes, confidences, boxes = detectVehicles(frame, ALLOWED_CLASSES)

        # Track detected vehicles
        frame, data, points = trackVehicles(frame, data, points, classes, confidences, boxes)
         
        # Save data every 5 min (4500 frames at 15 FPS)
        if len(data) > 10 and frameCount % 4500 == 0:
            if USE_DB:
                insert(data, points)
            else:
                saveData(data, points)

            # empty the points df
            points = points[0:0]

        # Encode frame to JPEG 
        _, jpeg = cv2.imencode('.jpg', frame)

        currTime = time.time()
        FPS = 1 / (currTime - prevTime)
        prevTime = currTime  

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')


#############
# Server Init
#############

server = Flask(__name__)
app = dash.Dash("Real-time Traffic Detection", server=server, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], meta_tags=[
                {"name": "viewport", "content": "width=device-width"}], assets_folder='application/assets',suppress_callback_exceptions=True)


@server.route('/video_stream')
def video_stream():
    if os.getenv('CAM_URL') != "":
        return Response(run(VideoStream()), mimetype='multipart/x-mixed-replace; boundary=frame')

app.layout = layout()


##################
# Sidebar elements
##################

# Show polygons switch
@app.callback(
    Output('emptyDiv2', 'children'),
    Input('showPolygons', 'on'))
def polygon_callback(on):
    os.environ['SHOW_POLYGONS'] = str(on)        
    dotenv.set_key(dotenv_file, 'SHOW_POLYGONS', os.environ['SHOW_POLYGONS'])

# Show tracks switch
@app.callback(
    Output('emptyDiv3', 'children'),
    Input('showTracks', 'on'))
def label_callback(on):
    os.environ['SHOW_TRACKS'] = str(on)        
    dotenv.set_key(dotenv_file, 'SHOW_TRACKS', os.environ['SHOW_TRACKS'])

# Use DB switch
@app.callback(
    Output('emptyDiv12', 'children'),
    Input('saveDB', 'on'))
def db_callback(on):
    global USE_DB
    USE_DB = on

# Confidence slider
@app.callback(
    Output('emptyDiv5', 'children'),
    Input('confidenceSlider', 'value'))
def confidence_callback(value):
    os.environ['CONFIDENCE_THRESHOLD'] = str(value)        
    dotenv.set_key(dotenv_file, 'CONFIDENCE_THRESHOLD', os.environ['CONFIDENCE_THRESHOLD'])

# Class select dropdown
@app.callback(
    Output('emptyDiv6', 'children'),
    Input('classSelect', 'value'))
def classes_callback(value):
    global ALLOWED_CLASSES
    ALLOWED_CLASSES = [x.lower() for x in value]

# DATE PICKER
@app.callback(
    Output('emptyDiv1', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'))
def update_output(start_date, end_date):
    if start_date is not None:
        start_date_object = datetime.strptime(start_date, '%Y-%m-%d')

    if end_date is not None:
        end_date_object = datetime.strptime(end_date, '%Y-%m-%d')  

# DOWNLOAD BUTTON
@app.callback(
    Output("download-data", "data"),
    Input("btn-download-data", "n_clicks"),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('download-dropdown', 'value'),
    prevent_initial_call=True,
)
def func(n_clicks,start_date, end_date, value):
    if n_clicks and value in ['Vehicles', 'Points']:
        downData = download(start_date, end_date, value)
        if value == 'Vehicles':
            return dcc.send_data_frame(downData.to_csv, "vehicleData-{0}_{1}.csv".format(start_date, end_date))
        if value == 'Points':
            return dcc.send_data_frame(downData.to_csv, "vehiclePoints-{0}_{1}.csv".format(start_date, end_date))

########
# Modals
########

# SETTINGS MODAL
@app.callback(
    Output("settingsModal", "is_open"),
    [Input("open-settingsModal", "n_clicks"), Input("SettingsModalClose", "n_clicks")],
    [State("settingsModal", "is_open")],
)
def toggle_modal(n_open, n_close, is_open):
    if n_open or n_close:
        return not is_open
    return is_open

# URL INPUT
@app.callback(
    Output('emptyDiv7', 'children'),    
    Input("urlInput", "value"),
)
def update_URLoutput(input1):
    if len(input1) > 10 and ('https://youtu.be' in input1 or 'rtsp://' in input1) and os.getenv('CAM_URL') != input1:        

        os.environ['CAM_URL'] = input1
        dotenv.set_key(dotenv_file, 'CAM_URL', os.environ['CAM_URL'])

# DB SERVER INPUT
@app.callback(
    Output('emptyDiv8', 'children'),    
    Input("serverInput", "value"),
)
def update_ServerOutput(input1):
    if len(input1) > 5 and os.getenv('DB_SERVER') != input1:        

        os.environ['DB_SERVER'] = input1        
        dotenv.set_key(dotenv_file, 'DB_SERVER', os.environ['DB_SERVER'])

# DB NAME INPUT
@app.callback(
    Output('emptyDiv9', 'children'),    
    Input("nameInput", "value"),
)
def update_DatabaseOutput(input1):
    if len(input1) > 5 and os.getenv('DB_DATABASE') != input1:        

        os.environ['DB_DATABASE'] = input1        
        dotenv.set_key(dotenv_file, 'DB_DATABASE', os.environ['DB_DATABASE'])

# DB Username INPUT
@app.callback(
    Output('emptyDiv10', 'children'),    
    Input("usernameInput", "value"),
)
def update_UsernameOutput(input1):
    if len(input1) > 2 and os.getenv('DB_USERNAME') != input1:        

        os.environ['DB_USERNAME'] = input1        
        dotenv.set_key(dotenv_file, 'DB_USERNAME', os.environ['DB_USERNAME'])

# DB Password INPUT
@app.callback(
    Output('emptyDiv11', 'children'),    
    Input("passwordInput", "value"),
)
def update_UsernameOutput(input1):
    if len(input1) > 2 and os.getenv('DB_PASSWORD') != input1:        

        os.environ['DB_PASSWORD'] = input1        
        dotenv.set_key(dotenv_file, 'DB_PASSWORD', os.environ['DB_PASSWORD'])

## POLYGON MODAL
@app.callback(
    Output("polygonModal", "is_open"),
    [Input("open-polygonModal", "n_clicks"), Input("PolygonModalClose", "n_clicks")],
    [State("polygonModal", "is_open")],
)
def toggle_modal(n_open, n_close, is_open):
    if n_open or n_close:
        return not is_open
    return is_open

def path_to_indices(path):
    """From SVG path to numpy array of coordinates, each row being a (row, col) point
    """
    indices_str = [
        el.replace("M", "").replace("Z", "").split(",") for el in path.split("L")
    ]
    return np.rint(np.array(indices_str, dtype=float)).astype(np.int)

# POLYGON ANNOTATIONS
@app.callback(
    Output("annotations-prePoly", "children"),
    Input("fig-poly", "relayoutData"),
    Input('areaInput', 'value'),
    prevent_initial_call=True,
)
def on_new_annotation(relayout_data, areaName):
    if len(areaName) > 0:
        names = areaName.replace(' ', '')
        names = names.split(',')
        areas = {}
        for key in relayout_data:
            if "shapes" in key:
                for i, shape in enumerate(relayout_data['shapes']):
                    data =  tuple(map(tuple, path_to_indices(shape['path'])))
                    data = [(int(x), int(y)) for x, y in data]
                    areas[names[i]] = list(data)

        if len(areas) > 0:
            with open("polygons.json", "r+") as f:
                data = json.load(f)
                data["areas"] = areas
                f.seek(0)  # rewind
                json.dump(data, f)
                f.truncate()  

            os.environ['UPDATE_POLYGONS'] = 'True'                

    return dash.no_update

# Area Clear
@app.callback(
    Output('emptyDiv14', 'children'),
    Input('PolygonModalClear', 'n_clicks'),
    State('PolygonModalClear', 'value')
)
def clear_area(n_clicks, value):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    with open("polygons.json", "r+") as f:
            data = json.load(f)
            data["areas"] = {}
            f.seek(0)  # rewind
            json.dump(data, f)
            f.truncate()

    os.environ['UPDATE_POLYGONS'] = 'True'

# Area Clear alert
@app.callback(
    Output("area-clr", "is_open"),
    [Input("PolygonModalClear", "n_clicks")],
    [State("area-clr", "is_open")],
)
def toggle_alert(n, is_open):
    if n:
        return not is_open
    return is_open   

# MASK MODAL
@app.callback(
    Output("maskModal", "is_open"),
    [Input("open-maskModal", "n_clicks"), Input("MaskModalClose", "n_clicks")],
    [State("maskModal", "is_open")],
)
def toggle_modal(n_open, n_close, is_open):
    if n_open or n_close:
        return not is_open
    return is_open

# MASK ANNOTATIONS
@app.callback(
    Output("annotations-preMask", "children"),
    Input("fig-mask", "relayoutData"),
    prevent_initial_call=True,
)
def on_new_annotation(relayout_data):
    mask = {}
    for key in relayout_data:
        if "shapes" in key:
            for i, shape in enumerate(relayout_data['shapes']):
                data =  tuple(map(tuple, path_to_indices(shape['path'])))
                data = [(int(x), int(y)) for x, y in data]
                mask[i] = data

    if len(mask) > 0:
        with open("polygons.json", "r+") as f:
            data = json.load(f)
            data["mask"] = mask
            f.seek(0)  # rewind
            json.dump(data, f)
            f.truncate()
            
        os.environ['UPDATE_POLYGONS'] = 'True'

    return dash.no_update


# Mask Clear
@app.callback(
    Output('emptyDiv13', 'children'),
    Input('MaskModalClear', 'n_clicks'),
    State('MaskModalClear', 'value')
)
def clear_mask(n_clicks, value):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    with open("polygons.json", "r+") as f:
            data = json.load(f)
            data["mask"] = {}
            f.seek(0)  # rewind
            json.dump(data, f)
            f.truncate()

    os.environ['UPDATE_POLYGONS'] = 'True'

# Mask Clear alert
@app.callback(
    Output("mask-clr", "is_open"),
    [Input("MaskModalClear", "n_clicks")],
    [State("mask-clr", "is_open")],
)
def toggle_alert(n, is_open):
    if n:
        return not is_open
    return is_open  


#####################
# Info and statistics
#####################

# FPS Counter
@app.callback(
  Output('fpsCounter','children'),
  [Input('interval-updating-oneSec','n_intervals')],
  [State('fpsCounter','children')]
)
def updateFPSCounter(n_intervals,old_logs):
    global FPS
    return round(FPS)
 

if __name__ == '__main__':
    global data, points, dotenv_file
    dotenv_file = dotenv.find_dotenv()
    dotenv.load_dotenv(dotenv_file)

    data = []

    if USE_DB:
        data = []
    else:
        data = []
    points = []

    # Possible to add host and port for specific adress -> app.run_server(debug=False,host=127.0.0.1, port=9000)
    app.run_server(debug=False)