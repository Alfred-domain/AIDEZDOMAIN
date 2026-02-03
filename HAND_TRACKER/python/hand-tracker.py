import cv2 # import camera
import serial # sending serial to usb wire into C++ esp32 
import time
import mediapipe as mp # for hand
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ---------- SERIAL ----------
try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    time.sleep(2)
    print("Serial connected")
except Exception as e:
    print("Serial failed:", e)
    ser = None

# ---------- MEDIAPIPE ----------
# new syntax for newer version of python 3 (3.12.3 venv)
BaseOptions = python.BaseOptions
HandLandmarker = vision.HandLandmarker
HandLandmarkerOptions = vision.HandLandmarkerOptions
RunningMode = vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="hand_landmarker.task"),
    running_mode=RunningMode.VIDEO,
    num_hands=1
)

detector = HandLandmarker.create_from_options(options)

# ---------- CAMERA ----------
cap = cv2.VideoCapture(0)
timestamp = 0
last_direction = None  # only send when direction changes good for effiency loop

def draw_hand(frame, landmarks):
    h, w, _ = frame.shape
    for lm in landmarks:
        x, y = int(lm.x * w), int(lm.y * h)
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)


# loops
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = detector.detect_for_video(mp_image, timestamp)
    timestamp += 1

    if result.hand_landmarks:
        hand = result.hand_landmarks[0]  # hand landmarks as list 
        draw_hand(frame, hand)  # draw dots this is the pivot dots 

        index_tip = hand[8]
        wrist = hand[0]

        direction = 'U' if index_tip.y < wrist.y else 'D'

        if ser and direction != last_direction:
            ser.write(direction.encode())
            print("Sent:", direction)
            last_direction = direction

        # show command on screen
        # show direction ang status in camera Down or Up
        cv2.putText(frame, f"CMD: {direction}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    else:
        # if no hand, show on screen this will provide status if no hands is visible
        cv2.putText(frame, "No hand detected", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow("Hand Tracker", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
if ser:
    ser.close()
