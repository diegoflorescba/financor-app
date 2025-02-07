#!/bin/bash

# Colores para los mensajes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Configurando Git y clonando repositorio...${NC}"

# Verificar si git está instalado
if ! command -v git &> /dev/null; then
    echo -e "${BLUE}Instalando git...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install git
    else
        sudo apt-get update
        sudo apt-get install -y git
    fi
fi

# Clonar el repositorio público si no estamos ya en el directorio
if [ ! -f "setup.sh" ]; then
    echo -e "${BLUE}Clonando repositorio...${NC}"
    git clone https://github.com/tu_usuario/prestamos_app.git
    cd prestamos_app
    echo -e "${BLUE}Cambiando a la rama 'andando'...${NC}"
    git checkout andando
else
    echo -e "${BLUE}Actualizando repositorio...${NC}"
    git checkout andando
    git pull origin andando
fi

echo -e "${GREEN}Configuración de Git completada!${NC}"