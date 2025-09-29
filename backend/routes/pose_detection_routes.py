from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import shutil
import os
import json
import base64
import cv2
import numpy as np
from io import BytesIO
from PIL import Image

from backend.utils.pose_detection_utils import PoseDetectionService

router = APIRouter()

# Initialize pose detection service
pose_service = PoseDetectionService()

@router.post("/detect-from-image")
async def detect_pose_from_image(file: UploadFile = File(...)):
    """
    Endpoint to detect yoga pose from uploaded image
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file temporarily
    temp_file_path = f"temp_uploads/pose_detection_{file.filename}"
    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the image
        result = await pose_service.classify_pose_from_image(temp_file_path)
        
        return JSONResponse(content={
            "success": True,
            "data": result
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.websocket("/realtime-detection")
async def websocket_realtime_detection(websocket: WebSocket):
    """
    WebSocket endpoint for real-time pose detection
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive image data from client
            data = await websocket.receive_text()
            image_data = json.loads(data)
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data['image'])
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Save temporarily for processing
            temp_path = "temp_realtime.jpg"
            cv2.imwrite(temp_path, cv_image)
            
            try:
                # Process the frame
                result = await pose_service.classify_pose_from_image(temp_path)
                
                # Send result back to client
                await websocket.send_json({
                    "success": True,
                    "data": result
                })
                
            except Exception as e:
                await websocket.send_json({
                    "success": False,
                    "error": str(e)
                })
            
            finally:
                # Clean up
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
    except WebSocketDisconnect:
        print("Client disconnected from real-time pose detection")
    except Exception as e:
        print(f"WebSocket error: {e}")

@router.get("/available-asanas")
async def get_available_asanas():
    """
    Get list of available yoga asanas for reference
    """
    try:
        asanas = pose_service.get_available_asanas()
        return JSONResponse(content={
            "success": True,
            "asanas": asanas
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching asanas: {str(e)}")

@router.get("/asana-info/{asana_name}")
async def get_asana_info(asana_name: str):
    """
    Get detailed information about a specific asana
    """
    try:
        info = pose_service.get_asana_info(asana_name)
        if not info:
            raise HTTPException(status_code=404, detail="Asana not found")
        
        return JSONResponse(content={
            "success": True,
            "data": info
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching asana info: {str(e)}")

@router.post("/compare-poses")
async def compare_poses(reference_asana: str, file: UploadFile = File(...)):
    """
    Compare uploaded pose with specific reference asana
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    temp_file_path = f"temp_uploads/compare_{file.filename}"
    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = await pose_service.compare_with_reference(temp_file_path, reference_asana)
        
        return JSONResponse(content={
            "success": True,
            "data": result
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing poses: {str(e)}")
    
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
