#!/usr/bin/env python3
"""Script para configurar la carpeta de descarga de ytdl-helper."""

import os
import sys
from pathlib import Path


def main():
    """Configurar la carpeta de descarga."""
    print("📁 Configurando carpeta de descarga para ytdl-helper")
    print("=" * 50)
    
    # Obtener el directorio del proyecto
    project_dir = Path(__file__).parent.parent
    download_dir = project_dir / "download"
    
    # Crear la carpeta si no existe
    download_dir.mkdir(exist_ok=True)
    print(f"✅ Carpeta de descarga creada: {download_dir}")
    
    # Crear archivo .env si no existe
    env_file = project_dir / ".env"
    if not env_file.exists():
        env_content = f"""# YTDL Helper Configuration
# Note: For nested configuration, use double underscore (__) 
# YTDL_DOWNLOAD__OUTPUT_DIR={download_dir.absolute()}
# YTDL_DOWNLOAD__FORMAT=best
# YTDL_DOWNLOAD__AUDIO_FORMAT=mp3
# YTDL_USER__CONFIRM_RIGHTS=true
# YTDL_USER__MAX_PLAYLIST_ITEMS=10
# YTDL_METADATA__WRITE_INFO_JSON=true
# YTDL_METADATA__WRITE_THUMBNAIL=true
"""
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        print(f"✅ Archivo .env creado: {env_file}")
        print("ℹ️  Para usar configuración desde .env, descomenta las líneas necesarias")
    else:
        print(f"ℹ️  Archivo .env ya existe: {env_file}")
    
    # Verificar .gitignore
    gitignore_file = project_dir / ".gitignore"
    if gitignore_file.exists():
        with open(gitignore_file, "r", encoding="utf-8") as f:
            content = f.read()
            if "download/" in content:
                print("✅ Carpeta 'download/' ya está en .gitignore")
            else:
                print("⚠️  Carpeta 'download/' no encontrada en .gitignore")
    
    print("\n🎉 Configuración completada!")
    print("\nPara usar la carpeta de descarga configurada:")
    print("  ytdl-helper download --output-dir ./download URL")
    print("\nO simplemente:")
    print("  ytdl-helper download URL")
    print("(si has configurado la variable de entorno)")


if __name__ == "__main__":
    main()
