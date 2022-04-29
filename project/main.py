import io
import json

from flask import Blueprint, url_for
from flask import request, flash, send_file, render_template
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename, redirect

from .models import Documento, CustomError
from .service import process_new_pdf, valid_code_hash, update_pdf, decode_base64

ALLOWED_EXTENSION = {'pdf'}
main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template("index.html")


@main.route('/profile')
@login_required
def profile():
    return render_template("profile.html", name=current_user.name)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSION


@main.route('/uploader')
@login_required
def uploader():
    return render_template("upload.html")


@main.route('/uploader', methods=['POST'])
@login_required
def uploader_post():
    if 'file' not in request.files:
        flash('Não foi encontrado o arquivo')
        return redirect(url_for('main.uploader'))
    file = request.files['file']
    if file.filename == '':
        flash('Nenhum arquivo selecionado')
        return redirect(url_for('main.uploader'))
    if not allowed_file(file.filename):
        flash('Selecione apenas arquivos tipos .pdf')
        return redirect(url_for('main.uploader'))
    try:
        pdf_plot = process_new_pdf(file)
        filename = secure_filename(file.filename)
        return send_file(pdf_plot, attachment_filename=filename)
    except Exception as ex:
        valid_message_exception(ex)
        return redirect(url_for('main.uploader'))


@main.route('/update-doc')
@login_required
def update_doc():
    return render_template("update_doc.html")


@main.route('/update-doc', methods=['POST'])
@login_required
def update_doc_post():
    file = request.form.get('file')
    code_hash = request.form.get('code')
    if not file:
        flash('Não foi encontrado o arquivo')
        return redirect(url_for('main.update_doc'))
    if not code_hash:
        flash('Informe corretamente o código de validação')
        return redirect(url_for('main.update_doc'))
    if file.filename == '':
        flash('Nenhum arquivo selecionado')
        return redirect(url_for('main.update_doc'))
    if not allowed_file(file.filename):
        flash('Selecione apenas arquivos tipos .pdf')
        return redirect(url_for('main.update_doc'))
    try:
        pdf_plot = update_pdf(file, code_hash)
        return send_file(pdf_plot, attachment_filename=secure_filename(file.filename))
    except Exception as e:
        valid_message_exception(e)
        return redirect(url_for('main.update_doc'))


@main.route('/valid', methods=['POST'])
@login_required
def valid_code():
    code_hash = request.form.get('code')
    if not code_hash:
        flash('Por favor informe o código corretamente', 'error')
        return redirect(url_for('main.index'))

    existing_document = valid_code_hash(code_hash)
    if not existing_document:
        flash('Não foi encontrado documento para esse código', 'error')
        return redirect(url_for('main.index'))

    flash('Documento validado com sucesso!')
    flash(existing_document.alternateLinkGDrive)
    return redirect(url_for('main.index'))


@main.route('/docs-all', methods=['GET'])
@login_required
def get_all():
    docs = Documento.query.all()
    l = [d.toDict() for d in docs]
    j = json.dumps(l)
    return j


@main.route('/getdoc', methods=['GET'])
@login_required
def get_pdf():
    args = request.args
    doc = Documento.query.filter(Documento.sha == args.get('key')).first()
    if not doc:
        flash('Não foi encontrado documento', 'error')
        return redirect(url_for('main.index'))
    stream = io.BytesIO()
    stream.write(decode_base64(doc.base64plot))
    stream.seek(0)
    return send_file(stream, attachment_filename=secure_filename(doc.filename))


def valid_message_exception(error):
    if isinstance(error, CustomError):
        flash(str(error))
    else:
        print(error)
        flash('Não foi possivel processar a operação')
