# app.py
import os
import pypandoc
from flask import Flask, request, send_file, render_template_string, flash, redirect, url_for
from werkzeug.utils import secure_filename
import tempfile
import uuid

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'md'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Checks if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

HTML_TEMPLATE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <title>Convertidor Markdown a Word</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', sans-serif; }
    .btn { @apply inline-block px-6 py-3 bg-blue-600 text-white font-medium text-sm leading-tight uppercase rounded-lg shadow-md hover:bg-blue-700 hover:shadow-lg focus:bg-blue-700 focus:shadow-lg focus:outline-none focus:ring-0 active:bg-blue-800 active:shadow-lg transition duration-150 ease-in-out cursor-pointer; }
    .file-input { @apply block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer border border-gray-300 rounded-lg p-2; }
  </style>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
  <div class="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
    <h1 class="text-2xl font-bold mb-6 text-center text-gray-800">Convertidor Markdown a Word (.docx)</h1>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="mb-4 p-4 rounded-lg {{ 'bg-red-100 text-red-700' if category == 'error' else 'bg-blue-100 text-blue-700' }}" role="alert">
            {{ message }}
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <form method="post" enctype="multipart/form-data" action="{{ url_for('upload_file') }}" class="space-y-6">
      <div>
        <label for="file" class="block mb-2 text-sm font-medium text-gray-700">Selecciona un archivo Markdown (.md):</label>
        <input type="file" name="file" id="file" class="file-input" accept=".md" required>
      </div>
      <div>
        <button type="submit" class="btn w-full">Convertir y Descargar</button>
      </div>
    </form>
    <p class="text-xs text-gray-500 mt-4 text-center">Desarrollado con Flask y Pandoc.</p>
  </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Renders the upload form."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload, conversion, and download."""
    if 'file' not in request.files:
        flash('No se encontró la parte del archivo.', 'error')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('No se seleccionó ningún archivo.', 'error')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        # Sanitize filename
        filename = secure_filename(file.filename)
        # Generate unique temporary paths
        _, md_ext = os.path.splitext(filename)
        unique_id = uuid.uuid4()
        input_md_path = os.path.join(tempfile.gettempdir(), f"{unique_id}{md_ext}")
        output_docx_path = os.path.join(tempfile.gettempdir(), f"{unique_id}.docx")
        output_filename = filename.rsplit('.', 1)[0] + '.docx'

        try:
            file.save(input_md_path)

            pypandoc.convert_file(input_md_path, 'docx', outputfile=output_docx_path, extra_args=['--standalone'])

            if not os.path.exists(output_docx_path):
                 raise Exception("Pandoc no pudo crear el archivo DOCX.")

            return send_file(
                output_docx_path,
                as_attachment=True,
                download_name=output_filename,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )

        except Exception as e:
            app.logger.error(f"Error en la conversión: {e}")
            flash(f'Error durante la conversión: {e}', 'error')
            return redirect(url_for('index'))
        finally:
            if os.path.exists(input_md_path):
                os.remove(input_md_path)
            if os.path.exists(output_docx_path):
                 pass

    else:
        flash('Tipo de archivo no permitido. Sube solo archivos .md.', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
