import cv2
import mediapipe as mp
import pyautogui
import time
import threading
from PIL import Image, ImageTk
import customtkinter as ctk

def count_fingers(lst, is_left=True):
    cnt = 0
    thresh = (lst.landmark[0].y * 100 - lst.landmark[9].y * 100) / 2
    if (lst.landmark[5].y * 100 - lst.landmark[8].y * 100) > thresh:
        cnt += 1
    if (lst.landmark[9].y * 100 - lst.landmark[12].y * 100) > thresh:
        cnt += 1
    if (lst.landmark[13].y * 100 - lst.landmark[16].y * 100) > thresh:
        cnt += 1
    if (lst.landmark[17].y * 100 - lst.landmark[20].y * 100) > thresh:
        cnt += 1
    if is_left:
        if (lst.landmark[4].x * 100 - lst.landmark[5].x * 100) > 6:
            cnt += 1
    else:
        if (lst.landmark[5].x * 100 - lst.landmark[4].x * 100) > 6:
            cnt += 1
    return cnt

running = True
gesture_enabled = True

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Gesture Media Control")
root.geometry("880x720")

gesture_status = ctk.StringVar(value="Menunggu...")
mode_status = ctk.StringVar(value="Mode: Aktif")

loading_label = ctk.CTkLabel(root, text="Memuat Sistem...", font=("Segoe UI", 20))
loading_bar = ctk.CTkProgressBar(root, orientation="horizontal", width=300)
loading_label.pack(pady=20)
loading_bar.pack()
loading_bar.set(0)

def finish_loading():
    loading_label.destroy()
    loading_bar.destroy()
    build_main_ui()

def animate_loading(i=0):
    if i >= 100:
        finish_loading()
    else:
        loading_bar.set(i / 100)
        root.after(15, lambda: animate_loading(i + 2))

def stop_program():
    global running
    running = False

def toggle_mode():
    global gesture_enabled
    gesture_enabled = not gesture_enabled
    if gesture_enabled:
        mode_status.set("Mode: Aktif")
        toggle_button.configure(text="Nonaktifkan Gesture", fg_color="red")
    else:
        mode_status.set("Mode: Nonaktif")
        toggle_button.configure(text="Aktifkan Gesture", fg_color="green")

def build_main_ui():
    global video_label, status_label, mode_label, toggle_button, exit_button

    content_frame = ctk.CTkFrame(root)
    content_frame.pack(padx=10, pady=10, fill="both", expand=True)

    left_frame = ctk.CTkFrame(content_frame)
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

    video_label = ctk.CTkLabel(left_frame, text="", width=640, height=480, corner_radius=10)
    video_label.pack(pady=10)

    status_label = ctk.CTkLabel(left_frame, textvariable=gesture_status, font=("Segoe UI", 16), text_color="white")
    status_label.pack(pady=5)

    mode_label = ctk.CTkLabel(left_frame, textvariable=mode_status, font=("Segoe UI", 13), text_color="lightgreen")
    mode_label.pack(pady=5)

    toggle_button = ctk.CTkButton(left_frame, text="Nonaktifkan Gesture", command=toggle_mode,
                                  fg_color="red", hover_color="#cc0000", corner_radius=20, width=250)
    toggle_button.pack(pady=10)

    exit_button = ctk.CTkButton(left_frame, text="Keluar", command=stop_program,
                                fg_color="gray", hover_color="darkgray", corner_radius=20, width=250)
    exit_button.pack(pady=5)

    right_frame = ctk.CTkFrame(content_frame, corner_radius=15, fg_color="#1e1e1e")
    right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

    instruction_title = ctk.CTkLabel(right_frame, text="Petunjuk Penggunaan", font=("Segoe UI", 16, "bold"),
                                     text_color="#ffffff", anchor="w")
    instruction_title.pack(pady=(15, 5), padx=15, anchor="nw")

    usage_text = """\
0 Jari  : Mengepal (siap)
1 Jari  : Next
2 Jari  : Previous
3 Jari  : Volume Naik (tahan)
4 Jari  : Volume Turun (tahan)
5 Jari  : Play / Pause
Kepal 2 tangan (2x): Toggle Aktif/Nonaktif Gesture
"""
    usage_label = ctk.CTkLabel(right_frame, text=usage_text, font=("Segoe UI", 13),
                               justify="left", text_color="#dddddd", anchor="nw")
    usage_label.pack(pady=(0, 15), padx=20, anchor="nw")

    threading.Thread(target=gesture_loop, daemon=True).start()

def gesture_loop():
    global running, gesture_enabled

    cap = cv2.VideoCapture(0)
    mp_hands = mp.solutions.hands
    drawing = mp.solutions.drawing_utils
    hand_obj = mp_hands.Hands(max_num_hands=2)

    ready_for_action = False
    prev_cnt = -1
    last_volume_time = time.time()
    prev_both_fist = False  # Toggle detection tracker

    while running:
        current_time = time.time()
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hand_obj.process(rgb)

        hand_counts = {}
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, hand_handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                hand_label = hand_handedness.classification[0].label
                is_left = (hand_label == "Left")
                cnt = count_fingers(hand_landmarks, is_left=is_left)
                hand_counts[hand_label] = cnt

                gesture_status.set(f"Tangan {hand_label.upper()}: {cnt} jari")

                if gesture_enabled:
                    if cnt == 0:
                        ready_for_action = True
                        prev_cnt = -1
                    elif ready_for_action:
                        if cnt == 1 and prev_cnt != cnt:
                            pyautogui.press("right")
                            gesture_status.set(f"Next ({hand_label})")
                            prev_cnt = cnt
                            ready_for_action = False
                        elif cnt == 2 and prev_cnt != cnt:
                            pyautogui.press("left")
                            gesture_status.set(f"Previous ({hand_label})")
                            prev_cnt = cnt
                            ready_for_action = False
                        elif cnt == 5 and prev_cnt != cnt:
                            pyautogui.press("space")
                            gesture_status.set(f"Play / Pause ({hand_label})")
                            prev_cnt = cnt
                            ready_for_action = False
                        elif cnt == 3:
                            if (current_time - last_volume_time) > 0.2:
                                pyautogui.press("volumeup")
                                gesture_status.set(f"Volume Up ({hand_label})")
                                last_volume_time = current_time
                            prev_cnt = cnt
                        elif cnt == 4:
                            if (current_time - last_volume_time) > 0.2:
                                pyautogui.press("volumedown")
                                gesture_status.set(f"Volume Down ({hand_label})")
                                last_volume_time = current_time
                            prev_cnt = cnt

                drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Toggle gesture mode via double fist
            both_fist = hand_counts.get("Left") == 0 and hand_counts.get("Right") == 0
            if both_fist and not prev_both_fist:
                gesture_enabled = not gesture_enabled
                mode_status.set("Mode: Aktif" if gesture_enabled else "Mode: Nonaktif")
                toggle_button.configure(
                    text="Nonaktifkan Gesture" if gesture_enabled else "Aktifkan Gesture",
                    fg_color="red" if gesture_enabled else "green"
                )
                gesture_status.set("Gesture " + ("diaktifkan" if gesture_enabled else "dinonaktifkan") + " (2 kepal toggle)")
            prev_both_fist = both_fist

        else:
            gesture_status.set("Tidak Terdeteksi")

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.configure(image=imgtk)
        video_label.image = imgtk

    cap.release()
    root.quit()

animate_loading()
root.mainloop()
