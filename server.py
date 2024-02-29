import grpc
import os
import glob
import time
from concurrent import futures
import video_stream_pb2
import video_stream_pb2_grpc
import ffmpeg  # Import the ffmpeg module
import tempfile

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
VIDEO_DIR = "C:\\Users\\Administrator\\Desktop\\grpc\\grpc\\videos"


class VideoStreamServicer(video_stream_pb2_grpc.VideoStreamServicer):
    import tempfile

    def StreamVideo(self, request, context):
        video_file_path = os.path.abspath(os.path.join(VIDEO_DIR, request.name))

        if not os.path.exists(video_file_path):
            context.abort(grpc.StatusCode.NOT_FOUND, f"Video file not found: {video_file_path}")

        try:
            # Use ffmpeg-python to encode the video and write to a temporary file
            input_stream = ffmpeg.input(video_file_path)
            temp_file = tempfile.NamedTemporaryFile(suffix=".ts", delete=False)
            temp_file_path = temp_file.name
            temp_file.close()

            ffmpeg_cmd = (
                input_stream
                .output(temp_file_path, format='mpegts', codec='libx264', preset='ultrafast', tune='zerolatency')
                .global_args('-loglevel', 'quiet')
                .global_args('-stats')
                .run_async()
            )
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Error starting FFmpeg process: {e}")
        finally:
            os.chdir(os.path.dirname(os.path.abspath(__file__)))

        try:
            # Read from the temporary file and yield chunks
            with open(temp_file_path, "rb") as temp_file:
                for chunk in iter(lambda: temp_file.read(4096), b""):
                    yield video_stream_pb2.VideoChunk(chunk=chunk)
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Error during video streaming: {e}")
        finally:
            ffmpeg_cmd.wait()  # Wait for FFmpeg to finish (optional, depending on your use case)
            os.remove(temp_file_path)  # Remove the temporary file

    def GetVideoList(self, request, context):
        video_files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
        for video_file in video_files:
            video_name = os.path.basename(video_file)
            yield video_stream_pb2.Video(name=video_name)


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
