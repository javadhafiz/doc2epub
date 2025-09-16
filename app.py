from flask import Flask, request, send_file, render_template
import pdfplumber
from ebooklib import epub
import tempfile, os

app = Flask(__name__, template_folder="templates")
UPLOAD_FOLDER = "/tmp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        lang = request.form.get("lang", "en")
        if uploaded_file:
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
            uploaded_file.save(file_path)
            try:
                epub_file = convert_pdf_to_epub(file_path, lang)
            except Exception as e:
                return f"<h2>Error converting PDF:</h2><pre>{e}</pre>"
            return send_file(epub_file, as_attachment=True, download_name="converted.epub")
    return render_template("index.html")

def convert_pdf_to_epub(file_path, lang='en'):
    book = epub.EpubBook()
    book.set_title("Converted PDF Book" if lang=='en' else "كتاب PDF المحول")
    book.set_language(lang)

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                chapter = epub.EpubHtml(
                    title=f"Page {i}" if lang=='en' else f"صفحة {i}",
                    file_name=f"chapter_{i}.xhtml",
                    lang=lang
                )
                direction = 'rtl' if lang=='ar' else 'ltr'
                chapter.content = f"""
                <div dir="{direction}" style="font-family: Arial, Tahoma, sans-serif; color: #1f4e79;">
                <h1>{'Page' if lang=='en' else 'صفحة'} {i}</h1>
                <p>{text.replace(chr(10), '<br>')}</p>
                </div>
                """
                book.add_item(chapter)
                book.spine.append(chapter)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".epub", dir=UPLOAD_FOLDER)
    epub.write_epub(temp_file.name, book)
    temp_file.close()
    return temp_file.name

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
