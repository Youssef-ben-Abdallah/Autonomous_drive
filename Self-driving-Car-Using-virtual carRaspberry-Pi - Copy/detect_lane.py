#!/usr/bin/env python3
"""
Lane Detection Module
Detects lanes and obstacles using YOLOv4-tiny
"""

import cv2
import numpy as np
import time
import os
import urllib.request
from utils.logger import get_logger

logger = get_logger(__name__)


class FastYOLONavigation:
    def __init__(self):
        """Initialize Fast YOLO Navigation System with error handling."""
        try:
            logger.info("Initializing Fast YOLO Navigation System...")

            # Download YOLO files
            self.download_yolo_files()

            # Load YOLO - CPU only for compatibility
            weights_file = 'yolov4-tiny.weights'
            config_file = 'yolov4-tiny.cfg'

            if not os.path.exists(weights_file) or not os.path.exists(config_file):
                logger.error(f"YOLO files not found: {weights_file}, {config_file}")
                raise FileNotFoundError("YOLO model files missing")

            self.net = cv2.dnn.readNet(weights_file, config_file)
            logger.info("✅ YOLO model loaded successfully")

            # Load class names
            coco_file = "coco.names"
            if not os.path.exists(coco_file):
                logger.error(f"Class names file not found: {coco_file}")
                raise FileNotFoundError("coco.names file missing")

            with open(coco_file, "r") as f:
                self.classes = [line.strip() for line in f.readlines()]

            # Road relevant classes and their colors
            self.road_classes = {
                'car': (0, 255, 0),  # Green
                'bus': (0, 255, 0),  # Green
                'truck': (0, 255, 0),  # Green
                'motorcycle': (0, 165, 255),  # Orange
                'bicycle': (0, 165, 255),  # Orange
                'person': (0, 0, 255),  # Red
                'traffic light': (255, 255, 0),  # Cyan
                'stop sign': (255, 255, 0)  # Cyan
            }

            self.road_class_ids = [i for i, class_name in enumerate(self.classes)
                                   if class_name in self.road_classes.keys()]

            # Get output layer names
            layer_names = self.net.getLayerNames()
            self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]

            # Performance optimization
            self.last_detections = []
            self.frame_count = 0
            self.detection_interval = 5  # Detect every 5th frame for speed

            logger.info("✅ Fast YOLO Navigation System Ready!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize YOLO Navigation: {e}", exc_info=True)
            raise

    def download_yolo_files(self):
        """Download YOLO files if they don't exist"""
        files = {
            'yolov4-tiny.weights': 'https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights',
            'yolov4-tiny.cfg': 'https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg',
            'coco.names': 'https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names'
        }

        for filename, url in files.items():
            if not os.path.exists(filename):
                logger.info(f"📥 Downloading {filename}...")
                try:
                    urllib.request.urlretrieve(url, filename)
                    logger.info(f"✓ Downloaded {filename}")
                except Exception as e:
                    logger.warning(f"✗ Failed to download {filename}: {e}")
                    # Create minimal fallback
                    self.create_fallback_files()
                    break

    def create_fallback_files(self):
        """Create minimal fallback files"""
        # Create minimal coco.names with only road classes
        if not os.path.exists("coco.names"):
            with open("coco.names", "w") as f:
                for class_name in self.road_classes.keys():
                    f.write(class_name + "\n")
            print("Created fallback coco.names")

    def detect_objects_yolo(self, image):
        """Fast YOLO object detection with CPU optimization"""
        self.frame_count += 1

        # Skip frames for detection to improve speed
        if self.frame_count % self.detection_interval != 0 and self.last_detections:
            return self.last_detections

        height, width = image.shape[:2]

        try:
            # Prepare input blob - using smaller size for speed (320x320 instead of 416x416)
            blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (320, 320), swapRB=True, crop=False)
            self.net.setInput(blob)

            # Run forward pass
            outputs = self.net.forward(self.output_layers)

            # Process detections
            detections = []
            boxes = []
            confidences = []
            class_ids = []

            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]

                    # Filter road-relevant objects with good confidence
                    if confidence > 0.4 and class_id in self.road_class_ids:
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)

                        # Rectangle coordinates
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)

                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        class_ids.append(class_id)

            # Apply non-maximum suppression
            if boxes:
                indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.4, 0.3)

                if len(indices) > 0:
                    for i in indices.flatten():
                        x, y, w, h = boxes[i]
                        class_name = self.classes[class_ids[i]]

                        detections.append({
                            'class': class_name,
                            'box': [x, y, x + w, y + h],
                            'confidence': confidences[i],
                            'center': (x + w // 2, y + h // 2)
                        })

            self.last_detections = detections
            return detections

        except Exception as e:
            print(f"Detection error: {e}")
            return self.last_detections

    def detect_lanes_fast(self, image):
        """Very fast lane detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Fast Gaussian blur
        blur = cv2.GaussianBlur(gray, (3, 3), 0)

        # Edge detection on smaller image for speed
        small_img = cv2.resize(blur, (320, 240))
        edges = cv2.Canny(small_img, 50, 150)

        # Scale back up
        edges = cv2.resize(edges, (image.shape[1], image.shape[0]))

        # Create mask for ROI
        height, width = image.shape[:2]
        mask = np.zeros_like(edges)

        # Define ROI polygon
        polygon = np.array([[
            (0, height),
            (width // 4, height // 2),
            (3 * width // 4, height // 2),
            (width, height)
        ]], np.int32)

        cv2.fillPoly(mask, [polygon], 255)
        masked_edges = cv2.bitwise_and(edges, mask)

        # Fast Hough Transform
        lines = cv2.HoughLinesP(masked_edges, 1, np.pi / 180, 20, minLineLength=25, maxLineGap=30)

        return lines, polygon

    def analyze_scene(self, image, detections, lane_lines):
        """Fast scene analysis"""
        height, width = image.shape[:2]

        analysis = {
            'cars_detected': 0,
            'obstacles_detected': 0,
            'traffic_controls': 0,
            'objects_in_path': [],
            'lane_status': 'NO_LANES',
            'safety_status': 'SAFE',
            'recommended_action': 'MAINTAIN_LANE'
        }

        # Analyze objects
        for obj in detections:
            if obj['class'] in ['car', 'bus', 'truck']:
                analysis['cars_detected'] += 1

                # Check if object is in our path
                center_x = obj['center'][0]
                if width * 0.3 < center_x < width * 0.7:
                    analysis['objects_in_path'].append(obj)

            elif obj['class'] in ['person', 'bicycle', 'motorcycle']:
                analysis['obstacles_detected'] += 1
                analysis['safety_status'] = 'CAUTION'

            elif obj['class'] in ['traffic light', 'stop sign']:
                analysis['traffic_controls'] += 1

        # Analyze lanes
        if lane_lines is not None and len(lane_lines) > 0:
            left_count = 0
            right_count = 0

            for line in lane_lines:
                for x1, y1, x2, y2 in line:
                    if x2 - x1 == 0:
                        continue
                    slope = (y2 - y1) / (x2 - x1)

                    if slope > 0.1:  # Left lane
                        left_count += 1
                    elif slope < -0.1:  # Right lane
                        right_count += 1

            if left_count >= 1 and right_count >= 1:
                analysis['lane_status'] = 'CLEAR_LANES'
            elif left_count >= 1 or right_count >= 1:
                analysis['lane_status'] = 'PARTIAL_LANES'

        # Make decision
        analysis['recommended_action'] = self.make_decision(analysis)

        return analysis

    def make_decision(self, analysis):
        """Make navigation decision"""
        # Priority 1: Safety first
        if analysis['safety_status'] == 'CAUTION':
            return "REDUCE_SPEED"

        # Priority 2: Objects blocking path
        if len(analysis['objects_in_path']) > 0:
            if analysis['lane_status'] == 'CLEAR_LANES':
                return "PREPARE_OVERTAKE"
            else:
                return "MAINTAIN_DISTANCE"

        # Priority 3: Road conditions
        if analysis['lane_status'] == 'NO_LANES':
            return "PROCEED_CAUTIOUSLY"

        # Priority 4: Traffic controls
        if analysis['traffic_controls'] > 0:
            return "PREPARE_TO_STOP"

        return "MAINTAIN_LANE"

    def draw_results_fast(self, image, analysis, detections, lane_lines, roi_vertices, fps):
        """Fast drawing with minimal operations"""
        result = image.copy()
        height, width = image.shape[:2]

        # Draw ROI
        cv2.polylines(result, [roi_vertices], True, (0, 255, 0), 1)

        # Draw lane lines (limited number for speed)
        if lane_lines is not None:
            for line in lane_lines[:8]:  # Limit to 8 lines
                for x1, y1, x2, y2 in line:
                    cv2.line(result, (x1, y1), (x2, y2), (0, 0, 255), 2)

        # Draw object detections (limited number for speed)
        for obj in detections[:10]:  # Limit to 10 detections
            x1, y1, x2, y2 = obj['box']
            class_name = obj['class']
            color = self.road_classes.get(class_name, (255, 255, 255))

            # Draw bounding box
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 1)

            # Draw simple label
            label = f"{class_name}"
            cv2.putText(result, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # Draw fast info panel
        self.draw_fast_info_panel(result, analysis, fps, width)

        return result

    def draw_fast_info_panel(self, image, analysis, fps, width):
        """Minimal info panel for maximum speed"""
        # Small overlay
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (280, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        # Status colors
        safety_color = (0, 255, 0) if analysis['safety_status'] == 'SAFE' else (0, 165, 255)
        action_color = (0, 255, 0) if analysis['recommended_action'] == 'MAINTAIN_LANE' else (0, 165, 255)

        # Minimal text
        y_pos = 15
        cv2.putText(image, f"FPS: {fps:.1f}", (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_pos += 15

        cv2.putText(image, f"Cars: {analysis['cars_detected']}", (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_pos += 15

        cv2.putText(image, f"Lanes: {analysis['lane_status']}", (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_pos += 15

        cv2.putText(image, f"Action: {analysis['recommended_action']}", (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, action_color, 1)

        # Simple action indicator
        if "OVERTAKE" in analysis['recommended_action']:
            cv2.putText(image, ">>>", (width - 50, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        elif "STOP" in analysis['recommended_action']:
            cv2.putText(image, "!", (width - 30, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


def main():
    # Initialize navigation
    nav = FastYOLONavigation()

    # Initialize camera with low resolution for speed
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("FAST YOLO NAVIGATION STARTED")
    print("=" * 40)
    print("Running on CPU - Optimized for speed")
    print("Press 'q' to quit")
    print("=" * 40)

    # FPS calculation
    frame_count = 0
    start_time = time.time()
    fps = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # Detect objects with YOLO
            detections = nav.detect_objects_yolo(frame)

            # Detect lanes
            lane_lines, roi_vertices = nav.detect_lanes_fast(frame)

            # Analyze scene
            analysis = nav.analyze_scene(frame, detections, lane_lines)

            # Calculate FPS
            if frame_count % 15 == 0:
                current_time = time.time()
                fps = 15 / (current_time - start_time)
                start_time = current_time

            # Draw results
            result_frame = nav.draw_results_fast(frame, analysis, detections, lane_lines, roi_vertices, fps)

            # Display
            cv2.imshow('Fast YOLO Navigation', result_frame)

            # Print status occasionally
            if frame_count % 45 == 0:
                print(f"FPS: {fps:.1f} | Cars: {analysis['cars_detected']} | Action: {analysis['recommended_action']}")

            # Exit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Navigation stopped")


if __name__ == "__main__":
    main()
    exit(0)