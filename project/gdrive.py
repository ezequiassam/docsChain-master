import os

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from .models import GDriveUploadError

GDRIVE_FOLDER_ID = '1REtUC7xUWNxmiEYQz9REO7_MM3OPhdiq'
ENCODING = 'LATIN1'
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
# Login to Google Drive and create drive object
g_login = GoogleAuth()
g_login.LocalWebserverAuth()
drive = GoogleDrive(g_login)


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
        GDriveUploadError()
