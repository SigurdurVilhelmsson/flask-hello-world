import os
from openai import OpenAI
import textract
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

client = OpenAI(
    api_key='sk-proj-UU55Vp5gbzbfy4Pn8p9JT3BlbkFJxMGSKxeiAd1LiT1LpzDJ',
)
GPT_MODEL = "gpt-4o"

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Set up logging
if not app.debug:
    file_handler = logging.FileHandler('error.log')
    file_handler.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)

# Also, add this to catch all unhandled exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
    return "Internal Server Error", 500



def extract_text(file_path):
    try:
        text = textract.process(file_path).decode('utf-8')
        return text
    except Exception as e:
        app.logger.error(f"Error extracting text: {e}")
        return None
def analyze_text(text):
    try:
        prompt = f"""
    Almennar leiðbeiningar fyrir skýrslugerð:
    1. Dagsetning framkvæmdar tilraunar: [Gefið upp dagsetningu]
    2. Heiti og númer tilraunar: [Heiti og númer]
    3. Upplýsingar um nemanda: [Nafn, bekkur, samstarfsfólk]
    4. Tilgangur: Stutt útskýring (1-2 setningar)
    5. Fræði:
        - Útskýring á lögmálum og reglum.
        - Innihaldið efnajöfnur og reikniformúlur.
        - Samfelldur texti sem styður niðurstöður.
    6. Tæki og efni: Listi yfir öll tæki og efni.
    7. Framkvæmd: Stutt lýsing á framkvæmd tilraunar.
    8. Niðurstöður:
        - Athuganir og mælingar í töfluformi ef mögulegt.
        - Útreikningar í töfluformi ef við á.
        - Allir útreikningar sem gerðir voru.
        - Línurit yfir niðurstöður ef við á.
        - Svör við spurningum úr vinnuseðli.
        - Sverta og undirstrika lykilniðurstöður.
    9. Lokaorð:
        - Draga saman niðurstöður.
        - Ræða áreiðanleika og óvissu.
    10. Undirskrift höfundar: [Undirskrift]
    11. Lokaúttekt: Tryggja samhengið og heildstætt yfirbragð skýrslu.

    Skýrsla:
    {text}

    Vinsamlegast yfirfarið skýrsluna byggt á almennum leiðbeiningum sem gefnar eru hér að ofan og gefið endurgjöf."""
        messages=[
                {"role": "system", "content": "Þú ert aðstoðarkennar í efnafræði sem hjálpar til við að fara yfir efnafræðiskýrslur. Þú talar íslensku."},
                {"role": "user", "content": prompt}
            ]
        response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages
        )
        feedback = response.choices[0].message.content.strip()
        return feedback
    except Exception as e:
        app.logger.error(f"Error analyzing text: {e}")
        app.logger.error(e, exc_info=True)
        return None

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and file.filename.endswith(('.doc', '.docx', '.pdf')):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            text = extract_text(file_path)
            if text is None:
                return "Error processing file", 500
            feedback = analyze_text(text)
            if feedback is None:
                return "Error analyzing text", 500
            return render_template('upload.html', feedback=feedback)
    return render_template('upload.html')

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
