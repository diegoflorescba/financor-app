#!/bin/bash

# Colores para los mensajes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Iniciando instalación de Financor...${NC}"

# Verificar si Homebrew está instalado
if ! command -v brew &> /dev/null; then
    echo -e "${BLUE}Instalando Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Agregar Homebrew al PATH
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Verificar la versión de Python
REQUIRED_VERSION="3.10.13"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')

if [ "$PYTHON_VERSION" != "$REQUIRED_VERSION" ]; then
    echo -e "${BLUE}Instalando Python $REQUIRED_VERSION...${NC}"
    
    # Instalar pyenv si no está instalado
    if ! command -v pyenv &> /dev/null; then
        brew install pyenv
        
        # Configurar pyenv
        echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
        echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
        echo 'eval "$(pyenv init -)"' >> ~/.zshrc
        
        source ~/.zshrc
    fi
    
    # Instalar Python 3.10.13
    pyenv install $REQUIRED_VERSION
    pyenv global $REQUIRED_VERSION
    
    # Verificar la instalación
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    if [ "$PYTHON_VERSION" != "$REQUIRED_VERSION" ]; then
        echo -e "${RED}Error: No se pudo instalar Python $REQUIRED_VERSION${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Python $REQUIRED_VERSION está instalado correctamente${NC}"

# Verificar si pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo -e "${BLUE}Instalando pip...${NC}"
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi

# Eliminar el entorno virtual existente si hay problemas
if [ -d "venv" ]; then
    echo -e "${BLUE}Eliminando entorno virtual anterior...${NC}"
    rm -rf venv
fi

# Crear nuevo entorno virtual
echo -e "${BLUE}Creando nuevo entorno virtual...${NC}"
python3 -m venv venv

# Verificar si el entorno virtual se creó correctamente
if [ ! -f "venv/bin/python3" ]; then
    echo -e "${RED}Error: No se pudo crear el entorno virtual${NC}"
    exit 1
fi

# Activar entorno virtual
echo -e "${BLUE}Activando entorno virtual...${NC}"
source venv/bin/activate

# Actualizar pip en el entorno virtual
echo -e "${BLUE}Actualizando pip...${NC}"
python3 -m pip install --upgrade pip

# Instalar dependencias
echo -e "${BLUE}Instalando dependencias...${NC}"
python3 -m pip install -r requirements.txt

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