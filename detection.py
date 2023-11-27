import os
import cv2
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

from application.deep_sort.detection import Detection
from database import getLastID
from utils import initYOLO, initDeepSort

vID = None
mask = None
routes = None
model, class_names = initYOLO()
tracker, encoder = initDeepSort()


def getPolygons():
    global mask, routes
    try:
        with open('polygons.json', 'r') as f:
            polygons = json.load(f)

            return polygons['mask'], polygons['areas']
    except:
        print('Error while reading polygons file!')
        exit()


def getRoutesLen():
    global mask, routes
    if routes is None:
        mask, routes = getPolygons()

    return len(routes)


# initialize color map
cmap = plt.get_cmap('tab20b')
colors = [cmap(i)[:3] for i in np.linspace(0, 1, 20)]

"""
Detects vehicles in a frame using YOLOv4 model.
"""


def detectVehicles(frame, ALLOWED_CLASSES):
    global model, class_names, tracker, encoder, vID, mask, routes

    if mask is None or routes is None or os.getenv('UPDATE_POLYGONS') == 'True':
        mask, routes = getPolygons()
        os.environ['UPDATE_POLYGONS'] = 'False'

        # Apply mask
    frame_masked = frame.copy()
    if len(mask) > 0:
        for name, poly in mask.items():
            cv2.fillPoly(frame_masked, [np.array(poly, np.int32)], (0, 0, 0))

    # OBJECT DETECTION
    classes, confidences, boxes = model.detect(
        frame_masked, confThreshold=float(os.getenv('CONFIDENCE_THRESHOLD')), nmsThreshold=0.4)

    # Boxes filtering - Passsing only specific classes to tracker
    filtered_boxes = []
    filtered_classes = []
    filtered_confidences = []
    for i in range(len(boxes)):
        if class_names[int(classes[i])] in ALLOWED_CLASSES:
            filtered_boxes.append(boxes[i])
            filtered_classes.append(class_names[int(classes[i])])
            filtered_confidences.append(confidences[i])
    filtered_classes = np.array(filtered_classes)  # ?
    filtered_boxes = np.array(filtered_boxes)
    filtered_confidences = np.array(filtered_confidences)

    return filtered_classes, confidences, filtered_boxes


"""
Tracks vehicles based on data from detectVehicle function.
"""


def trackVehicles(frame, data, points, classes, confidences, boxes):
    global vID
    features = encoder(frame, boxes)

    # creating Detection objs for tracking
    detections = [Detection(bbox, score, class_name, feature) for bbox, score,
    class_name, feature in zip(boxes, confidences, classes, features)]

    # Call the tracker
    tracker.predict()
    tracker.update(detections)

    for track in tracker.tracks:
        if not track.is_confirmed() or track.time_since_update > 1 or track.counted:
            continue

        box = track.to_tlbr().astype('int32')
        left, top, width, height = box

        color = colors[int(track.track_id) % len(colors)]
        color = [i * 255 for i in color]

        # Center point of the obj
        cx = int((left + width) / 2)
        cy = int((top + height) / 2)

        # Center of the object
        cv2.circle(frame, (cx, cy), 5, color, -1)

        cv2.putText(frame, track.get_class().capitalize(), (cx - 10, cy - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Tracking line - last 10 points
        if os.environ['SHOW_TRACKS'] == 'True' and len(track.points) > 3:
            pts = []
            i = 0
            while len(pts) < 10 and i < len(track.points):
                if track.points[i] not in pts:
                    pts.append(track.points[i])
                i += 1

            if len(pts) > 3:
                cv2.polylines(frame, [np.array(pts, np.int32)], False, color, 2)

        # COUNTING | 1 (inside), -1 (outside), or 0 (on an edge)
        if not track.counted:
            # Save obj position in current frame
            track.points.append((cx, cy))

            # Using detection areas
            if len(routes) > 0:
                for name, poly in routes.items():

                    # Test if obj is in polygon
                    result = cv2.pointPolygonTest(
                        np.array(poly, np.int32), (int(cx), int(cy)), False)

                    if result >= 0 and track.origin is None:
                        track.origin = name
                        break

                    if result >= 0 and track.origin is not None and name != track.origin:
                        track.exit = name

                        # Manually increasing VehicleID
                        #if vID == None:
                        #    if len(data) != 0:
                        #        vID = data['VehicleID'].max() + 1
                        #    else:
                        #        vID = getLastID() + 1
                        #else:
                        #    vID += 1

                        if vID is None:
                            if len(data) != 0:
                                vID = max(d['VehicleID'] for d in data) + 1
                            else:
                                vID = getLastID() + 1
                        else:
                            vID += 1

                        # Add vehicle data to list
                        new_data = {
                            'VehicleID': vID,
                            'Class': track.get_class(),
                            'IntersectionOrigin': track.origin,
                            'IntersectionExit': track.exit,
                            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        data.append(new_data)
                        #data = data.append(
                        #    {'VehicleID': vID, 'Class': track.get_class(), 'IntersectionOrigin': track.origin,
                        #     'IntersectionExit': track.exit, 'Timestamp': datetime.now().strftime(
                        #        "%Y-%m-%d %H:%M:%S")}, ignore_index=True)

                        # Add vehicle points to separate dataframe
                        #pointsDF = pd.DataFrame(track.points, columns=['X_point', 'Y_point'])
                        #pointsDF['VehicleID'] = vID
                        #points = pd.concat([points, pointsDF], ignore_index=True)
                        for point in track.points:
                            new_point = {
                                'X_point': point[0],
                                'Y_point': point[1],
                                'VehicleID': vID
                            }
                            points.append(new_point)

                        track.counted = True

                        print('{0} #{1} came from {2} and went to {3}. Pos. points: {4}'.format(
                            track.get_class().capitalize(), str(track.track_id), track.origin, track.exit,
                            track.points))
                        break

            # Not using detection areas          
            else:
                # Manually increasing VehicleID
                #if vID == None:
                #    if len(data) != 0:
                #        vID = data['VehicleID'].max() + 1
                #    else:
                #        vID = getLastID() + 1
                #else:
                #    vID += 1
                if vID is None:
                    if len(data) != 0:
                        vID = max(d['VehicleID'] for d in data) + 1
                    else:
                        vID = getLastID() + 1
                else:
                    vID += 1

                    #data = data.append({'VehicleID': vID, 'Class': track.get_class(), 'IntersectionOrigin': 'None',
                    #                    'IntersectionExit': 'None', 'Timestamp': datetime.now().strftime(
                    #        "%Y-%m-%d %H:%M:%S")}, ignore_index=True)
                    new_data = {
                        'VehicleID': vID,
                        'Class': track.get_class(),
                        'IntersectionOrigin': track.origin,
                        'IntersectionExit': track.exit,
                        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    data.append(new_data)

                    # Add vehicle points to separate dataframe
                    #pointsDF = pd.DataFrame(track.points, columns=['X_point', 'Y_point'])
                    #pointsDF['VehicleID'] = vID
                    #points = pd.concat([points, pointsDF], ignore_index=True)
                    for point in track.points:
                        new_point = {
                            'X_point': point[0],
                            'Y_point': point[1],
                            'VehicleID': vID
                        }
                        points.append(new_point)

                    track.counted = True

    # Show polygons
    if os.getenv('SHOW_POLYGONS') == 'True':
        if routes is not None:
            for poly in routes:
                cv2.polylines(frame, [np.array(routes[poly], np.int32)],
                              True, (255, 0, 255), 2)

    return frame, data, points
