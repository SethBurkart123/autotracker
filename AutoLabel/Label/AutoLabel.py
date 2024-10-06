import requests
import numpy as np
import torch
import cv2
from PIL import Image
import torchvision.ops as ops

from transformers import OwlViTProcessor, OwlViTForObjectDetection

showImg = True

class OwlViT:
    def __init__(self):
        self.processor = OwlViTProcessor.from_pretrained("google/owlvit-large-patch14")
        self.model = OwlViTForObjectDetection.from_pretrained("google/owlvit-large-patch14")
        self.iou_threshold = 0.4
        self.min_score_threshold = 0.1

    def processImage(self, imgPath, showImg=False):
        #url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        #image = Image.open(requests.get(url, stream=True).raw) # Retreave image from url
        image = Image.open(imgPath)
        texts = [["person's head", "person's eye", "person's hand", "person's nose", "eye", "an eye", "a mouth", "a picture of a mouth", "mouth"]]
        inputs = self.processor(text=texts, images=image, return_tensors="pt")
        outputs = self.model(**inputs)

        # Target image sizes (height, width) to rescale box predictions [batch_size, 2]
        target_sizes = torch.Tensor([image.size[::-1]])
        # Convert outputs (bounding boxes and class logits) to COCO API
        results = self.processor.post_process(outputs=outputs, target_sizes=target_sizes)

        if showImg:
            # Convert PIL image to numpy array and then to OpenCV format
            image_np = np.array(image)
            img = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            um_img = cv2.UMat(img)

        i = 0  # Retrieve predictions for the first image for the corresponding text queries
        text = texts[i]
        boxes, scores, labels = results[i]["boxes"], results[i]["scores"], results[i]["labels"]

        # Apply non-maximum suppression to remove overlapping bounding boxes
        keep_indices = ops.nms(boxes, scores, iou_threshold=self.iou_threshold)
        boxes, scores, labels = boxes[keep_indices], scores[keep_indices], labels[keep_indices]

        result = []

        # Print detected objects and rescaled box coordinates
        for box, score, label in zip(boxes, scores, labels):
            box = [round(i, 2) for i in box.tolist()]
            if score >= self.min_score_threshold:
                #print(f"Detected {text[label]} with confidence {round(score.item(), 3)} at location {box}")
                
                if showImg:
                    # Draw bounding box on image
                    box = [int(b) for b in box]
                    try:
                        cv2.rectangle(um_img, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
                    except:
                        print("box not in bounds")
                    # Define the text and its properties
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 1
                    color = (255, 0, 0)
                    thickness = 2

                    # Put the text on the image
                    try:
                        cv2.putText(um_img, str(text[label]), (box[2], box[3]), font, font_scale, color, thickness)
                    except:
                        print("box not in bounds")
                
                result.append({'label': str(text[label]), 'box': box, 'center': ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), 'confidence': round(score.item(), 3)})

        if showImg:
            # Display image with bounding boxes
            cv2.imshow('Image with Bounding Boxes', um_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return result

ModelOwlVit = OwlViT()
ModelOwlVit.texts = [["person's head", "person's hand"]]

detectionData = ModelOwlVit.processImage("../ExtractImg/output_frames/example_video.mp4_200.jpg", showImg=True)
print(detectionData)
