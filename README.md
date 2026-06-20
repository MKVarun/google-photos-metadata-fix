# Google Photos Metadata Fixer
A Python utility to restore accurate EXIF metadata for Google Photos (photos and videos) using their accompanying JSON files. Currently, when you export photos from Google Photos Takeout, the photos and videos have a date modified as 1 Jan 1980. The correct timestamps are stored in json file. This repo merges the metadata from the JSON files into the media files.

## Features
- Photos Metadata Injection: Writes DateTimeOriginal, CreateDate, ModifyDate, Title, and comments using exiftool.
- Video Metadata Injection: Uses ffmpeg for stream-level metadata and exiftool for container/date fields.
- Batch Processing: Iterates through year-based folder structures.
- Format Correction: Detects and renames "fake PNG" files to .jpg.
- Geolocation Embedding: Writes GPS coordinates (lat/long/altitude) from JSON.

## Requirements
- `Python 3.x`
- `pytz`
- `timezonefinder`
- `exiftool`
- `ffmpeg`

## Usage
Ensure your directory structure as follows:
```
../Photos/
├── 2021/
│   ├── photo.jpg
│   └── photo.jpg.json
├── 2022/
│   └── ...

```
Run the script for fixing photos' metadata
```
python fix_metadata_photos.py
```

Run the script for fixing videos' metadata
```
python fix_metadata_videos.py
```

## Configuration

Change the following lines in `__main__` function to match your root folder.

For photos: `process_screenshots('root_folder_path')`

For videos: `process_folder('root_folder_path')`

Edit `get_timezone_for_ts()` to adjust custom timezone cutoffs for specific years.

## Output

Prints a summary of successful, skipped, and failed files upon completion. Original files are modified in-place.

<img width="578" height="646" alt="output" src="https://github.com/user-attachments/assets/67e8a1d3-7445-4b68-9f37-b40dd46ab412" />
