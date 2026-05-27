import os
import pytz
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Third-party package
from timezonefinder import TimezoneFinder

IST = pytz.timezone("Asia/Kolkata")
EST = pytz.timezone("America/New_York")

def get_timezone(latitude: float, longitude: float):
      # Get timezone from location info from photos. 
      # Fails if photos don't have location info
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=latitude, lng=longitude)
    if tz_name:
        return pytz.timezone(tz_name)
    return timezone.utc  # fallback to UTC if no timezone found

def get_timezone_for_ts(ts: int):
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
      ## Custom mark photos from different dates 
      ## as different timezones if photos don't have location

    if dt.year < 2021:
        return IST

    # 2022: before Jan 1 04:40 IST → IST, rest → EST
    if dt.year == 2021:
        cutoff = datetime(2021, 1, 1, 4, 40, 0, tzinfo=IST)
        return IST if dt < cutoff else EST

    # 2023: Aug 1 2:40 EST to Aug 30 8:05 IST → IST, rest → EST
    if dt.year == 2022:
        ist_start = datetime(2022, 8, 1, 2, 40, 0, tzinfo=EST)  # 19:40 EST
        ist_end   = datetime(2022, 8, 30, 8, 5, 0, tzinfo=IST)  # 8:05 IST
        return IST if ist_start <= dt <= ist_end else EST

    return timezone.utc

def get_exif_dt(ts: int):
    tz = get_timezone_for_ts(ts)
    dt = datetime.fromtimestamp(ts, tz=tz)
    offset = dt.strftime("%z")
    tz_offset = f"{offset[:3]}:{offset[3:]}"
    return dt.strftime(f"%Y:%m:%d %H:%M:%S{tz_offset}")

def fix_screenshot(photo_path: Path, json_path: Path):
    # To fix fake png errors
    if photo_path.suffix.lower() == ".png":
        result = subprocess.run(["file", str(photo_path)], capture_output=True, text=True)
        if "JPEG" in result.stdout:
            new_path = photo_path.with_suffix(".jpg")
            photo_path.rename(new_path)
            photo_path = new_path
            print(f"  Renamed fake PNG → JPG: {photo_path.name}")

    with open(json_path) as f:
        json_data = json.load(f)

    ts = int(json_data["photoTakenTime"]["timestamp"])
    
    ## Skip photos that have already been processed
    current_mtime = int(os.stat(photo_path).st_mtime)
    if current_mtime == ts:
        print(f"  Already processed, skipping")
        return True

    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    dt_exif = dt.strftime("%Y:%m:%d %H:%M:%S00:00")

    # For changing timezone using location info or custom
    # dt_exif = get_exif_dt(ts)
    
    title       = json_data.get("title", "")
    url         = json_data.get("url", "")
    device_type = json_data.get("googlePhotosOrigin", {}).get("mobileUpload", {}).get("deviceType", "")
    app         = json_data.get("appSource", {}).get("androidPackageName", "")

    # device based on date
    # cutoff = datetime(2020, 2, 31, tzinfo=timezone.utc)
    # if dt > cutoff:
    #     make  = "Phone make 1"
    #     model = "Phone model 1"
    # else:
    #     make  = "Phone make 2"
    #     model = "Phone model 2"

    cmd = [
        "exiftool",
        "-m",
        f"-DateTimeOriginal={dt_exif}",
        f"-CreateDate={dt_exif}",
        f"-ModifyDate={dt_exif}",
        f"-Title={title}",
        f"-Comment={url}",
        # f"-Make={make}",
        # f"-Model={model}",
        f"-XPComment={app}",
        "-overwrite_original",
        str(photo_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Error: {result.stderr[-200:]}")
        return False

    # fix file system date
    os.utime(photo_path, (ts, ts))
    return True


def process_screenshots(root_folder: str):
    root = Path(root_folder)

    success = []
    skipped = []
    failed  = []

    for year_folder in sorted(root.iterdir()):
    # for year_folder in [root]:
        if not year_folder.is_dir():
            continue

        print(f"\n{'='*50}")
        print(f" Processing: {year_folder.name}")
        print(f"{'='*50}")

        for photo_file in sorted(year_folder.iterdir()):
            # skip only screenshots
            # if photo_file.name.lower().startswith("screenshot"):
            #     continue
            if photo_file.suffix.lower() not in {".jpg", ".jpeg",".png"}:
                continue

            # find JSON
            json_path = photo_file.with_suffix(".json")                          
            if not json_path.exists():
                json_path = photo_file.parent / (photo_file.stem[:-1] + ".json")
            if not json_path.exists():
                json_path = photo_file.parent / (photo_file.name + ".json")
            if not json_path.exists():
                json_path = photo_file.parent / (photo_file.stem + "..json")      
            if not json_path.exists():
                print(f"  SKIP (no JSON): {photo_file.name}")
                skipped.append(str(photo_file))
                continue

            print(f"  Fixing: {photo_file.name}")
            ok = fix_screenshot(photo_file, json_path)
            if ok:
                success.append(str(photo_file))
                print(f"  Done ✅")
            else:
                failed.append(str(photo_file))
                print(f"  Failed ❌")

    print(f"\n{'='*50}")
    print(f" SUMMARY")
    print(f"{'='*50}")
    print(f"  Success : {len(success)}")
    print(f"  Skipped : {len(skipped)}")
    print(f"  Failed  : {len(failed)}")

    if skipped:
        print(f"\nSkipped (no JSON):")
        for f in skipped: print(f"  {f}")
    if failed:
        print(f"\nFailed:")
        for f in failed: print(f"  {f}")

if __name__ == "__main__":
    ## Process all photo folders in Photos
    process_screenshots("../Photos")

    # Process single photo
    # fix_screenshot(Path("../Photos/Photos from 2021/photo_1.jpg"),   
    #                 Path("../Photos/Photos from 2021/photo_2.jpg.json"))