import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import hashlib

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [ os.environ.get('FRONT_URL', 'http://localhost:3000') ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    logger.info(f"Receive item: {name}, category: {category}")

    # Read and save image
    image_content = image.file.read()
    sha256_hash = hashlib.sha256(image_content).hexdigest()
    image_filename = f"{sha256_hash}.jpg"
    with open(images / image_filename, "wb") as f:
        f.write(image_content)

    # Load existing data
    with open('items.json', 'r') as file:
        data = json.load(file)

    # Add new item
    new_item = {"name": name, "category": category, "image": image_filename}
    data['items'].append(new_item)

    # Save updated data
    with open('items.json', 'w') as file:
        json.dump(data, file)

    return {"message": f"item received: {name}, category: {category}, image: {image_filename}"}

@app.get("/image/{image_filename}")
async def get_image(image_filename):
    # Create image path
    image = images / image_filename

    if not image_filename.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)

@app.get("/items/{item_id}")
def get_items():
    try:
        with open('items.json', 'r') as f:
            items = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Items not found")
    return items
def get_item_id(item_id: int):
    items = get_items()

    if item_id >= len(items["items"]):
        raise HTTPException(status_code=404, detail="Item id not found!")

    return items["items"][item_id]