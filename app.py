from flask import Flask, request, jsonify, send_file
import os
import subprocess
import uuid

app = Flask(__name__)

TEMP_FOLDER = "temp"


# def download_video(video_url, output_path):
#     # Use aria2c to download the video
#     aria2c_opts = [
#         "aria2c",
#         video_url,
#         "--out",
#         output_path + ".temp",  # Download with a temporary file extension
#     ]

#     try:
#         subprocess.run(aria2c_opts, check=True)

#         # Use ffmpeg to convert the downloaded video to the desired output path
#         ffmpeg_command = f'ffmpeg -i "{output_path}.temp" -c:v libx264 -c:a aac -strict -2 "{output_path}"'
#         subprocess.run(ffmpeg_command, shell=True, check=True)

#         # Remove the temporary file
#         os.remove(f"{output_path}.temp")

#         return True
#     except subprocess.CalledProcessError as e:
#         print(f"Error downloading or converting video: {e}")

#     # If an error occurred, remove the temporary file if it exists
#     if os.path.exists(f"{output_path}.temp"):
#         os.remove(f"{output_path}.temp")

#     return False

import os
import subprocess


def download_video(video_url, output_path):
    if ".m3u8" in video_url:
        # Construct FFmpeg command for M3U8 playlist
        ffmpeg_command = (
            f'ffmpeg -i "{video_url}" -c copy -bsf:a aac_adtstoasc "{output_path}"'
        )

        try:
            subprocess.run(ffmpeg_command, shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error converting M3U8 to MP4: {e}")
            return False
    else:
        # Use aria2c to download the video
        aria2c_opts = [
            "aria2c",
            video_url,
            "--out",
            output_path + ".temp",  # Download with a temporary file extension
        ]

        try:
            subprocess.run(aria2c_opts, check=True)

            # Use ffmpeg to convert the downloaded video to the desired output path
            ffmpeg_command = f'ffmpeg -i "{output_path}.temp" -c:v libx264 -c:a aac -strict -2 "{output_path}"'
            subprocess.run(ffmpeg_command, shell=True, check=True)

            # Remove the temporary file
            os.remove(f"{output_path}.temp")

            return True
        except subprocess.CalledProcessError as e:
            print(f"Error downloading or converting video: {e}")

        # If an error occurred, remove the temporary file if it exists
        if os.path.exists(f"{output_path}.temp"):
            os.remove(f"{output_path}.temp")

        return False


def print_video_info(video_url):
    print(f"Video URL: {video_url}")
    print("Video Information:")
    subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,width,height",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video_url,
        ]
    )


def convert_video(temp_download_path, target_width, target_height, unique_filename):
    # Convert the video to 9/16
    ffmpeg_command = f'ffmpeg -i {temp_download_path} -vf "scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:-1:-1:color=black" static/{unique_filename}'

    subprocess.run(ffmpeg_command, shell=True)


@app.route("/api/convert", methods=["POST"])
def convert_video_api():
    try:
        video_url = request.form["video_url"]

        # Generate a unique filename using uuid
        unique_filename = str(uuid.uuid4()) + ".mp4"

        # Download the video to the temp folder
        temp_download_path = os.path.join(TEMP_FOLDER, unique_filename)
        if download_video(video_url, temp_download_path):
            # Print video information
            print_video_info(temp_download_path)

            # Check if the video needs conversion
            target_width = 720
            target_height = int(target_width * 16 / 9)
            ffprobe_command = f"ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 {temp_download_path}"
            result = subprocess.run(
                ffprobe_command, shell=True, capture_output=True, text=True
            )

            if result.returncode == 0:
                width, height = map(int, result.stdout.strip().split(","))
                if width / height != 9 / 16:
                    # Convert the video
                    convert_video(
                        temp_download_path, target_width, target_height, unique_filename
                    )
                    converted_url = (
                        f"http://vid-nexuswho.koyeb.app/static/{unique_filename}"
                    )
                else:
                    # If no conversion is needed, serve the original video
                    converted_url = (
                        f"http://vid-nexuswho.koyeb.app/temp/{unique_filename}"
                    )

                return jsonify(
                    {"converted": True, "success": True, "url": converted_url}
                )
            else:
                print("Error running ffprobe.")
                return jsonify({"converted": False, "success": False, "url": None})
        else:
            return jsonify({"converted": False, "success": False, "url": None})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"converted": False, "success": False, "url": None})


# Serve files from the temp folder
@app.route("/temp/<filename>")
def serve_temp_file(filename):
    return send_file(os.path.join(TEMP_FOLDER, filename), as_attachment=True)


# Run the app
if __name__ == "__main__":
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
