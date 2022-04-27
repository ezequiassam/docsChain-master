import os

from .models import GDriveUploadError

GDRIVE_FOLDER_ID = '1REtUC7xUWNxmiEYQz9REO7_MM3OPhdiq'
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
