import os
import io
from analyze import process_image_data
from flask import Flask, render_template, redirect, request, send_file


app = Flask(__name__)

@app.route('/')
def index():
    return redirect("upload_image")

@app.route('/upload_image', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No uploaded file')
            redirect(request.url)
        f = request.files['file']
        if f.filename == '':
            flash('No uploaded file')
            redirect(request.url)
        result_image_data = process_image_data(f.read(), ".png")
        return send_file(io.BytesIO(result_image_data),
                         attachment_filename='gymranks.png',
                         mimetype='image/png')

    return render_template("upload_image.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0')
