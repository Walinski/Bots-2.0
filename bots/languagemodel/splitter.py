import asyncio
import re

async def retrieve_sentences(raw_response, min_length: int = 80, max_length: int = 95):

    regex_sentences = re.split(r'(?<!\b[A-Z]\.)(?<=[.!?])\s+(?=[A-Z])|\n\n', raw_response)  # splits into sentences using regular expressions
    buffer = ""
    sentences = []

    def split_by_length(sentence, max_length):
        words = sentence.split()  # splits into words with spaces preserving full words
        chunks, chunk = [], []

        for word in words:
            # Add word to chunk if it doesn't exceed max_length
            if sum(len(w) + 1 for w in chunk) + len(word) <= max_length:
                chunk.append(word)
            else:
                chunks.append(" ".join(chunk))  # Add the current chunk to chunks
                chunk = [word]  # Start a new chunk with the word

        # Add the remaining chunk
        if chunk:
            chunks.append(" ".join(chunk))
        
        return chunks

    for sentence in regex_sentences:
        sentence = (buffer + " " + sentence.strip()).strip() if buffer else sentence.strip()
        buffer = ""  # Clear any buffer after use

        # If the sentence is smaller than min_length, keep it in the buffer
        if len(sentence) < min_length:
            buffer += " " + sentence
            continue

        # Split long sentences into chunks that don't exceed max_length
        subsentences = split_by_length(sentence, max_length)

        for subsentence in subsentences:
            if len(subsentence) >= min_length:
                sentences.append(subsentence)
            else:
                # If it's smaller than min_length, buffer it for next loop
                buffer += " " + subsentence

    if buffer.strip():
        sentences.append(buffer.strip())  

    return sentences

if __name__ == "__main__":
    raw_response = input("Enter Raw Response: ")
    cleaned = asyncio.run(retrieve_sentences(raw_response))
    print(cleaned)
