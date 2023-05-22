import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, File, UploadFile,Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import sqlite3

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

# Establish a connection to the SQLite database and create a cursor object
conn = sqlite3.connect('mercari.sqlite3')
cur = conn.cursor()
# Create the table if it doesn't exist
with conn:
    cur.execute("""CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY,
        category TEXT
    )""")

#with conn:
    #category_name = 'fashion'
    #cur.execute("""INSERT INTO categories (category) VALUES (?)""", (category_name,))

# Modify the items table to use category_id instead of category name
with conn:
    cur.execute("""CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT,
        category_id INTEGER,
        image_name TEXT,
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    )""")

# Save the table structure to the file db/items.db
with open('/Users/zhao/PycharmProjects/merukari/mercari-build-training-2023/db/items.db', 'w') as f:
    schema = '\n'.join(conn.iterdump())
    f.write(schema)

conn.commit()
conn.close()

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

    # Save the item to the database
    category_id = check_category(category)
    conn = sqlite3.connect('mercari.sqlite3')
    cur = conn.cursor()
    with conn:
        cur.execute("""INSERT INTO items (name, category_id, image_name) VALUES (?, ?, ?)""",
                    (name, category_id, image_filename))
    conn.commit()
    conn.close()

    return {"message": f"item received: {name}, category_id: {category_id}, image: {image_filename}"}
def check_category(category_name: str):
    conn = sqlite3.connect('mercari.sqlite3')
    cur = conn.cursor()
    # check if the category name exists
    with conn:
        cur.execute("SELECT category_id FROM categories WHERE category = ?", (category_name,))
    result = cur.fetchone()
    conn.close()

    if result is not None:
        category_id = result[0]
    else:
        # Prevent customers from modifying the database.
        raise HTTPException(status_code=404, detail="Category not found!")

    return category_id

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

@app.get("/search")
def search_keyword(keyword: str = Query(..., description="Keyword for searching items")):
    # Retrieve the item list from the database
    conn = sqlite3.connect('mercari.sqlite3')
    cur = conn.cursor()
    with conn:
        cur.execute("SELECT * FROM items WHERE name LIKE ?", (f"%{keyword}%",))
        items = cur.fetchall()
    conn.close()
    # Convert the item list to the appropriate format and return
    response = {
        "items": items
    }
    return response
@app.get("/items/{item_id}")
def get_id_item(item_id: int):
    # select by items.id
    conn = sqlite3.connect('mercari.sqlite3')
    cur = conn.cursor()
    with conn:
        cur.execute("SELECT * FROM items INNER JOIN categories ON items.id = ?", (item_id,))
        items = cur.fetchall()
    conn.close()
    # Convert the item list to the appropriate format and return
    response = {
        "items": items
    }
    return response
