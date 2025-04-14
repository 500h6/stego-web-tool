from flask import Flask, request, render_template, send_file
from PIL import Image
import os

app = Flask(__name__)

# مجلدات التحميل والإخراج
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# دالة لإخفاء النص في الصورة
def hide_text(image_path, text, output_path):
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    width, height = img.size

    # تحويل النص إلى ثنائي
    binary_text = ''.join(format(ord(c), '08b') for c in text)
    binary_text += '11111111'  # علامة نهاية النص

    index = 0
    for y in range(height):
        for x in range(width):
            if index < len(binary_text):
                r, g, b = pixels[x, y]
                # تعديل أقل بت في القناة الحمراء
                r = (r & ~1) | int(binary_text[index])
                pixels[x, y] = (r, g, b)
                index += 1
            else:
                break
        if index >= len(binary_text):
            break

    img.save(output_path, 'PNG')
    return output_path

# دالة لاستخراج النص من الصورة
def extract_text(image_path):
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    width, height = img.size

    binary_text = ''
    for y in range(height):
        for x in range(width):
            r, _, _ = pixels[x, y]
            binary_text += str(r & 1)
            # التحقق من علامة النهاية
            if len(binary_text) >= 8 and binary_text[-8:] == '11111111':
                binary_text = binary_text[:-8]
                text = ''
                for i in range(0, len(binary_text), 8):
                    byte = binary_text[i:i+8]
                    text += chr(int(byte, 2))
                return text
    return "لا يوجد نص مخفي"

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    output_file = ''
    extracted_text = ''

    if request.method == 'POST':
        action = request.form.get('action')

        # إخفاء النص
        if action == 'hide':
            if 'image' not in request.files or not request.form.get('text'):
                message = "يرجى تحميل صورة وإدخال نص"
            else:
                image = request.files['image']
                text = request.form['text']

                if image.filename == '':
                    message = "يرجى تحميل صورة صحيحة"
                else:
                    image_path = os.path.join(UPLOAD_FOLDER, image.filename)
                    image.save(image_path)

                    output_path = os.path.join(OUTPUT_FOLDER, 'output.png')
                    hide_text(image_path, text, output_path)
                    output_file = 'output.png'
                    message = "تم إخفاء النص بنج819اح!"

        # استخراج النص
        elif action == 'extract':
            if 'image_extract' not in request.files:
                message = "يرجى تحميل صورة"
            else:
                image = request.files['image_extract']
                if image.filename == '':
                    message = "يرجى تحميل صورة صحيحة"
                else:
                    image_path = os.path.join(UPLOAD_FOLDER, image.filename)
                    image.save(image_path)
                    extracted_text = extract_text(image_path)
                    message = "تم استخراج النص بنجاح!"

    return render_template('index.html', message=message, output_file=output_file, extracted_text=extracted_text)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)