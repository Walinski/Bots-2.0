# External Imports
from better_profanity import profanity

# Package Imports
from . import logger

profanity.load_censor_words()

OBFUSCATION_PATTERNS = {
    'a': ['@', '4', '/\\'],
    'e': ['3'],
    'i': ['ia', '1', '!', '|'],
    'o': ['0', 'a'],
    'oo': ['ew'],
    's': ['$', '5', 'z'],
    'l': ['1', '|'],
    't': ['7'],
    'g': ['9'],
    'b': ['8'],
    'c': ['k'],
    'u': ['*', 'aw'],
    'f': ['ph'],
    'gg': ['wg']
}

def deobfuscate_word(word):
    if word in ['can']:
        return word
    for letter, replacements in OBFUSCATION_PATTERNS.items():
        for replacement in replacements:
            word = word.replace(replacement, letter)
    return word

async def contains_badword(question: str):

    if profanity.contains_profanity(question):
        logger.info(f"Profane word in: {question}")
        return True

    deobfuscated_query = ''.join(deobfuscate_word(char) for char in question)

    # Check the deobfuscated version
    if profanity.contains_profanity(deobfuscated_query):
        logger.info(f"'{question}' deobfuscated as '{deobfuscated_query}'")
        return True

    custom_words = []

    # Check if any custom words are contained in the deobfuscated query
    profanities = [str(word) for word in list(profanity.CENSOR_WORDSET) + custom_words]
    for bad_word in profanities:
        if bad_word in deobfuscated_query:
            logger.info(f"Profane word '{bad_word}' found in query '{deobfuscated_query}'")
            return True

    return False
