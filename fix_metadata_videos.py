import json
import subprocess
import os
from pathlib import Path
from datetime import datetime, timezone

MAKE  = "MAKE"
MODEL = "PHONE MODEL"

def fix_video(video_path: Path, json_path: Path):
    with open(json_path) as f:
        json_data = json.load(f)

    ts = int(json_data["photoTakenTime"]["timestamp"])
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    dt_ffmpeg = dt.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    dt_exif   = dt.strftime("%Y:%m:%d %H:%M:%S")

    title       = json_data.get("title", "")
    description = json_data.get("description", "")
    device_type = json_data.get("googlePhotosOrigin", {}).get("mobileUpload", {}).get("deviceType", "")
    latitude    = json_data["geoData"]["latitude"]
    longitude   = json_data["geoData"]["longitude"]
    altitude    = json_data["geoData"]["altitude"]

    tmp_path = video_path.with_suffix(".tmp" + video_path.suffix)

    # Step 1: ffmpeg — embed all metadata
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-movflags", "use_metadata_tags",
        "-metadata", f"creation_time={dt_ffmpeg}",
        "-metadata", f"title={title}",
        "-metadata", f"description={description}",
        "-metadata", f"device={device_type}",
        "-metadata", f"location={latitude},{longitude},{altitude}",
        "-metadata", f"make={MAKE}",
        "-metadata", f"model={MODEL}",
        "-metadata:s:v:0", f"creation_time={dt_ffmpeg}",
        "-metadata:s:a:0", f"creation_time={dt_ffmpeg}",
        "-codec", "copy",
        str(tmp_path), "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr[-200:]}")
        tmp_path.unlink(missing_ok=True)
        return False

    # Step 2: exiftool — fix broken date fields
    cmd2 = [
        "exiftool",
        f"-ModifyDate={dt_exif}",
        f"-TrackCreateDate={dt_exif}",
        f"-TrackModifyDate={dt_exif}",
        f"-MediaCreateDate={dt_exif}",
        f"-MediaModifyDate={dt_exif}",
        "-overwrite_original",
        str(tmp_path)
    ]
    result2 = subprocess.run(cmd2, capture_output=True, text=True)
    if result2.returncode != 0:
        print(f"  Exiftool error: {result2.stderr[-200:]}")
        tmp_path.unlink(missing_ok=True)
        return False

    # Step 3: replace original
    os.replace(tmp_path, video_path)

    # Step 4: fix file system date
    os.utime(video_path, (ts, ts))

    return True


def process_folder(root_folder: str):
    root = Path(root_folder)
    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".3gp"}

    skipped  = []
    success  = []
    failed   = []

    # find all year subfolders
    for year_folder in sorted(root.iterdir()):
    # for year_folder in [root]:
        if not year_folder.is_dir():
            continue

        print(f"\n{'='*50}")
        print(f" Processing: {year_folder.name}")
        print(f"{'='*50}")

        for video_file in sorted(year_folder.iterdir()):
            if video_file.suffix.lower() not in video_extensions:
                continue

            # look for matching JSON (video.mp4.json or video.json)
            json_path = video_file.parent / (video_file.name + ".json")
            if not json_path.exists():
                json_path = video_file.with_suffix(".json")

            if not json_path.exists():
                print(f"  SKIP (no JSON): {video_file.name}")
                skipped.append(str(video_file))
                continue

            print(f"  Fixing: {video_file.name}")
            ok = fix_video(video_file, json_path)
            if ok:
                success.append(str(video_file))
                print(f"  Done ✅")
            else:
                failed.append(str(video_file))
                print(f"  Failed ❌")

    # summary
    print(f"\n{'='*50}")
    print(f" SUMMARY")
    print(f"{'='*50}")
    print(f"  Success : {len(success)}")
    print(f"  Skipped : {len(skipped)}")
    print(f"  Failed  : {len(failed)}")

    if skipped:
        print(f"\nSkipped files (no JSON):")
        for f in skipped:
            print(f"  {f}")

    if failed:
        print(f"\nFailed files:")
        for f in failed:
            print(f"  {f}")

if __name__ == "__main__":
    process_folder("../Photos")  # update to your root folder path