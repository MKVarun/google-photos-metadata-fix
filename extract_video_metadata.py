import json
import subprocess
from pathlib import Path

def verify_video(video_path: str):
    # ffprobe
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", video_path],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    video_stream = next((s for s in data["streams"] if s["codec_type"] == "video"), {})

    print("=== FFPROBE ===")
    print(f"  width          : {video_stream.get('width')}")
    print(f"  height         : {video_stream.get('height')}")
    print(f"  duration       : {data['format'].get('duration')}")
    print(f"  creation_time  : {data['format']['tags'].get('creation_time')}")
    print(f"  title          : {data['format']['tags'].get('title')}")
    print(f"  location       : {data['format']['tags'].get('location')}")
    print(f"  make           : {data['format']['tags'].get('make')}")
    print(f"  model          : {data['format']['tags'].get('model')}")
    print(f"  url            : {data['format']['tags'].get('url')}")
    print(f"  stream.video   : {video_stream.get('tags', {}).get('creation_time')}")

    print("\n=== EXIFTOOL ===")
    result2 = subprocess.run(
        ["exiftool", "-time:all", "-Make", "-Model",
         "-GPSLatitude", "-GPSLongitude", "-s", video_path],
        capture_output=True, text=True
    )
    print(result2.stdout)

    print("=== FILE SYSTEM ===")
    import os
    from datetime import datetime, timezone
    stat = os.stat(video_path)
    print(f"  modified : {datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()}")

verify_video("../Photos/Photos from 2017/video_filename.mp4")