#!/bin/bash
# Instala dependencias y corre todos los tests BDD

set -e

echo "==> Instalando dependencias..."
pip install pytest pytest-bdd --quiet

echo "==> Corriendo todos los features..."
pytest tests/ -v --tb=short 2>&1

echo "==> Listo."
