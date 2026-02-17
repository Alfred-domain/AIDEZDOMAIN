import cv2
import numpy as np
from collections import deque
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions
import time
import tkinter as tk

# Screen Centering Setup
root = tk.Tk()
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
root.withdraw()

# screen ratio 
WIDTH, HEIGHT = 800, 600 
center_x = int((screen_w - WIDTH) / 2)
center_y = int((screen_h - HEIGHT) / 2)

#  HandLandmarker setup
base_options = BaseOptions(model_asset_path="hand_landmarker.task")
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    #confidence higher = less confusion
    min_hand_detection_confidence=0.8,
    min_tracking_confidence=0.8,
    running_mode=vision.RunningMode.VIDEO
)
landmarker = vision.HandLandmarker.create_from_options(options)

#  Setup

# color set
colors = [(255, 255, 255), (0, 0, 0), (255, 191, 0), (128, 128, 128)]

# color start up
color_indices = [0, 1] 
all_points = [[ [deque(maxlen=1024)] for _ in range(len(colors)) ] for _ in range(2)]
stroke_indices = [[0]*len(colors), [0]*len(colors)]
cooldowns = [0, 0]

paintWindow = np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8) * 255
cap = cv2.VideoCapture(0)

cv2.namedWindow("Output", cv2.WINDOW_AUTOSIZE)
cv2.namedWindow("Air Canvas", cv2.WINDOW_AUTOSIZE)

cv2.moveWindow("Output", center_x, center_y)
cv2.moveWindow("Air Canvas", center_x, center_y)

# z index for fronting camera
cv2.setWindowProperty("Air Canvas", cv2.WND_PROP_TOPMOST, 1)

def reset_canvas():
    global all_points, stroke_indices, paintWindow
    paintWindow[:, :, :] = 255
    for h in range(2):
        all_points[h] = [[deque(maxlen=1024)] for _ in range(len(colors))]
        stroke_indices[h] = [0]*len(colors)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    #camera ratio when open
    frame = cv2.resize(frame, (WIDTH, HEIGHT))
    frame = cv2.flip(frame, 1)
    
    frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frameRGB)
    hand_result = landmarker.detect_for_video(mp_image, int(time.time() * 1000))

    # DRAW UI
    cv2.rectangle(frame, (330, 10), (470, 65), (0, 0, 255), -1)
    cv2.putText(frame, "CLEAR", (365, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    for i, col in enumerate(colors):
        lx = 20 + (i * 65)
        cv2.rectangle(frame, (lx, 10), (lx + 55, 65), col, -1)
        if i == color_indices[1]: cv2.rectangle(frame, (lx-4, 6), (lx+59, 69), (0, 0, 0), 3)
        
        rx = 520 + (i * 65)
        cv2.rectangle(frame, (rx, 10), (rx + 55, 65), col, -1)
        if i == color_indices[0]: cv2.rectangle(frame, (rx-4, 6), (rx+59, 69), (0, 0, 0), 3)

    if hand_result.hand_landmarks:
        for i, lm in enumerate(hand_result.hand_landmarks):
            label = hand_result.handedness[i][0].category_name
            h_id = 0 if label == "Left" else 1 
            
            # Show dots on hand
            for pt in lm:
                cv2.circle(frame, (int(pt.x * WIDTH), int(pt.y * HEIGHT)), 3, (0, 255, 0), -1)

            curr_c = colors[color_indices[h_id]]
            up = [lm[4].y < lm[3].y, lm[8].y < lm[6].y, lm[12].y < lm[10].y, lm[20].y < lm[18].y]
            ix, iy = int(lm[8].x * WIDTH), int(lm[8].y * HEIGHT)

            # 1. CLEAR use pinky finger
            if up[3] and not up[1]:
                reset_canvas()

            # 2. SELECTION index and middle finger
            elif up[1] and up[2]:
                cv2.circle(frame, (ix, iy), 20, curr_c, 2)
                if iy <= 75:
                    if 330 <= ix <= 470: reset_canvas()
                    elif h_id == 1 and 20 <= ix <= 280: color_indices[1] = (ix - 20) // 65
                    elif h_id == 0 and 520 <= ix <= 780: color_indices[0] = (ix - 520) // 65
                
                # BREAK LINE when selecting
                all_points[h_id][color_indices[h_id]].append(deque(maxlen=1024))
                stroke_indices[h_id][color_indices[h_id]] += 1

            # 3. DRAWING index and thumb
            elif up[1] and up[0] and not up[2]:
                cv2.circle(frame, (ix, iy), 12, curr_c, -1)
                cv2.circle(frame, (ix, iy), 14, (255,255,255), 1)
                c_idx = color_indices[h_id]
                
                # logic for line confusion or jumping line
                if len(all_points[h_id][c_idx][stroke_indices[h_id][c_idx]]) > 0:
                    lp = all_points[h_id][c_idx][stroke_indices[h_id][c_idx]][0]
                    if np.hypot(ix-lp[0], iy-lp[1]) > 60: # Distance threshold
                        all_points[h_id][c_idx].append(deque(maxlen=1024))
                        stroke_indices[h_id][c_idx] += 1
                
                all_points[h_id][c_idx][stroke_indices[h_id][c_idx]].appendleft((ix, iy))

            # 4. COLOR CYCLE Thumb Down
            elif up[1] and not up[0] and not up[2]:
                if time.time() - cooldowns[h_id] > 0.6:
                    color_indices[h_id] = (color_indices[h_id] + 1) % len(colors)
                    cooldowns[h_id] = time.time()
                cv2.circle(frame, (ix, iy), 6, curr_c, 1)

            else:
                # Add a break point to all deques to stop drawing
                for c in range(len(colors)):
                    all_points[h_id][c].append(deque(maxlen=1024))
                    stroke_indices[h_id][c] += 1
    
    # RENDER STROKES
    for h_idx in range(2):
        for c_idx in range(len(colors)):
            for stroke in all_points[h_idx][c_idx]:
                for k in range(1, len(stroke)):
                    if stroke[k-1] is None or stroke[k] is None: continue
                    cv2.line(frame, stroke[k-1], stroke[k], colors[c_idx], 5)
                    cv2.line(paintWindow, stroke[k-1], stroke[k], colors[c_idx], 5)

    
    
    # windows
    cv2.imshow("Output", paintWindow)
    cv2.imshow("Air Canvas", frame)
    # letter q for close program
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()