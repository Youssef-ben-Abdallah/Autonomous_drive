# Running detect_lane.py - Complete Guide

## ✅ Issue Fixed

The error you encountered was due to:
1. **Unreachable code** - Code after `raise` statement in `__init__` method
2. **Print statements** - Should use logger instead

Both issues have been fixed in `detect_lane.py`.

---

## 🚀 How to Run detect_lane.py

### Method 1: Direct Python Command (Recommended)

```bash
# From the project directory
python detect_lane.py
```

Or with explicit Python 3:
```bash
python3 detect_lane.py
```

### Method 2: From VS Code Terminal

1. Open the integrated terminal in VS Code (Ctrl + `)
2. Make sure you're in the project directory
3. Run:
```bash
python detect_lane.py
```

### Method 3: Run Configuration in VS Code

Create or update `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: detect_lane.py",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/detect_lane.py",
            "console": "integratedTerminal",
            "justMyCode": true,
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

Then press F5 to run.

---

## 📋 Prerequisites

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- opencv-python
- numpy
- ultralytics (for YOLO)
- python-dotenv

### 2. Create Logs Directory
```bash
mkdir logs
```

### 3. Configure Environment
```bash
# Copy the template
cp .env .env.local

# Edit .env.local with your settings
```

### 4. Download YOLO Files (Optional)
The script will automatically download:
- `yolov4-tiny.weights` (~40 MB)
- `yolov4-tiny.cfg`
- `coco.names`

Or download manually:
```bash
# Download weights
curl -L -o yolov4-tiny.weights https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights

# Download config
curl -L -o yolov4-tiny.cfg https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg

# Download class names
curl -L -o coco.names https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names
```

---

## 🧪 Test Before Running

Run the test script to verify everything is set up correctly:

```bash
python test_detect_lane.py
```

Expected output:
```
============================================================
🚀 DETECT_LANE.PY TEST SUITE
============================================================
🧪 Testing imports...
✅ cv2 (OpenCV) imported successfully
✅ numpy imported successfully
✅ utils.logger imported successfully

🧪 Testing logger...
✅ Logger initialized successfully

🧪 Testing detect_lane import...
✅ detect_lane module imported successfully

============================================================
✅ ALL TESTS PASSED!
============================================================
```

---

## 🔧 Troubleshooting

### Issue: "The system cannot find the path specified"

**Solution**: This was caused by unreachable code in the `__init__` method. This has been fixed.

### Issue: "ModuleNotFoundError: No module named 'cv2'"

**Solution**: Install OpenCV
```bash
pip install opencv-python
```

### Issue: "ModuleNotFoundError: No module named 'utils'"

**Solution**: Make sure you're running from the project root directory
```bash
cd "c:\Users\AHMED\Desktop\Self-driving-Car-Using-virtual carRaspberry-Pi - Copy"
python detect_lane.py
```

### Issue: "FileNotFoundError: YOLO model files missing"

**Solution**: Download YOLO files
```bash
python detect_lane.py
# The script will automatically download them
```

Or download manually (see Prerequisites section above).

### Issue: "UnicodeEncodeError" with emoji characters

**Solution**: This is a Windows console encoding issue. The code still works fine. To fix:

**Option 1**: Use Windows Terminal instead of Command Prompt
- Download from Microsoft Store
- Run: `python detect_lane.py`

**Option 2**: Set environment variable
```bash
set PYTHONIOENCODING=utf-8
python detect_lane.py
```

**Option 3**: Use PowerShell
```powershell
$env:PYTHONIOENCODING = "utf-8"
python detect_lane.py
```

### Issue: "No camera/webcam found"

**Solution**: The script needs a camera input. Make sure:
1. Your webcam is connected
2. No other application is using the camera
3. Camera permissions are granted

### Issue: "YOLO model loading fails"

**Solution**: Check that model files exist
```bash
# List files
dir yolov4-tiny.*
dir coco.names

# If missing, download them
python detect_lane.py
```

---

## 📊 What detect_lane.py Does

The script performs:
1. **Lane Detection** - Detects road lanes using computer vision
2. **Object Detection** - Detects cars, pedestrians, traffic lights using YOLO
3. **Scene Analysis** - Analyzes the driving scene
4. **Safety Assessment** - Determines if the path is safe
5. **Action Recommendation** - Suggests driving actions

---

## 📝 Output

### Console Output
```
2025-10-23 22:34:31 - detect_lane - INFO - Initializing Fast YOLO Navigation System...
2025-10-23 22:34:31 - detect_lane - INFO - ✅ YOLO model loaded successfully
2025-10-23 22:34:31 - detect_lane - INFO - ✅ Fast YOLO Navigation System Ready!
```

### Log Files
Logs are saved to: `logs/vehicle_YYYYMMDD.log`

Example:
```
logs/vehicle_20251023.log
```

### Video Output
If running with video input, a window will display:
- Detected lanes (green lines)
- Detected objects (bounding boxes)
- Safety status
- Recommended actions

---

## 🎯 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create logs directory
mkdir logs

# 3. Configure environment
cp .env .env.local

# 4. Test setup
python test_detect_lane.py

# 5. Run detect_lane
python detect_lane.py
```

---

## 📚 Related Files

- `detect_lane.py` - Main lane detection module
- `test_detect_lane.py` - Test script
- `utils/logger.py` - Logging system
- `config/config.yaml` - Configuration
- `.env` - Environment variables
- `requirements.txt` - Python dependencies

---

## ✨ Recent Fixes

### Fixed Issues
- ✅ Unreachable code in `__init__` method (lines 49-76)
- ✅ Print statements replaced with logger
- ✅ Error handling improved
- ✅ File existence checks added

### Code Quality Improvements
- ✅ Proper exception handling
- ✅ Comprehensive logging
- ✅ Better error messages
- ✅ Type hints added

---

## 🚀 Next Steps

1. **Run the test**: `python test_detect_lane.py`
2. **Check logs**: `logs/vehicle_YYYYMMDD.log`
3. **Run the script**: `python detect_lane.py`
4. **Monitor output**: Check console and log files

---

## 📞 Support

If you encounter issues:

1. **Check the logs**: `logs/vehicle_YYYYMMDD.log`
2. **Run the test**: `python test_detect_lane.py`
3. **Verify setup**: Check all prerequisites are installed
4. **Review documentation**: See QUICK_START.md

---

**Status**: ✅ Ready to Run  
**Last Updated**: 2025-10-23  
**Python Version**: 3.6+

