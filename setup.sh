#!/bin/bash

# Colores para los mensajes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Iniciando instalación de Financor...${NC}"

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python3 no está instalado. Por favor, instala Python 3.8 o superior."
    exit 1
fi

# Verificar si pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "Pip3 no está instalado. Instalando pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creando entorno virtual...${NC}"
    python3 -m venv venv
fi

# Activar entorno virtual
echo -e "${BLUE}Activando entorno virtual...${NC}"
source venv/bin/activate

# Instalar dependencias
echo -e "${BLUE}Instalando dependencias...${NC}"
pip install -r requirements.txt

# Crear carpeta instance si no existe
if [ ! -d "instance" ]; then
    echo -e "${BLUE}Creando carpeta instance...${NC}"
    mkdir instance
fi

# Verificar si la base de datos existe
if [ ! -f "instance/prestamos.db" ]; then
    echo -e "${BLUE}Base de datos no encontrada. Inicializando...${NC}"
    python3 init_db.py
else
    echo -e "${BLUE}Base de datos existente encontrada. Continuando...${NC}"
fi

# Crear archivo de inicio
echo -e "${BLUE}Creando archivo de inicio...${NC}"
cat > run.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python3 app.py
EOF

# Dar permisos de ejecución
chmod +x run.sh
chmod +x setup.sh

echo -e "${GREEN}¡Instalación completada!${NC}"
echo -e "${GREEN}Para iniciar la aplicación, ejecuta: ./run.sh${NC}"