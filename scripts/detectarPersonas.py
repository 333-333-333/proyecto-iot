from picamera2 import Picamera2
import cv2
import torch
import numpy as np
import time
from datetime import datetime
import json
import paho.mqtt.client as mqtt

THINGSBOARD_HOST = "iot.ceisufro.cl"
ACCESS_TOKEN = "GyimZTJPTB4rJc08ETWM"

client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)
client.connect(THINGSBOARD_HOST, 1883, 60)
client.loop_start()

model = torch.hub.load("ultralytics/yolov5", "yolov5s", trust_repo=True)
model.classes = [0]

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
picam2.start()
time.sleep(1)

cv2.namedWindow("Detección de personas", cv2.WINDOW_NORMAL)

last_sent = time.time()
send_interval = 5

try:
    while True:
        frame = picam2.capture_array()
        results = model(frame)
        detections = results.pred[0]
        people = [det for det in detections if int(det[5]) == 0 and det[4] >= 0.40]
        person_count = len(people)
        avg_conf = round(float(np.mean([det[4] for det in people])) * 100, 2) if people else 0.0
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_time = time.time()

        if person_count > 0 and avg_conf >= 40 and current_time - last_sent >= send_interval:
            payload = {
                "people_detected": person_count,
                "avg_confidence": avg_conf,
                "timestamp": timestamp_str
            }
            client.publish("v1/devices/me/telemetry", json.dumps(payload), qos=1)
            print(f"{timestamp_str} → {payload}")
            last_sent = current_time

        annotated_frame = np.squeeze(results.render())
        resized = cv2.resize(annotated_frame, (640, 480))
        cv2.imshow("Detección de personas", resized)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Detenido por el usuario")

finally:
    client.loop_stop()
    client.disconnect()
    cv2.destroyAllWindows()
    print("Conexión cerrada")
