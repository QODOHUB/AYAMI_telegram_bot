import re


def contains_only_russian_letters(input_string):
    pattern = r'^[а-яА-ЯёЁ]+$'
    return bool(re.match(pattern, input_string))
