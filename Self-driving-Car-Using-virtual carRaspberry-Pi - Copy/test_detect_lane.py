#!/usr/bin/env python3
"""
Test script for detect_lane.py
Verifies that the module can be imported and initialized
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    try:
        import cv2
        print("✅ cv2 (OpenCV) imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import cv2: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import numpy: {e}")
        return False
    
    try:
        from utils.logger import get_logger
        print("✅ utils.logger imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import utils.logger: {e}")
        return False
    
    return True

def test_logger():
    """Test that logger works"""
    print("\n🧪 Testing logger...")
    try:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("✅ Logger initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Logger test failed: {e}")
        return False

def test_detect_lane_import():
    """Test that detect_lane module can be imported"""
    print("\n🧪 Testing detect_lane import...")
    try:
        from detect_lane import FastYOLONavigation
        print("✅ detect_lane module imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import detect_lane: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 DETECT_LANE.PY TEST SUITE")
    print("=" * 60)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import test failed. Please install required packages:")
        print("   pip install -r requirements.txt")
        return False
    
    # Test 2: Logger
    if not test_logger():
        print("\n❌ Logger test failed")
        return False
    
    # Test 3: detect_lane import
    if not test_detect_lane_import():
        print("\n❌ detect_lane import failed")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("1. Ensure YOLO model files are downloaded")
    print("2. Run: python detect_lane.py")
    print("3. Check logs in logs/vehicle_YYYYMMDD.log")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

