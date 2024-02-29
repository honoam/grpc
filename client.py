import grpc
import tkinter as tk
from tkinter import messagebox
import video_stream_pb2
import video_stream_pb2_grpc
import cv2
import numpy as np

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def play_video():
    selected_video = video_listbox.get(tk.ACTIVE)
    if not selected_video:
        messagebox.showwarning("Warning", "No video selected.")
        return

    channel = grpc.insecure_channel('localhost:50051')
    stub = video_stream_pb2_grpc.VideoStreamStub(channel)

    video_request = video_stream_pb2.VideoRequest(name=selected_video)

    try:
        video_chunk_responses = stub.StreamVideo(video_request)

        cv2.namedWindow("Video Stream", cv2.WINDOW_NORMAL)

        for chunk_response in video_chunk_responses:
            frame_data = np.frombuffer(chunk_response.chunk, dtype=np.uint8)
            frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)

            # Check if the frame is valid
            if frame is not None and frame.size[0] > 0 and frame.size[1] > 0:
                cv2.imshow("Video Stream", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("Invalid frame received.")

        cv2.destroyAllWindows()

    except grpc.RpcError as rpc_error:
        print(f"Error during video streaming: {rpc_error}")
        print(f"Debug error string: {rpc_error.debug_error_string}")

    finally:
        channel.close()


def populate_video_list():
    channel = grpc.insecure_channel('localhost:50051')  # Replace with the server address
    stub = video_stream_pb2_grpc.VideoStreamStub(channel)

    video_list_request = video_stream_pb2.VideoListRequest()
    video_list_response = stub.GetVideoList(video_list_request)

    for video in video_list_response:
        video_listbox.insert(tk.END, video.name)

    channel.close()


# Create the GUI window
window = tk.Tk()
window.title("Video Stream")

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
