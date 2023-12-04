def paragraph_is_lengthy(paragraph):
    content = paragraph.text.strip()
    if content and len(content) > 20: 
        return True
    else:
        return False

def count_words(text_block):
    words = text_block.split()
    word_count = len(words)
    return word_count

def extract_words(text_block, first_count=1000, last_count=100):
    # Split the text block into words using whitespace as a delimiter
    words = text_block.split()
    
    # Extract the first 1000 words and the last 100 words
    first_words = ' '.join(words[:first_count])
    last_words = ' '.join(words[-last_count:])
    
    # Concatenate the two parts into one text
    concatenated_text = first_words + ' ' + last_words
    
    return concatenated_text