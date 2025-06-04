#!/bin/bash

# Check if an image path was provided
if [ $# -eq 0 ]; then
    echo "Usage: ./detect_image.sh <path_to_image>"
    exit 1
fi

IMAGE_PATH=$1

# Check if the file exists
if [ ! -f "$IMAGE_PATH" ]; then
    echo "Error: File '$IMAGE_PATH' does not exist"
    exit 1
fi

# Send the image to the detection server
echo "Sending image '$IMAGE_PATH' to detection server..."
curl -X POST -F "image=@$IMAGE_PATH" http://localhost:3000/detect_persons

echo ""
echo "Done!"