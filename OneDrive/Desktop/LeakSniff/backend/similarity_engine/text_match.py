from rapidfuzz import fuzz

def compare_texts(text1, text2, threshold=80):
    """
    Compare 2 OCR texts and return similarity percentage + leak flag.
    Uses token_set_ratio for more robust matching.
    """
    score = fuzz.token_set_ratio(text1, text2)
    is_leak = score >= threshold
    return score, is_leak
