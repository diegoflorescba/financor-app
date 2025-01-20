from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import shutil

# Definir los scopes necesarios
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def backup_database():
    # Configurar la fecha para el nombre del archivo
    fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_original = './instance/prestamos.db'
    db_backup = f'./instance/prestamos_backup_{fecha_actual}.db'
    
    try:
        # Crear una copia de la base de datos
        shutil.copy2(db_original, db_backup)
        
        # Cargar credenciales desde el archivo de cuenta de servicio
        creds = Credentials.from_service_account_file(
            './instance/service-account.json',
            scopes=SCOPES
        )

        # Crear el servicio de Drive
        service = build('drive', 'v3', credentials=creds)
        
        # ID de la carpeta en Drive donde se guardarán los backups
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