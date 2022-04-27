import os

import time

from .models import GDriveUploadError, GDriveBackupError

GDRIVE_FOLDER_ID = '1REtUC7xUWNxmiEYQz9REO7_MM3OPhdiq'
GDRIVE_FOLDER_BACKUPS_ID = '1OcfS1UWNRF8gDs1rkV-DcuvJ4JbYwyay'
MAX_SAVE_BACKUPS = 10
ENCODING = 'LATIN1'
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


# Login to Google Drive and create drive object
def connect_google_drive_api():
    # use Gdrive API to access Google Drive
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive

    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # client_secrets.json need to be in the same directory as the script

    drive = GoogleDrive(gauth)

    return drive


drive = connect_google_drive_api()


def gdrive_upload(file_stream, filename, str_validator_hash):
    # my_file = os.path.join(THIS_FOLDER, 'teste.txt')
    # file = open(my_file, 'r')
    # fn = os.path.basename(file.name)
    try:
        fn = f"{str_validator_hash}-{filename}"
        file_drive = drive.CreateFile(
            {'title': fn, 'mimeType': 'application/pdf', 'parents': [{'id': GDRIVE_FOLDER_ID}]})
        file_drive.SetContentString(file_stream.getvalue().decode(ENCODING), ENCODING)
        file_drive.Upload()

        permission = file_drive.InsertPermission({
            'type': 'anyone',
            'value': 'anyone',
            'role': 'reader'})

        return file_drive['alternateLink']
    except Exception as e:
        print(e)
        raise GDriveUploadError()


def gdrive_backup_database():
    print('Iniciando backup do banco de dados')
    my_file = os.path.join(THIS_FOLDER, 'dockchain.db')
    if not os.path.isfile(my_file):
        print('Não foi localizado o banco de dados')
        return
    try:
        file = open(my_file, 'rb')
        filename = f'{time.strftime("%Y-%m-%d-%H:%M:%S")}_backup-dockchain.db'
        file_drive = drive.CreateFile(
            {'title': filename, 'mimeType': 'application/db', 'parents': [{'id': GDRIVE_FOLDER_BACKUPS_ID}]})
        file_drive.SetContentString(file.read().decode(ENCODING), ENCODING)
        file_drive.Upload()

        print(file_drive['alternateLink'])
        print('Backup do banco de dados realizado com sucesso')
    except Exception as e:
        print(e)
        raise GDriveBackupError()


def gdrive_clean_backups():
    print('Limpando a pasta de backup')
    file_list = drive.ListFile(
        {'q': f"'{GDRIVE_FOLDER_BACKUPS_ID}' in parents and trashed=false", 'orderBy': 'modifiedDate asc'}).GetList()
    size_files = len(file_list)
    if size_files <= MAX_SAVE_BACKUPS:
        return
    for file in file_list:
        file.Trash()
        size_files -= 1
        if size_files <= MAX_SAVE_BACKUPS:
            break

    print('Limpeza da pasta de backup concluido')
