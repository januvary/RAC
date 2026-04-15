#!/bin/bash
# RAC - Script de Atualizacao (Linux)
# Baixa o src/ mais recente do repositorio e substitui os arquivos.
# Nao precisa de git - usa a API do GitHub (requer gh CLI autenticado).
#
# Uso: ./update.sh [branch]
#   branch: branch do git para baixar (padrao: master)

if [ ! -t 0 ]; then
    for term in x-terminal-emulator xterm gnome-terminal konsole xfce4-terminal mate-terminal; do
        if command -v "$term" &>/dev/null; then
            exec "$term" -e "bash '$0' $1"
        fi
    done
    echo "Nenhum emulador de terminal encontrado. Execute este script num terminal."
    exit 1
fi

set -e

BRANCH="${1:-master}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR"
SRC_DIR="$APP_DIR/_internal/src"
BACKUP_DIR="$APP_DIR/_internal/src_backup"
TMP_DIR=$(mktemp -d)

echo "=== Atualizacao RAC ==="
echo "Branch: $BRANCH"
echo ""

if [ ! -d "$SRC_DIR" ]; then
    echo "[ERRO] Nao foi possivel encontrar _internal/src/. Diretorio correto?"
    exit 1
fi

if ! command -v gh &>/dev/null; then
    echo "[ERRO] CLI 'gh' nao encontrado. Instale e execute 'gh auth login'."
    echo "  Veja: https://cli.github.com/"
    exit 1
fi

echo "[1/4] Baixando codigo fonte..."
ZIP_PATH="$TMP_DIR/source.zip"
gh api "repos/januvary/RAC/zipball/$BRANCH" > "$ZIP_PATH"

if [ ! -s "$ZIP_PATH" ]; then
    echo "[ERRO] Falha no download. Verifique 'gh auth status' e acesso ao repo."
    rm -rf "$TMP_DIR"
    exit 1
fi

echo "[2/4] Extraindo..."
unzip -q "$ZIP_PATH" -d "$TMP_DIR/extracted"
EXTRACTED_SRC=$(find "$TMP_DIR/extracted" -maxdepth 2 -type d -name "src" | head -1)

if [ -z "$EXTRACTED_SRC" ]; then
    echo "[ERRO] Nao foi possivel encontrar src/ no arquivo baixado."
    rm -rf "$TMP_DIR"
    exit 1
fi

echo "[3/4] Substituindo arquivos..."
rm -rf "$BACKUP_DIR"
mv "$SRC_DIR" "$BACKUP_DIR"
cp -r "$EXTRACTED_SRC" "$SRC_DIR"
find "$SRC_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "[4/4] Limpando..."
rm -rf "$TMP_DIR"

echo ""
echo "Atualizacao concluida! Backup salvo em _internal/src_backup/"
echo "Reinicie o RAC para aplicar as alteracoes."
echo ""
echo "Para reverter: mv _internal/src_backup/ _internal/src/"
echo ""
read -p "Pressione Enter para fechar..."
