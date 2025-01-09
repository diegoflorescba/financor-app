from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import shutil

# Si modificas estos scopes, elimina el archivo token.json
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def backup_database():
    # Configurar la fecha para el nombre del archivo
    fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_original = './instance/prestamos.db'
    db_backup = f'./instance/prestamos_backup_{fecha_actual}.db'
    
    try:
        # Crear una copia de la base de datos
        shutil.copy2(db_original, db_backup)
        
        # Autenticación con Google Drive
        creds = None
        if os.path.exists('./instance/token.json'):
            creds = Credentials.from_authorized_user_file('./instance/token.json', SCOPES)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    './instance/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('./instance/token.json', 'w') as token:
                token.write(creds.to_json())

        # Crear el servicio de Drive
        service = build('drive', 'v3', credentials=creds)
        
        # Carpeta en Drive donde se guardarán los backups (reemplazar con tu ID de carpeta)
        folder_id = '1ry8RAwDuE81Ygp-cVTcdNnE9Dn9NcaBB'
        
        # Metadata del archivo
        file_metadata = {
            'name': os.path.basename(db_backup),
            'parents': [folder_id]
        }
        
        # Subir el archivo
        media = MediaFileUpload(db_backup, mimetype='application/x-sqlite3')
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f'Backup creado con éxito. File ID: {file.get("id")}')
        
        # Eliminar el archivo local de backup
        os.remove(db_backup)
        
    except Exception as e:
        print(f'Error durante el backup: {str(e)}')

if __name__ == '__main__':
    backup_database()