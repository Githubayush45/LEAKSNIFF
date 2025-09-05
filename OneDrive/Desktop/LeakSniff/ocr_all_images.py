import os
import json
from PIL import Image
import pytesseract


def extract_text(image_path):
    try:
        print(f"[DEBUG] Opening image for OCR: {image_path}")
        img = Image.open(image_path)
        print(f"[DEBUG] Image opened successfully. Running pytesseract...")
        text = pytesseract.image_to_string(img)
        clean_text = text.strip()
        print(f"📝 OCR extracted from {os.path.basename(image_path)}: {clean_text[:100]}...")
        if clean_text == "":
            print(f"[ERROR] OCR returned empty string for {image_path}")
            return None
        return clean_text
    except Exception as e:
        print(f"❌ OCR failed for {image_path}: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    downloaded_images_dir = "downloaded_images"
    ocr_texts = {}
    for file in os.listdir(downloaded_images_dir):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join(downloaded_images_dir, file)
            print(f"\n🔍 Processing {file}...")
            ocr_text = extract_text(img_path)
            if ocr_text:
                print(f"OCR Text from {file}:\n{ocr_text}")
                ocr_texts[file] = ocr_text
            else:
                print(f"No OCR text extracted from {file}")
                ocr_texts[file] = ""

    # Save OCR texts to JSON file
    ocr_texts_path = os.path.join(downloaded_images_dir, "ocr_texts.json")
    with open(ocr_texts_path, 'w') as f:
        json.dump(ocr_texts, f, indent=4)
    print(f"\n📁 OCR texts saved to {ocr_texts_path}")
