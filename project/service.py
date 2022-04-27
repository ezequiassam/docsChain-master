import base64
import hashlib
import io
from datetime import datetime as dt

import requests
from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from . import db
from .gdrive import gdrive_upload
from .models import Documento, RequestBlockchainError, DocumentExistError, DocumentNotFoundError

HOST_CHAIN = "http://127.0.0.1:5000"


def encode_base64(data: bytes):
    """
    Return base-64 encoded value of binary data.
    """
    return base64.b64encode(data)


def decode_base64(data: str):
    """
    Return decoded value of a base-64 encoded string.
    """
    return base64.b64decode(data.encode())


def get_pdf_data(filename):
    """
    Open pdf file in binary mode,
    return a string encoded in base-64.
    """
    with open(filename, 'rb') as file:
        return encode_base64(file.read())


def generate_hash_sha224(*args):
    hash_object = hashlib.sha224()
    # append the byte string
    for s in args:
        if isinstance(s, str):
            s = s.encode()
        hash_object.update(s)
    return hash_object.hexdigest()


def plot_pdf(file, codText):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawString(10, 5, f"Código de validação: {codText}")
    can.save()

    # movendo para o começo do StringIO buffer
    packet.seek(0)

    # criando um novo PDF com Reportlab
    new_pdf = PdfFileReader(packet)
    # lendo o PDF existente
    existing_pdf = PdfFileReader(file.stream)
    output = PdfFileWriter()

    # adicionando a "marca d'agua" (que é o novo pdf) em cada pagina existente
    for numPage in range(existing_pdf.getNumPages()):
        page = existing_pdf.getPage(numPage)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)

    # finalizando, salvadando o "output"
    output_stream = io.BytesIO()
    output.write(output_stream)
    output_stream.seek(0)
    return output_stream


def save_pdf(file, pdf_plot_base64, previous_hash, sha_hash, str_pdf, previous_validator):
    new_document = Documento(
        filename=secure_filename(file.filename),
        base64orig=str_pdf,
        base64plot=pdf_plot_base64,
        chain=previous_hash,
        sha=sha_hash,
        previousValidator=previous_validator,
        created=dt.now()
    )
    db.session.add(new_document)
    db.session.commit()


def process_pdf(file, str_pdf, existing_document=None):
    # gerando novo bloco e capturando hash
    try:
        response = requests.get(f"{HOST_CHAIN}/mine").json()
        previous_hash = response.get('previous_hash')
    except Exception as e:
        print(e)
        raise RequestBlockchainError()

    # gerando composição do bloco e base64
    sha_hash = generate_hash_sha224(str_pdf, previous_hash)

    # plotar no pdf
    pdf_plot_stream = plot_pdf(file, sha_hash)
    pdf_plot_base64 = encode_base64(pdf_plot_stream.getvalue()).decode()
    pdf_plot_stream.seek(0)

    previous_validator = None
    if existing_document:
        previous_validator = existing_document.sha
        existing_document.nextValidator = sha_hash
        db.session.commit()

    # upload para google drive
    gdrive_link = gdrive_upload(pdf_plot_stream, secure_filename(file.filename), sha_hash)

    # salvar e retornar pdf plotado
    save_pdf(file, pdf_plot_base64, previous_hash, sha_hash, str_pdf, previous_validator)
    return pdf_plot_stream


def process_new_pdf(file):
    str_pdf = encode_base64(file.stream.read()).decode()

    # validar com o banco se já existe
    existing_document = Documento.query.filter(
        or_(Documento.base64orig == str_pdf, Documento.base64plot == str_pdf)
    ).first()
    if existing_document:
        raise DocumentExistError()

    return process_pdf(file, str_pdf)


def update_pdf(file, code_hash):
    str_pdf = encode_base64(file.stream.read()).decode()
    existing_document = valid_code_hash(code_hash)
    if not existing_document:
        raise DocumentNotFoundError()

    return process_pdf(file, str_pdf, existing_document)


def valid_code_hash(code_hash):
    return Documento.query.filter(Documento.sha == code_hash).first()
