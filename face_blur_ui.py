import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import os
import shutil
import threading
import datetime
import subprocess

# Setup folders
OUTPUT_FOLDER = "output_videos"
PHOTO_OUTPUT_FOLDER = "blurred_photos"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PHOTO_OUTPUT_FOLDER, exist_ok=True)

# Load face cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# ---- Helper functions ----

def blur_faces_in_image(image_path, output_dir):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    for (x, y, w, h) in faces:
        face = image[y:y+h, x:x+w]
        blurred = cv2.GaussianBlur(face, (99, 99), 30)
        image[y:y+h, x:x+w] = blurred

    filename = os.path.basename(image_path)
    output_path = os.path.join(output_dir, f"blurred_{filename}")
    cv2.imwrite(output_path, image)
    return output_path

def process_photos(photo_paths, progress, status):
    total = len(photo_paths)
    output_dir = os.path.join(os.getcwd(), PHOTO_OUTPUT_FOLDER)
    os.makedirs(output_dir, exist_ok=True)

    for i, path in enumerate(photo_paths, 1):
        blur_faces_in_image(path, output_dir)
        progress["value"] = int((i / total) * 100)
        status.set(f"Processed {i}/{total}")

    messagebox.showinfo("Done", f"Saved all blurred photos to {output_dir}")
    progress["value"] = 0
    status.set("")

def blur_faces_in_video(video_path, progress, status):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        messagebox.showerror("Error", "Cannot open video file.")
        return

    filename = os.path.basename(video_path)
    filename_wo_ext = os.path.splitext(filename)[0]
    output_path = os.path.join(OUTPUT_FOLDER, f"{filename_wo_ext}_blurred.avi")

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, 20.0, (
        int(cap.get(3)), int(cap.get(4))
    ))

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    current_frame = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        for (x, y, w, h) in faces:
            face = frame[y:y+h, x:x+w]
            blurred = cv2.GaussianBlur(face, (99, 99), 30)
            frame[y:y+h, x:x+w] = blurred

        out.write(frame)

        current_frame += 1
        if total_frames:
            progress["value"] = int((current_frame / total_frames) * 100)
            status.set(f"Blurring video... {progress['value']}%")

    cap.release()
    out.release()
    progress["value"] = 0
    status.set("")
    messagebox.showinfo("Done", f"Saved as {output_path}")

def blur_faces_from_webcam(progress, status):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Cannot access webcam.")
        return

    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_FOLDER, f"webcam_blurred_{now}.avi")
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, 20.0, (
        int(cap.get(3)), int(cap.get(4))
    ))

    status.set("Press 'q' to stop webcam")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        for (x, y, w, h) in faces:
            face = frame[y:y+h, x:x+w]
            blurred = cv2.GaussianBlur(face, (99, 99), 30)
            frame[y:y+h, x:x+w] = blurred

        out.write(frame)
        cv2.imshow("Webcam Blur", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    status.set("")
    messagebox.showinfo("Done", f"Saved webcam recording to {output_path}")

def open_video_folder():
    path = os.path.abspath(OUTPUT_FOLDER)
    if os.path.exists(path):
        subprocess.Popen(f'explorer "{path}"')

def open_photo_folder():
    path = os.path.abspath(PHOTO_OUTPUT_FOLDER)
    if os.path.exists(path):
        subprocess.Popen(f'explorer "{path}"')
    else:
        messagebox.showinfo("Info", "No blurred photos found yet.")

# ---- UI Setup ----
root = tk.Tk()
root.title("Face Blur App")
root.geometry("350x300")

status_var = tk.StringVar()

progress = ttk.Progressbar(root, orient="horizontal", length=250, mode="determinate")
progress.pack(pady=10)
tk.Label(root, textvariable=status_var).pack()

tk.Label(root, text="Choose an Option", font=("Helvetica", 14)).pack(pady=10)

def choose_photos():
    paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    if paths:
        threading.Thread(target=process_photos, args=(paths, progress, status_var)).start()

def choose_video():
    path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi")])
    if path:
        threading.Thread(target=blur_faces_in_video, args=(path, progress, status_var)).start()

def start_webcam():
    threading.Thread(target=blur_faces_from_webcam, args=(progress, status_var)).start()

# Blurring Buttons (top 3)
tk.Button(root, text="🖼️ Blur Photos", bg="white", width=30, height=1, command=choose_photos).pack(pady=3)
tk.Button(root, text="🎞️ Blur Video File", bg="white", width=30, height=1, command=choose_video).pack(pady=3)
tk.Button(root, text="📷 Blur Webcam", bg="white", width=30, height=1, command=start_webcam).pack(pady=3)

# Very small gap between blur and folder section
tk.Label(root, text="").pack(pady=5)

# Folder Buttons (bottom 2)
tk.Button(root, text="📂 Open Blurred Photos Folder", bg="white", width=30, height=1, command=open_photo_folder).pack(pady=3)
tk.Button(root, text="📂 Open Blurred Videos Folder", bg="white", width=30, height=1, command=open_video_folder).pack(pady=3)


tk.Label(root, text="Press 'q' to stop webcam or video preview", font=("Arial", 8)).pack(pady=10)

root.mainloop()
