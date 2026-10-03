#!/usr/bin/env bash
# Remove o Copiado e o atalho Win+V
command -v copiado >/dev/null && copiado remover-atalho
pkill -f "/usr/bin/copiado" 2>/dev/null
sudo apt-get remove -y copiado
rm -rf "$HOME/.local/share/copiado"
echo "Copiado removido. (O histórico salvo também foi apagado.)"
