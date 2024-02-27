# server.py
import grpc
import os
import glob
import time
from concurrent import futures
import video_stream_pb2
import video_stream_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
VIDEO_DIR = "videos"  # Update this with the folder path containing the MP4 files


class VideoStreamServicer(video_stream_pb2_grpc.VideoStreamServicer):
    def GetVideoList(self, request, context):
        video_files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
        for video_file in video_files:
            video_name = os.path.basename(video_file)
            yield video_stream_pb2.Video(name=video_name)

    def StreamVideo(self, request, context):
        video_file_path = os.path.join(VIDEO_DIR, request.name)
        with open(video_file_path, "rb") as video_file:
            for chunk in iter(lambda: video_file.read(4096), b""):
                yield video_stream_pb2.VideoChunk(chunk=chunk)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    video_stream_pb2_grpc.add_VideoStreamServicer_to_server(VideoStreamServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()

    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()