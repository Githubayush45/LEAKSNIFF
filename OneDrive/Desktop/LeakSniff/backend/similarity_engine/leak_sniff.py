import os
from PIL import Image
import imagehash
import pytesseract
from difflib import SequenceMatcher

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'



# =========================
# Paths
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERNAL_ASSETS = os.path.join(BASE_DIR, "downloaded_images")
DOWNLOADED_IMAGES = os.path.join(BASE_DIR, "downloaded_images")

# =========================
# 1. HASH CHECK FUNCTIONS
# =========================
def build_reference_hashes():
    hashes = {}
    for file in os.listdir(INTERNAL_ASSETS):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            path = os.path.join(INTERNAL_ASSETS, file)
            try:
                img = Image.open(path)
                hash_val = imagehash.phash(img)  # perceptual hash
                hashes[file] = hash_val
                print(f"🔒 Hashed internal asset: {file} -> {hash_val}")
            except Exception as e:
                print(f"❌ Error hashing {file}: {e}")
    return hashes

def check_image_leak(image_path, reference_hashes, threshold=5):
    try:
        img = Image.open(image_path)
        img_hash = imagehash.phash(img)
        for ref_file, ref_hash in reference_hashes.items():
            diff = img_hash - ref_hash  # Hamming distance
            if diff <= threshold:
                return True, ref_file, diff
        return False, None, None
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}")
        return False, None, None

# =========================
# 2. OCR KEYWORD SCAN
# =========================
CONFIDENTIAL_KEYWORDS = ["confidential", "top secret", "internal use only", "do not distribute"]

def contains_confidential_keywords(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        if not text:
            return False, None
        text = text.lower()
        for keyword in CONFIDENTIAL_KEYWORDS:
            if keyword in text:
                return True, keyword
        return False, None
    except Exception as e:
        print(f"❌ OCR error on {image_path}: {e}")
        return False, None


# =========================
# 3. OCR TEXT SIMILARITY CHECK
# =========================
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




def is_text_similar(text1, text2, threshold=0.75):
    ratio = SequenceMatcher(None, text1, text2).ratio()
    return ratio >= threshold, ratio

def build_reference_texts():
    texts = {}
    for file in os.listdir(INTERNAL_ASSETS):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            path = os.path.join(INTERNAL_ASSETS, file)
            text = extract_text(path)
            if text:
                texts[file] = text
                print(f"📝 Extracted text from internal asset: {file}")
    return texts

def check_text_leak(image_path, reference_texts, threshold=0.75):
    new_text = extract_text(image_path)
    if not new_text:
        return False, None, None
    for ref_file, ref_text in reference_texts.items():
        similar, ratio = is_text_similar(new_text, ref_text, threshold)
        if similar:
            return True, ref_file, ratio
    return False, None, None

# =========================
# MAIN DRIVER
# =========================
if __name__ == "__main__":
    print("🚀 Starting LeakSniff (hash + OCR keyword + OCR similarity)...")

    # Build internal references
    reference_hashes = build_reference_hashes()
    reference_texts = build_reference_texts()

    # Scan all downloaded images
        # Scan all downloaded images
    for file in os.listdir(DOWNLOADED_IMAGES):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            test_img = os.path.join(DOWNLOADED_IMAGES, file)
            print(f"\n🔍 Scanning {file}...")

            found = False  # track if any issue detected

            # 1. Hash check
            result, match, diff = check_image_leak(test_img, reference_hashes)
            if result:
                print(f"⚠️ Leak detected via HASH! {file} matches {match} (difference {diff})")
                found = True

            # 2. Keyword check
            keyword_found, keyword = contains_confidential_keywords(test_img)
            if keyword_found:
                print(f"⚠️ Leak detected via KEYWORD! {file} contains '{keyword}'")
                found = True

            # 3. OCR text similarity
            text_match, ref_file, ratio = check_text_leak(test_img, reference_texts)
            if text_match:
                print(f"⚠️ Leak detected via TEXT SIMILARITY! {file} is {ratio*100:.1f}% similar to {ref_file}")
                found = True

            if not found:
                print(f"✅ {file} has no match.")
