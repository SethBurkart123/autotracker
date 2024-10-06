import torch
import cv2
import os

# load the YOLOv5 object detection model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

# set the minimum confidence score
min_confidence = 0.5

# specify the directory containing the videos
video_directory = '../AutoDownloadVid/downloaded_videos/'

# create the output directory if it doesn't exist
output_directory = 'output_frames'
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# loop through all the video files in the directory
for filename in os.listdir(video_directory):
    if filename.endswith('.mp4'):
        video_file = os.path.join(video_directory, filename)

        # open the video file
        cap = cv2.VideoCapture(video_file)

        # loop through the video frames
        frame_number = 0
        while(cap.isOpened()):
            # read the next frame
            ret, frame = cap.read()
            if ret == True:
                if frame_number % 40 == 0:
                    # check if the frame is dark
                    if cv2.mean(frame)[0] > 30:
                        # detect persons in the frame using YOLOv5
                        results = model([frame])
                        persons = results.xyxy[0][results.xyxy[0][:, 5] == 0]

                        # filter persons based on their confidence score
                        persons = persons[persons[:, 4] >= min_confidence]

                        # if at least one person is detected with high enough confidence, save the frame as a JPEG image in the output directory
                        if len(persons) > 0:
                            out_filename = os.path.join(output_directory, f'{filename.replace(" ", "")}_{frame_number}.jpg')
                            cv2.imwrite(out_filename, frame)
                            print(f'Saved frame {frame_number} of video {filename} with {len(persons)} person(s) detected with confidence score >= {min_confidence}.')
                    
                # increment the frame number
                frame_number += 1
            else:
                break

        # release the video file
        cap.release()

        print(f'Finished processing {frame_number} frames of video {filename}.')

        # remove the video file after processing
        os.remove(video_file)
