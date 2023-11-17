def paragraph_is_lengthy(paragraph):
    content = paragraph.text.strip()
    if content and len(content) > 20: 
        return True
    else:
        return False

def text_is_lengthy(text_block):
    pass