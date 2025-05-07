import random
import string
import math

def generate_random_string(length: int = 10, alpha: bool = True, digits: bool = True, specials: bool = True) -> str:
    """
    Generate a random string.
    :param length:
    :param alpha: alphabet chars
    :param digits: digits
    :param specials: some special characters
    :return: random string
    """
    characters = ""
    if alpha:
        characters = characters + string.ascii_letters
    if digits:
        characters = characters + string.digits
    if specials:
        characters = characters + "-_*()^%$#!{}[]+;:/" # can be string.punctuation but don't want to use hairy
    char_count = len(characters)

    # Make a large enough random int to cover all of length
    bits_needed = math.ceil(math.log2(char_count ** length))
    rand_int = random.getrandbits(bits_needed)

    result = ""
    for _ in range(length):
        rand_int, index = divmod(rand_int, char_count)
        result += characters[index]

    return result
