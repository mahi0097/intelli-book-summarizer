def convert_to_bullets(text:str) -> str:
    """
    convert plaint text summary to builet point formate.
    """
    if not text:
        return "" 
    
    #split sentence
    sentence = [s.strip() for s in text.split(".") if s.strip()]

    bullets = []
    for sentences in sentence:
        bullets.append(f".{sentences}")
    return "\n".join(bullets)
    
