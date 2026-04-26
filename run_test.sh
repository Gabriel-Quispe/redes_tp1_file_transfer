#!/bin/bash
# Instala dependencias y corre tests BDD usando venv local

set -e

VENV_DIR="env"

# 1. Crear venv si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creando entorno virtual..."
    python3 -m venv $VENV_DIR
fi

# 2. Usar SIEMPRE el pip del venv
echo "==> Instalando dependencias..."
$VENV_DIR/bin/pip install --upgrade pip --quiet
$VENV_DIR/bin/pip install pytest pytest-bdd --quiet

# 3. Ejecutar tests con el python del venv
echo "==> Corriendo tests..."
$VENV_DIR/bin/python -m pytest tests/ -v --tb=short

echo "==> Listo."
