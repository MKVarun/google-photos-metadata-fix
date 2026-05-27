from pathlib import Path
import subprocess
import json

def extract_photo_metadata(photo_path: str):
    # exiftool - all relevant photo fields
    result = subprocess.run(
        ["exiftool",
         "-DateTimeOriginal", "-CreateDate", "-ModifyDate",
         "-FileModifyDate", "-FileAccessDate",
         "-GPSLatitude", "-GPSLongitude", "-GPSAltitude",
         "-Make", "-Model",
         "-ImageWidth", "-ImageHeight",
         "-Title", "-Comment",
         "-json", photo_path],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)[0]
    data.pop("SourceFile", None)

    print(f"\n=== EXIFTOOL ===")
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    extract_photo_metadata("../Photos/Photos from 2018/Screenshot_2018-01-21-17-12-11-035_com.bsb.hike.jpg")