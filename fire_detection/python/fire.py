from ultralytics import YOLO
import cvzone
import cv2
import time

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FPS, 10)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

model = YOLO("pytorch/best.pt")
model.to("cpu")

classnames = ['fire']

frame_id = 0
last_fire_detected = False
last_conf = 0
last_bbox = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_id += 2

    if frame_id % 3 == 0:
        results = model(frame, imgsz=320, conf=0.5)

        last_fire_detected = False

        for r in results:
            for box in r.boxes:
                conf = int(float(box.conf[0]) * 100)
                cls = int(box.cls[0])

                if conf > 50:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    last_fire_detected = True
                    last_conf = conf
                    last_bbox = (x1, y1, x2, y2)

    if last_fire_detected and last_bbox:
        x1, y1, x2, y2 = last_bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cvzone.putTextRect(
            frame,
            f"fire {last_conf}%",
            (x1, max(35, y1)),
            scale=1,
            thickness=2
        )

    cv2.imshow("Fire Detection", frame)

    if cv2.waitKey(100) & 0xFF == 27: 
        break

cap.release()
cv2.destroyAllWindows()