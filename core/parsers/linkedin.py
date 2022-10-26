
def linkedin_se_name_parser(text):
    try:
        name, _ = text.split('-', 1)
    except ValueError:
        try:
            name, _ = text.split('|', 1)
        except ValueError:
            return ('', '')

    parts = name.split()
    if len(parts) == 2:
        first, last = parts

    elif len(parts) == 3:
        first, middle, last = parts
        if middle.endswith(','):
            last = middle[:-1]
        elif first.endswith('.'):
            first = middle
        elif last.endswith(')'):
            last = middle

    elif len(parts) >= 4:
        first = parts[0]
        middle = parts[1]
        last = parts[2]

        if middle.endswith(','):
            last = middle[:-1]
        elif last.isupper():
            last = middle
        elif last.endswith(','):
            last = last[:-1]

    return first, last
