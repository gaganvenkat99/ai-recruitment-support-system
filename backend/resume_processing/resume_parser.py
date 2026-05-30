def clean_text(text):
    return text.lower().replace("\n", " ").strip()


# ✅ FINAL FIXED PARSER
async def parse_resume(file):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    text = clean_text(text)

    return text