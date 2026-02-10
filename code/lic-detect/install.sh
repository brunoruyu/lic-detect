#!/bin/bash

echo "🚀 Instalando Licitación Detector..."
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    echo "✓ Virtual environment creado"
else
    echo "✓ Virtual environment ya existe"
fi

# Activate venv
echo "🔧 Activando venv..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip setuptools wheel

# Install package in editable mode
echo "📥 Instalando package en modo desarrollo..."
pip install -e .
echo "✓ Package instalado"

# Install dev dependencies
echo "📥 Instalando dependencias de desarrollo..."
pip install -e ".[dev]"
echo "✓ Dependencias de desarrollo instaladas"

# Create directories
echo "📁 Creando directorios de trabajo..."
mkdir -p logs data/historical docs
echo "✓ Directorios creados"

# Create .env template if not exists
if [ ! -f ".env" ]; then
    echo "📝 Creando template .env..."
    cp .env.example .env
    echo "✓ Template .env creado - CONFIGURAR CON TUS CREDENCIALES"
else
    echo "✓ .env ya existe"
fi

echo ""
echo "✅ Instalación completada!"
echo ""
echo "📋 El package está instalado como 'licitacion-detector'"
echo "   Puedes usarlo desde cualquier lugar con:"
echo "   $ licitacion-detector --help"
echo "   $ licitacion-quickstart"
echo ""
echo "📋 O importarlo en Python:"
echo "   >>> from licitacion_detector import TesoritacionScraper"
echo "   >>> from licitacion_detector import MarketDataProvider"
echo ""
echo "📋 Próximos pasos:"
echo "1. Editar .env con tus credenciales"
echo "2. Ejecutar: licitacion-quickstart"
echo "3. Ver README.md para más detalles"
echo ""
echo "🎯 Para activar el venv en el futuro:"
echo "   source venv/bin/activate"
