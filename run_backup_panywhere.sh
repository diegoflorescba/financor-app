#!/bin/bash
cd /home/diegoaflores/financor-app
/home/diegoaflores/.virtualenvs/prestamos_env/bin/python backup_db.py >> /home/diegoaflores/financor-app/instance/backup.log 2>&1