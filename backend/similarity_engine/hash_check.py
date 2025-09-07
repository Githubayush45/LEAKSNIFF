from PIL import Image
import imagehash
import os

# Folders

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATCH_CONFIDENTIAL = os.path.join(BASE_DIR, "match_confidential")
DOWNLOADED_IMAGES = os.path.join(BASE_DIR, "downloaded_images")


# Step 1: build reference hashes for internal confidential images
def build_reference_hashes():
    hashes = {}
    for file in os.listdir(MATCH_CONFIDENTIAL):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            path = os.path.join(MATCH_CONFIDENTIAL, file)
            try:
                img = Image.open(path)
                hash_val = imagehash.phash(img)  # perceptual hash
                hashes[file] = hash_val
                print(f"🔒 Hashed internal asset: {file} -> {hash_val}")
            except Exception as e:
                print(f"❌ Error hashing {file}: {e}")
    return hashes

# Step 2: check similarity between a new image and reference hashes
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

if __name__ == "__main__":
    print("🚀 Starting LeakSniff hash check...")

    # Build hashes from confidential assets
    refs = build_reference_hashes()

    # Scan all downloaded images
    for file in os.listdir(DOWNLOADED_IMAGES):
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            test_img = os.path.join(DOWNLOADED_IMAGES, file)
            result, match, diff = check_image_leak(test_img, refs)
            if result:
                print(f"⚠️ Leak detected! {file} is similar to {match} (difference {diff})")
            else:
                print(f"✅ {file} has no match.")
