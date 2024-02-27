import grpc
import tkinter as tk
from tkinter import messagebox
import video_stream_pb2
import video_stream_pb2_grpc
import tempfile
import os
import subprocess


def play_video():
    selected_video = video_listbox.get(tk.ACTIVE)
    if not selected_video:
        messagebox.showwarning("Warning", "No video selected.")
        return

    channel = grpc.insecure_channel('localhost:50051')  # Replace with the server address
    stub = video_stream_pb2_grpc.VideoStreamStub(channel)

    video_request = video_stream_pb2.VideoRequest(name=selected_video)
    video_chunk_responses = stub.StreamVideo(video_request)

    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    temp_file_path = temp_file.name
    temp_file.close()

    with open(temp_file_path, "wb") as f:
        for chunk_response in video_chunk_responses:
            f.write(chunk_response.chunk)

    channel.close()

    subprocess.run(["vlc", temp_file_path])  # Play the video using VLC

    os.remove(temp_file_path)  # Delete the temporary file


def populate_video_list():
    channel = grpc.insecure_channel('localhost:50051')  # Replace with the server address
    stub = video_stream_pb2_grpc.VideoStreamStub(channel)

    video_list_request = video_stream_pb2.VideoListRequest()
    video_list_response = stub.GetVideoList(video_list_request)

    for video in video_list_response.videos:
        video_listbox.insert(tk.END, video.name)

    channel.close()


# Create the GUI window
window = tk.Tk()
window.title("Video Stream Client")

# Create a listbox to display the video list
video_listbox = tk.Listbox(window)
video_listbox.pack(pady=10)

# Button to play the selected video
play_button = tk.Button(window, text="Play", command=play_video)
play_button.pack(pady=5)

# Populate the video list
populate_video_list()

# Start the GUI event loop
window.mainloop()