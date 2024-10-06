import os
from pytube import YouTube

# Define the path to the file that contains video URLs
url_file = 'video_urls.txt'

# Define the folder name
folder_name = 'downloaded_videos'

# Create the folder if it does not exist
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

# Read the video URLs from the file and download any videos that match the resolution criteria
with open(url_file, 'r') as f:
    video_urls = f.readlines()

for i, video_url in enumerate(video_urls):
    try:
        video = YouTube(video_url.strip())
        video_streams = video.streams.filter(res='1080p')
        if video_streams:
            video_streams.first().download(output_path=folder_name)
            print(f'Downloaded video: {video.title} at 1080p')
            # Remove the URL from the list
            video_urls.pop(i)
        else:
            print(f'Video {video.title} does not have a 1080p stream')
            for stream in video.streams:
                print(f'{stream.resolution} - {stream.mime_type}')
    except:
        print(f'Error downloading video {video_url.strip()}: {sys.exc_info()[0]}')

# Write the remaining URLs back to the file
with open(url_file, 'w') as f:
    for video_url in video_urls:
        f.write(video_url)
