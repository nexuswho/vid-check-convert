from flask import Flask, request, jsonify, send_file
import os
import subprocess
import uuid

app = Flask(__name__)

TEMP_FOLDER = "temp"


def download_video(video_url, output_path, start=None, end=None):
    if ".m3u8" in video_url or ".m3u" in video_url or ".mpd" in video_url:
        # Construct FFmpeg command for M3U8 playlist
        print("Downloading M3U8 playlist...")
        try:
            ffmpeg_command = f'ffmpeg -protocol_whitelist file,http,https,tcp,tls,crypto -i "{video_url}" -c copy -bsf:a aac_adtstoasc "{output_path}"'
            print(f"FFmpeg command: {ffmpeg_command}")

            result = subprocess.run(
                ffmpeg_command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"Error downloading video: {result.stderr}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"Error downloading video: {e}")
            print(e)
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

            # Trim the video if start and end times are provided
            if start is not None and end is not None:
                ffmpeg_command += f" -ss {start} -to {end} -copyts"

            result = subprocess.run(
                ffmpeg_command, shell=True, check=True, capture_output=True, text=True
            )

            if result.returncode != 0:
                print(f"Error converting video: {result.stderr}")
                return False

            # Remove the temporary file
            os.remove(f"{output_path}.temp")

            return True
        except subprocess.CalledProcessError as e:
            print(f"Error downloading or converting video: {e}")

        # If an error occurred, remove the temporary file if it exists
        if os.path.exists(f"{output_path}.temp"):
            os.remove(f"{output_path}.temp")

        return False


def trim_video(temp_download_path, start, end):
    # Add a standard extension to the temporary trimmed file
    trimmed_temp_file = f"{temp_download_path}.trimmed.mp4"
    start = "00:00:" + start
    end = "00:00:" + end

    print(start, "to ", end)
    # Trim the video using FFmpeg
    ffmpeg_command = f'ffmpeg -ss {start} -to {end} -i "{temp_download_path}" -c copy "{trimmed_temp_file}"'
    print(f"FFmpeg command: {ffmpeg_command}")
    try:
        result = subprocess.run(
            ffmpeg_command, shell=True, check=True, capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"Error trimming video: {result.stderr}")
            return

        print("Trimming successful")
        # Remove the original temporary file
        os.remove(temp_download_path)

        # Rename the trimmed file to the original temporary file name
        os.rename(trimmed_temp_file, temp_download_path)
    except subprocess.CalledProcessError as e:
        print(f"Error trimming video: {e}")


# Rest of your code...


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

    try:
        result = subprocess.run(
            ffmpeg_command, shell=True, check=True, capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"Error converting video: {result.stderr}")
            return False

        print("Conversion successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error converting video: {e}")
        return False


@app.route("/api/convert", methods=["POST"])
def convert_video_api():
    try:
        video_url = request.form["video_url"]

        # Generate a unique filename using uuid
        unique_filename = str(uuid.uuid4()) + ".mp4"

        # Download the video to the temp folder
        temp_download_path = os.path.join(TEMP_FOLDER, unique_filename)

        # Check if 'start' and 'end' fields are present in the API request
        start = request.form.get("start")
        end = request.form.get("end")

        print("Starting download...")
        download_video(video_url, temp_download_path, start, end)
        print("Download successful.")

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
                # Trim the video if start and end times are provided
                if start is not None and end is not None:
                    print("Trimming video...")
                    trim_video(temp_download_path, start, end)
                    print("Trimming successful.")

                print("Converting video...")
                # Convert the video
                if convert_video(
                    temp_download_path, target_width, target_height, unique_filename
                ):
                    print("Conversion successful.")
                else:
                    return jsonify({"converted": False, "success": False, "url": None})

                converted_url = (
                    f"http://vid-nexuswho.koyeb.app/static/{unique_filename}"
                )
            else:
                # Trim the video if start and end times are provided
                if start is not None and end is not None:
                    print("Trimming video...")
                    trim_video(temp_download_path, start, end)
                    print("Trimming successful.")

                # If no conversion is needed, serve the original video
                converted_url = f"http://vid-nexuswho.koyeb.app/temp/{unique_filename}"

            return jsonify({"converted": True, "success": True, "url": converted_url})
        else:
            print("Error running ffprobe.")
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
