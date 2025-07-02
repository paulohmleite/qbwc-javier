import json
import requests
import os
from urllib.parse import quote
from PIL import Image
import io
import glob
import sys
sys.path.append('.')
from supabase import fetch_all_rows, bulk_insert

SUPABASE_URL = "https://ojybvaboxesqiutohbgw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9qeWJ2YWJveGVzcWl1dG9oYmd3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczOTA1OTMsImV4cCI6MjA2Mjk2NjU5M30.2cocq1cpXIin5YYIPAf6Xw8JaokDV-DPV1mB53EZGQk"
SUPABASE_PUBLIC_URL = f"{SUPABASE_URL}/storage/v1/object/public"


def compress_and_resize_image(input_path):
    # Print original size
    original_size = os.path.getsize(input_path)
    print(f"Original size: {original_size / 1024:.2f} KB")

    if original_size <= 500 * 1024:
        print("File is <= 500KB, skipping compression.")
        with open(input_path, 'rb') as f:
            return io.BytesIO(f.read())

    img = Image.open(input_path)
    img_format = img.format if img.format else 'PNG'
    # Resize to 20% width and height
    new_size = (max(1, img.width * 20 // 100), max(1, img.height * 20 // 100))
    img = img.resize(new_size, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    # Save with reasonable quality (default 75 for JPEG, 80 for PNG)
    if img_format.upper() == 'JPEG':
        img.save(buffer, format=img_format, optimize=True, quality=75)
    else:
        img.save(buffer, format=img_format, optimize=True, quality=80)
    buffer.seek(0)
    compressed_size = buffer.getbuffer().nbytes
    print(f"Compressed size: {compressed_size / 1024:.2f} KB")
    return buffer


def upload_image_to_supabase(image_path, file_name, listid, insert_db=True):
    compressed_image = compress_and_resize_image(image_path)
    bucket = "product-images"
    storage_url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{quote(file_name)}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "image/png",
        "x-upsert": "true"
    }
    resp = requests.post(storage_url, headers=headers, data=compressed_image)
    if resp.status_code in (200, 201):
        print(f"✅ Uploaded {file_name} to Supabase Storage.")
        image_url = f"{SUPABASE_PUBLIC_URL}/{bucket}/{quote(file_name)}"
    else:
        print(f"❌ Failed to upload image: {resp.status_code} {resp.text}")
        return
    if insert_db:
        table_url = f"{SUPABASE_URL}/rest/v1/images"
        headers_table = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "listid": listid,
            "image": image_url
        }
        resp2 = requests.post(table_url, headers=headers_table, data=json.dumps(data))
        if resp2.status_code in (200, 201):
            print(f"✅ Inserted image record for {file_name}.")
        else:
            print(f"❌ Failed to insert image record: {resp2.status_code} {resp2.text}")


def process_and_upload_all_images():
    # Load filter items
    with open('data/filter_items.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    # Fetch all existing images (by image url)
    existing_images = fetch_all_rows('images', 'image')
    existing_image_urls = set(existing_images.keys())

    records_to_insert = []
    for item in items:
        name = item.get('Name')
        listid = item.get('ListID')
        folder_path = os.path.join('data', 'images', name)
        if os.path.isdir(folder_path):
            image_files = glob.glob(os.path.join(folder_path, '*.*'))
            for image_path in image_files:
                if image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_name = f"{name}/{os.path.basename(image_path)}"
                    image_url = f"{SUPABASE_PUBLIC_URL}/product-images/{quote(file_name)}"
                    if image_url in existing_image_urls:
                        print(f"Skipping {file_name} (already exists in DB)")
                        continue
                    print(f"Uploading {image_path} as {file_name} for listid {listid}")
                    upload_image_to_supabase(image_path, file_name, listid, insert_db=False)
                    records_to_insert.append({"listid": listid, "image": image_url})
        else:
            print(f"No folder found for {name}, skipping.")

    # Bulk insert new image records
    bulk_insert('images', records_to_insert)


if __name__ == "__main__":
    process_and_upload_all_images()
