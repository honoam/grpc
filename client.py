import grpc
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import video_stream_pb2
import video_stream_pb2_grpc

class VideoStreamClient:
    def __init__(self, channel):
        self.channel = channel
        self.stub = video_stream_pb2_grpc.VideoStreamStub(self.channel)

    def get_video_list(self):
        video_list_request = video_stream_pb2.VideoListRequest()
        video_list_response = self.stub.GetVideoList(video_list_request)
        return [video.name for video in video_list_response]

    def stream_video(self, selected_video):
        video_request = video_stream_pb2.VideoRequest(name=selected_video)
        video_chunks = self.stub.StreamVideo(video_request)
        return video_chunks

class VideoStreamGUI:
    def __init__(self, client):
        self.client = client
        self.window = tk.Tk()
        self.window.title("Video Stream Client")

        self.video_list_var = tk.StringVar(value=self.client.get_video_list())

        self.video_listbox = tk.Listbox(self.window, listvariable=self.video_list_var, width=50)
        self.video_listbox.pack(pady=10)

        self.stream_button = ttk.Button(self.window, text="Stream", command=self.stream_video)
        self.stream_button.pack(pady=5)

    def stream_video(self):
        selected_index = self.video_listbox.curselection()
        if selected_index:
            selected_video = self.video_listbox.get(selected_index)
            video_chunks = self.client.stream_video(selected_video)
            for chunk in video_chunks:
                process_video_chunk(chunk.chunk)
        else:
            messagebox.showwarning("No Video Selected", "Please select a video to stream.")

    def run(self):
        self.window.mainloop()

def process_video_chunk(chunk):
    # Process the video chunk as per your requirement
    # For example, you can write it to a file or display it
    # Here, we are just printing the length of the chunk
    print(f"Received video chunk of length: {len(chunk)}")

if __name__ == '__main__':
    channel = grpc.insecure_channel('localhost:50051')
    client = VideoStreamClient(channel)
    gui = VideoStreamGUI(client)
    gui.run()