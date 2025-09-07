from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import json

from similarity_engine.leak_sniff import extract_text, build_reference_texts, check_text_leak, contains_confidential_keywords
from similarity_engine.text_match import compare_texts
from similarity_engine.hash_check import build_reference_hashes, check_image_leak



app = Flask(__name__)

CORS(app)  # Enable CORS for all routes

@app.route('/check_image', methods=['POST'])
def check_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image file selected'}), 400

    # Save the uploaded image to a temporary file (in memory, not persistent)
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp:
        file.save(temp.name)
        temp_path = temp.name
    print(f"Saved uploaded image to temporary file {temp_path}")



    try:
        print(f"[DEBUG] Received image for check: {temp_path}")
        # Build references from downloaded_images
        reference_texts = build_reference_texts()

        # Build reference hashes from match_confidential
        reference_hashes = build_reference_hashes()

        # Extract OCR text
        ocr_text = extract_text(temp_path)
        print(f"OCR text: {repr(ocr_text)}")
        
        # Check for confidential keywords
        keyword_found, keyword = contains_confidential_keywords(temp_path)
        
        # Check text similarity
        text_match, text_ref, text_ratio = check_text_leak(temp_path, reference_texts)

        # Check image hash similarity
        hash_leak, hash_match, hash_diff = check_image_leak(temp_path, reference_hashes)

        # Prepare response
        results = {
            'hash_check': {
                'leak_detected': hash_leak,
                'matched_file': hash_match,
                'difference': hash_diff
            },
            'ocr_text': ocr_text,
            'keyword_check': {
                'keyword_found': keyword_found,
                'keyword': keyword
            },
            'text_similarity': {
                'similar': text_match,
                'matched_file': text_ref,
                'similarity_ratio': text_ratio
            }
        }

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# New endpoint for UI text similarity check
@app.route('/check_confidential_text', methods=['POST'])
def check_confidential_text():
    data = request.get_json()
    ui_text = data.get('ui_text', None)
    if not ui_text:
        return jsonify({'error': 'No UI text provided'}), 400

    # Load OCR texts from JSON file
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DOWNLOADED_IMAGES = os.path.join(BASE_DIR, "downloaded_images")
    ocr_texts_path = os.path.join(DOWNLOADED_IMAGES, "ocr_texts.json")

    # Load existing OCR texts or initialize empty dict
    try:
        with open(ocr_texts_path, 'r') as f:
            ocr_texts = json.load(f)
    except FileNotFoundError:
        ocr_texts = {}

    # Check for new images not in OCR texts and update
    updated = False
    for file in os.listdir(DOWNLOADED_IMAGES):
        if file.lower().endswith((".png", ".jpg", ".jpeg")) and file not in ocr_texts:
            img_path = os.path.join(DOWNLOADED_IMAGES, file)
            text = extract_text(img_path)
            ocr_texts[file] = text if text else ""
            updated = True

    # Save updated OCR texts if changed
    if updated:
        with open(ocr_texts_path, 'w') as f:
            json.dump(ocr_texts, f, indent=4)


    from rapidfuzz import fuzz
    confidential = False
    matched_file = None
    highest_score = 0
    ui_text_norm = ui_text.strip().lower()
    for file, img_text in ocr_texts.items():
        if img_text:
            img_text_norm = img_text.strip().lower()
            # Use fuzz.ratio for strict matching
            score = fuzz.ratio(ui_text_norm, img_text_norm)
            if score > highest_score:
                highest_score = score
                matched_file = file
            if score >= 95:
                confidential = True
                break
    return jsonify({
        'confidential': confidential,
        'matched_file': matched_file,
        'similarity_score': highest_score
    })


if __name__ == '__main__':
    app.run(debug=True)
