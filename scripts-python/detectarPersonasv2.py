import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import time
import threading
import numpy as np
import json
from datetime import datetime
import paho.mqtt.client as mqtt
import torch

THINGSBOARD_HOST = "iot.ceisufro.cl"
ACCESS_TOKEN = "GyimZTJPTB4rJc08ETWM"
client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)
client.connect(THINGSBOARD_HOST, 1883, 60)
client.loop_start()

model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)
model.classes = [0]

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
picam2.start()
time.sleep(1)

app = Flask(__name__)

latest_frame = None
lock = threading.Lock()
detections_global = []
last_person_count = -1

def detection_thread():
    global latest_frame, detections_global, last_person_count
    while True:
        time.sleep(0.5)
        if latest_frame is None:
            continue
        with lock:
            frame = latest_frame.copy()

        results = model(frame)
        detections = results.pred[0]
        people = [det for det in detections if int(det[5]) == 0 and det[4] >= 0.4]

        with lock:
            detections_global = people.copy()

        count = len(people)
        avg_conf = float(np.mean([det[4] for det in people])) * 100 if people else 0.0

        if count != last_person_count:
            payload = {
                "people_detected": count,
                "avg_confidence": round(avg_conf, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            client.publish("v1/devices/me/telemetry", json.dumps(payload), qos=1)
            print(f"Enviado MQTT → {payload}")
            last_person_count = count

def gen():
    global latest_frame, detections_global
    while True:
        frame = picam2.capture_array()
        with lock:
            latest_frame = frame.copy()
            people = detections_global.copy()

        for det in people:
            x1, y1, x2, y2, conf, cls = det.cpu().numpy()
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{conf*100:.1f}%"
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.putText(frame, f"Personas: {len(people)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.03)

@app.route('/')
def index():
    return "Stream en <a href='/video_feed'>/video_feed</a>"

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    thread = threading.Thread(target=detection_thread, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=5000)
