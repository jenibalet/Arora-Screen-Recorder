
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import base64
from datetime import datetime
from ibm_boto3 import client
from ibm_botocore.client import Config
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse


app = FastAPI()

# Allow frontend to connect

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



# IBM COS credentials (replace with your actual credentials)
credentials = {
    "apikey": "D6nKhm1X2hsHT018LFARv0278MnQ_gxuW2csx-ZKq1uQ",
    "resource_instance_id":  "crn:v1:bluemix:public:cloud-object-storage:global:a/90f87cc5c3f34bc7bf98165268e0d800:fe3a2a66-94a3-4125-a745-2aa00cb81825:bucket:screenrecordingpy",
    "endpoint_url": "https://screenrecordingpy.s3-web.us-south.cloud-object-storage.appdomain.cloud",
    "bucket_name": "screenrecordingpy"
}

# IBM COS client setup
cos = client("s3",
    ibm_api_key_id=credentials["apikey"],
    ibm_service_instance_id=credentials["resource_instance_id"],
    config=Config(signature_version="oauth"),
    endpoint_url=credentials["endpoint_url"]
)

# Ensure frames directory exists
os.makedirs("frames", exist_ok=True)

# Mount static files for serving images
app.mount("/frames", StaticFiles(directory="frames"), name="frames")


    
    
@app.post("/upload-frame")
async def upload_frame(request: Request):
    data = await request.json()
    image_data = data["image"].split(",")[1]  # Remove base64 header
    image_bytes = base64.b64decode(image_data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"frames/frame_{timestamp}.png"

    with open(filename, "wb") as f:
        f.write(image_bytes)

    return {"status": "saved", "filename": filename}
    

    # Upload to IBM COS
    cos.put_object(
        Bucket=credentials["bucket_name"],
        Key=filename,
        Body=image_bytes
    )

    return {"status": "uploaded", "filename": filename}

@app.get("/view-frames", response_class=HTMLResponse)
def view_frames():
    frame_dir = "frames"
    files = sorted(os.listdir(frame_dir))
    html = "<h1>Captured Frames Gallery</h1><div style='display:flex;flex-wrap:wrap;'>"
    for file in files:
        if file.endswith(".png"):
            html += f"<div style='margin:10px'><img src='/frames/{file}' width='300'><p>{file}</p></div>"
    html += "</div>"
    return html
