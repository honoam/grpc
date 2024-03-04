import grpc
import os
import glob
import time
from concurrent import futures
import video_stream_pb2
import video_stream_pb2_grpc
import subprocess

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
VIDEO_DIR = os.getenv("VIDEO_DIR", "/apps/videos")

class VideoStreamServicer(video_stream_pb2_grpc.VideoStreamServicer):
    
    def StreamVideo(self, request, context):
        video_file_path = os.path.join(os.path.abspath(VIDEO_DIR), request.name)

        if not os.path.exists(video_file_path):
            context.abort(grpc.StatusCode.NOT_FOUND, f"Video file not found: {video_file_path}")

        try:
            # Construct FFmpeg command
            rtsp_url = f"rtsp://45.159.197.153:8554/{request.name}"
            self.start_rtsp_server(video_file_path, rtsp_url)

            # Wait for the RTSP server to be ready
            time.sleep(2)

            # Return the RTSP URL to the client
            return video_stream_pb2.VideoUrl(url=rtsp_url)

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Exception during video streaming: {e}")

    def get_video_codec(self, video_file_path):
        ffprobe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name',
            '-of', 'json',
            video_file_path
        ]

        result = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result)
        return None

    def GetVideoList(self, request, context):
        video_files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
        print("Video Files:", video_files)
        for video_file in video_files:
            video_name = os.path.basename(video_file)
            yield video_stream_pb2.Video(name=video_name)

    def start_rtsp_server(self, video_file_path, rtsp_url):
        # print(video_file_path)
        # self.get_video_codec(video_file_path)
        ffmpeg_cmd = [
            'ffmpeg',
            '-re',
            '-stream_loop', '-1',  # Loop the input indefinitely
            '-i', video_file_path,
            '-c:v', 'h264',  # Copy video codec
            '-c:a', 'aac',
            '-f', 'rtsp',
            '-rtsp_transport', 'tcp',  # Use TCP transport for RTSP
            rtsp_url
        ]
        process =  subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
        out, err = process.communicate()
        print("FFmpeg Process Output:", out.decode('utf-8'))
        print("FFmpeg Process Errors:", err.decode('utf-8'))


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
