import sys
from ..detect_persons import get_persons_bounding_box
import json

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_detection.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    print(f"Testing detection on image: {image_path}")
    
    try:
        result = get_persons_bounding_box(image_path)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")