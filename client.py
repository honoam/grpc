import grpc
import tkinter as tk
from tkinter import messagebox
import video_stream_pb2
import video_stream_pb2_grpc
import cv2
import threading

class VideoClient:
    def __init__(self):
        self.channel = grpc.insecure_channel('45.159.197.153:50051')
        self.stub = video_stream_pb2_grpc.VideoStreamStub(self.channel)

        self.root = tk.Tk()
        self.root.title("Video Stream Client")

        self.video_listbox = tk.Listbox(self.root)
        self.video_listbox.pack(pady=10)

        self.play_button = tk.Button(self.root, text="Play", command=self.play_video)
        self.play_button.pack(pady=5)

        self.populate_video_list()

        self.root.mainloop()

    def populate_video_list(self):
        video_list_request = video_stream_pb2.VideoListRequest()
        video_list_response = self.stub.GetVideoList(video_list_request)

        for video in video_list_response:
            self.video_listbox.insert(tk.END, video.name)

    def play_video(self):
        selected_video = self.video_listbox.get(tk.ACTIVE)
        if not selected_video:
            messagebox.showwarning("Warning", "No video selected.")
            return

        rtsp_url = self.get_rtsp_url(selected_video)

        if rtsp_url:
            print(f"RTSP URL for {selected_video}: {rtsp_url}")

            # Start a new thread to display the video stream
            threading.Thread(target=self.display_video, args=(rtsp_url,)).start()

        else:
            messagebox.showwarning("Error", "Failed to retrieve RTSP URL.")

    def get_rtsp_url(self, video_name):
        video_request = video_stream_pb2.VideoRequest(name=video_name)
        rtsp_url_response = self.stub.StreamVideo(video_request)
        return rtsp_url_response.url

    def display_video(self, rtsp_url):
        cap = cv2.VideoCapture(rtsp_url)

        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                break

            cv2.imshow('Video Stream', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        self.channel.close()

if __name__ == "__main__":
    client = VideoClient()
