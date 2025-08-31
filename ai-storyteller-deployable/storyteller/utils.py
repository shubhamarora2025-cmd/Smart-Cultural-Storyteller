import os
import io
import zipfile

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def save_text_file(path: str, text: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def zip_folder(folder_path: str, out_bytes_io: io.BytesIO):
    with zipfile.ZipFile(out_bytes_io, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_path):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, folder_path)
                zf.write(full, arcname=rel)
