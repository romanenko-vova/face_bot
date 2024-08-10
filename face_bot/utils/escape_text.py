def escape_text(text):
    escape_chars = [
        "-",
        "~",
        "`",
        ">",
        "#",
        "+",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text
