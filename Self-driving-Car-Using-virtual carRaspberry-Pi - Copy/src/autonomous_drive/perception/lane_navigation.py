"""Lane detection and scene understanding for autonomous driving.

This module wraps the original ``detect_lane.py`` script into a reusable
``LaneNavigationSystem`` class. The behaviour is intentionally equivalent to the
legacy implementation but the code has been reorganised and heavily commented to
improve readability and maintainability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np
import time
import urllib.request

from autonomous_drive.utils.logger import get_logger

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Detection:
    """Simple container for object detections produced by YOLO."""

    label: str
    box: Tuple[int, int, int, int]
    confidence: float
    center: Tuple[int, int]


@dataclass
class SceneAnalysis:
    """Summarises the high level understanding of the current frame."""

    cars_detected: int = 0
    obstacles_detected: int = 0
    traffic_controls: int = 0
    objects_in_path: List[Detection] = field(default_factory=list)
    lane_status: str = "NO_LANES"
    safety_status: str = "SAFE"
    recommended_action: str = "MAINTAIN_LANE"


# ---------------------------------------------------------------------------
# Lane navigation system
# ---------------------------------------------------------------------------


class LaneNavigationSystem:
    """Run lightweight YOLO inference alongside fast lane detection.

    The implementation mirrors the legacy ``FastYOLONavigation`` class while
    adding extensive inline documentation.  All external behaviour – logging,
    frame analysis and the console interface – remains unchanged which ensures
    existing scripts keep working after the repository cleanup.
    """

    MODEL_FILES: Dict[str, str] = {
        "yolov4-tiny.weights": "https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights",
        "yolov4-tiny.cfg": "https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg",
        "coco.names": "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names",
    }

    # Colours used when drawing the detection overlay.
    ROAD_CLASS_COLOURS: Dict[str, Tuple[int, int, int]] = {
        "car": (0, 255, 0),
        "bus": (0, 255, 0),
        "truck": (0, 255, 0),
        "motorcycle": (0, 165, 255),
        "bicycle": (0, 165, 255),
        "person": (0, 0, 255),
        "traffic light": (255, 255, 0),
        "stop sign": (255, 255, 0),
    }

    def __init__(self, model_directory: Optional[Path] = None) -> None:
        """Initialise the navigation system and load the YOLO weights."""

        self.logger = get_logger(__name__)
        self.logger.info("Initialising fast YOLO navigation system")

        self.model_directory = model_directory or Path.cwd()
        self.model_directory.mkdir(parents=True, exist_ok=True)

        # Internal state used to reduce the inference load on the CPU.
        self.last_detections: List[Detection] = []
        self.frame_count: int = 0
        self.detection_interval: int = 5  # Run YOLO on every 5th frame by default.

        # Prepare model artefacts.
        self._download_model_files()
        self._load_class_labels()
        self._load_yolo_network()

    # ------------------------------------------------------------------
    # Model preparation
    # ------------------------------------------------------------------

    def _download_model_files(self) -> None:
        """Download YOLO artefacts when they are missing from disk."""

        for filename, url in self.MODEL_FILES.items():
            target = self.model_directory / filename
            if target.exists():
                continue

            self.logger.info("Downloading %s", filename)
            try:
                urllib.request.urlretrieve(url, str(target))
            except Exception as exc:  # pragma: no cover - network failures
                self.logger.warning("Failed to download %s: %s", filename, exc)
                self._create_fallback_files()
                break

    def _create_fallback_files(self) -> None:
        """Create a minimal ``coco.names`` file when downloads fail."""

        target = self.model_directory / "coco.names"
        if target.exists():
            return

        self.logger.warning("Creating fallback coco.names file")
        with target.open("w", encoding="utf-8") as handle:
            for class_name in self.ROAD_CLASS_COLOURS:
                handle.write(f"{class_name}\n")

    def _load_class_labels(self) -> None:
        """Load COCO class labels from the local filesystem."""

        labels_file = self.model_directory / "coco.names"
        if not labels_file.exists():
            raise FileNotFoundError("coco.names file is required for YOLO inference")

        with labels_file.open("r", encoding="utf-8") as handle:
            self.class_labels: List[str] = [line.strip() for line in handle if line.strip()]

        self.road_class_ids = [
            index
            for index, name in enumerate(self.class_labels)
            if name in self.ROAD_CLASS_COLOURS
        ]

    def _load_yolo_network(self) -> None:
        """Load the YOLOv4-tiny model into OpenCV's DNN module."""

        weights_file = self.model_directory / "yolov4-tiny.weights"
        config_file = self.model_directory / "yolov4-tiny.cfg"

        if not weights_file.exists() or not config_file.exists():
            raise FileNotFoundError("YOLO model files are missing – run download first")

        self.net = cv2.dnn.readNet(str(weights_file), str(config_file))
        layer_names = self.net.getLayerNames()
        self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]

        self.logger.info("YOLO model loaded successfully")

    # ------------------------------------------------------------------
    # Perception helpers
    # ------------------------------------------------------------------

    def detect_objects(self, image: np.ndarray) -> List[Detection]:
        """Run YOLO detection on the provided frame with simple frame skipping."""

        self.frame_count += 1
        if self.frame_count % self.detection_interval != 0 and self.last_detections:
            return self.last_detections

        height, width = image.shape[:2]

        blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (320, 320), swapRB=True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)

        boxes: List[List[int]] = []
        confidences: List[float] = []
        class_ids: List[int] = []

        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = int(np.argmax(scores))
                confidence = float(scores[class_id])

                if confidence <= 0.4 or class_id not in self.road_class_ids:
                    continue

                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                box_width = int(detection[2] * width)
                box_height = int(detection[3] * height)

                x = int(center_x - box_width / 2)
                y = int(center_y - box_height / 2)

                boxes.append([x, y, box_width, box_height])
                confidences.append(confidence)
                class_ids.append(class_id)

        detections: List[Detection] = []
        if boxes:
            indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.4, 0.3)
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                label = self.class_labels[class_ids[i]]
                detections.append(
                    Detection(
                        label=label,
                        box=(x, y, x + w, y + h),
                        confidence=confidences[i],
                        center=(x + w // 2, y + h // 2),
                    )
                )

        self.last_detections = detections
        return detections

    def detect_lanes(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], np.ndarray]:
        """Perform a fast lane search using Canny edges and the Hough transform."""

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        small_img = cv2.resize(blur, (320, 240))
        edges = cv2.Canny(small_img, 50, 150)
        edges = cv2.resize(edges, (image.shape[1], image.shape[0]))

        height, width = image.shape[:2]
        mask = np.zeros_like(edges)
        polygon = np.array(
            [
                [
                    (0, height),
                    (width // 4, height // 2),
                    (3 * width // 4, height // 2),
                    (width, height),
                ]
            ],
            np.int32,
        )
        cv2.fillPoly(mask, polygon, 255)
        masked_edges = cv2.bitwise_and(edges, mask)

        lines = cv2.HoughLinesP(
            masked_edges,
            rho=1,
            theta=np.pi / 180,
            threshold=20,
            minLineLength=25,
            maxLineGap=30,
        )
        return lines, polygon[0]

    # ------------------------------------------------------------------
    # Scene analysis
    # ------------------------------------------------------------------

    def analyse_scene(self, image: np.ndarray, detections: Sequence[Detection], lane_lines: Optional[np.ndarray]) -> SceneAnalysis:
        """Combine object detections and lane lines into a high level summary."""

        analysis = SceneAnalysis()
        height, width = image.shape[:2]

        for obj in detections:
            if obj.label in {"car", "bus", "truck"}:
                analysis.cars_detected += 1
                if width * 0.3 < obj.center[0] < width * 0.7:
                    analysis.objects_in_path.append(obj)
            elif obj.label in {"person", "bicycle", "motorcycle"}:
                analysis.obstacles_detected += 1
                analysis.safety_status = "CAUTION"
            elif obj.label in {"traffic light", "stop sign"}:
                analysis.traffic_controls += 1

        if lane_lines is not None and len(lane_lines) > 0:
            left_count = 0
            right_count = 0

            for line in lane_lines:
                for x1, y1, x2, y2 in line:
                    if x2 == x1:
                        continue
                    slope = (y2 - y1) / (x2 - x1)
                    if slope > 0.1:
                        left_count += 1
                    elif slope < -0.1:
                        right_count += 1

            if left_count >= 1 and right_count >= 1:
                analysis.lane_status = "CLEAR_LANES"
            elif left_count >= 1 or right_count >= 1:
                analysis.lane_status = "PARTIAL_LANES"

        analysis.recommended_action = self._make_decision(analysis)
        return analysis

    def _make_decision(self, analysis: SceneAnalysis) -> str:
        """Determine the appropriate driving action based on the analysis."""

        if analysis.safety_status == "CAUTION":
            return "REDUCE_SPEED"

        if analysis.objects_in_path:
            if analysis.lane_status == "CLEAR_LANES":
                return "PREPARE_OVERTAKE"
            return "MAINTAIN_DISTANCE"

        if analysis.lane_status == "NO_LANES":
            return "PROCEED_CAUTIOUSLY"

        if analysis.traffic_controls > 0:
            return "PREPARE_TO_STOP"

        return "MAINTAIN_LANE"

    # ------------------------------------------------------------------
    # Visualisation helpers
    # ------------------------------------------------------------------

    def draw_results(
        self,
        image: np.ndarray,
        analysis: SceneAnalysis,
        detections: Sequence[Detection],
        lane_lines: Optional[np.ndarray],
        roi_vertices: np.ndarray,
        fps: float,
    ) -> np.ndarray:
        """Overlay detections, lanes and a status panel on the frame."""

        result = image.copy()
        height, width = image.shape[:2]

        cv2.polylines(result, [roi_vertices], True, (0, 255, 0), 1)

        if lane_lines is not None:
            for line in lane_lines[:8]:
                for x1, y1, x2, y2 in line:
                    cv2.line(result, (x1, y1), (x2, y2), (0, 0, 255), 2)

        for obj in list(detections)[:10]:
            x1, y1, x2, y2 = obj.box
            colour = self.ROAD_CLASS_COLOURS.get(obj.label, (255, 255, 255))
            cv2.rectangle(result, (x1, y1), (x2, y2), colour, 1)
            cv2.putText(result, obj.label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, colour, 1)

        self._draw_info_panel(result, analysis, fps, width)
        return result

    def _draw_info_panel(self, image: np.ndarray, analysis: SceneAnalysis, fps: float, width: int) -> None:
        """Render a compact information overlay in the top left corner."""

        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (280, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        safety_colour = (0, 255, 0) if analysis.safety_status == "SAFE" else (0, 165, 255)
        action_colour = (0, 255, 0) if analysis.recommended_action == "MAINTAIN_LANE" else (0, 165, 255)

        y_pos = 15
        cv2.putText(image, f"FPS: {fps:.1f}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_pos += 15
        cv2.putText(image, f"Cars: {analysis.cars_detected}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_pos += 15
        cv2.putText(image, f"Lanes: {analysis.lane_status}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        y_pos += 15
        cv2.putText(image, f"Action: {analysis.recommended_action}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, action_colour, 1)

        if "OVERTAKE" in analysis.recommended_action:
            cv2.putText(image, ">>>", (width - 50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        elif "STOP" in analysis.recommended_action:
            cv2.putText(image, "!", (width - 30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # ------------------------------------------------------------------
    # Convenience runner
    # ------------------------------------------------------------------

    def run(self, camera_index: int = 0) -> None:
        """Provide a CLI-friendly loop that mirrors the legacy script output."""

        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        print("FAST YOLO NAVIGATION STARTED")
        print("=" * 40)
        print("Running on CPU - Optimised for speed")
        print("Press 'q' to quit")
        print("=" * 40)

        frame_count = 0
        start_time = time.time()
        fps = 0.0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                detections = self.detect_objects(frame)
                lane_lines, roi_vertices = self.detect_lanes(frame)
                analysis = self.analyse_scene(frame, detections, lane_lines)

                if frame_count % 15 == 0:
                    current_time = time.time()
                    fps = 15 / (current_time - start_time)
                    start_time = current_time

                result_frame = self.draw_results(frame, analysis, detections, lane_lines, roi_vertices, fps)
                cv2.imshow("Fast YOLO Navigation", result_frame)

                if frame_count % 45 == 0:
                    print(
                        f"FPS: {fps:.1f} | Cars: {analysis.cars_detected} | "
                        f"Action: {analysis.recommended_action}"
                    )

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        except KeyboardInterrupt:
            print("Stopped by user")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("Navigation stopped")


__all__ = ["LaneNavigationSystem", "Detection", "SceneAnalysis"]
