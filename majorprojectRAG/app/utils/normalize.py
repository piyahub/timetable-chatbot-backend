def normalize(text: str) -> str:
    return (
        text.lower()
        .replace(".", "")
        .replace("-", "")
        .replace("_", "")
        .replace("+", "")
        .replace(" ", "")
    )
