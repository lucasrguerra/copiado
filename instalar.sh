#!/usr/bin/env bash
# Instala (ou atualiza) o Copiado a partir do pacote publicado no GitHub
set -e
URL="https://github.com/lucasrguerra/copiado/releases/latest/download"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "==> Baixando a versão mais recente..."
curl -fsSL --proto '=https' --tlsv1.2 -o "$TMP/copiado_all.deb" "$URL/copiado_all.deb"
curl -fsSL --proto '=https' --tlsv1.2 -o "$TMP/SHA256SUMS" "$URL/SHA256SUMS"

echo "==> Conferindo a integridade do pacote..."
(cd "$TMP" && sha256sum --check --strict --quiet SHA256SUMS) || {
  echo "ERRO: o pacote baixado não confere com o checksum publicado. Instalação cancelada."
  exit 1
}
chmod 644 "$TMP/copiado_all.deb"

echo "==> Instalando o pacote..."
sudo apt-get update -qq || echo "   (aviso: algum repositório falhou no update, seguindo mesmo assim)"
sudo apt-get install -y "$TMP/copiado_all.deb"

# remove instalações antigas feitas sem pacote (o histórico é mantido)
pkill -f "share/copiado/copiado.py" 2>/dev/null || true
pkill -f "share/clipboard-winv/clipboard-winv.py" 2>/dev/null || true
rm -f "$HOME/.local/share/copiado/copiado.py" \
      "$HOME/.config/autostart/copiado.desktop" \
      "$HOME/.config/autostart/clipboard-winv.desktop"
if [ -f "$HOME/.local/share/clipboard-winv/historico.json" ]; then
  mkdir -p "$HOME/.local/share/copiado"
  cp -a "$HOME/.local/share/clipboard-winv"/. "$HOME/.local/share/copiado"/
  sed -i "s#/clipboard-winv/#/copiado/#g" "$HOME/.local/share/copiado/historico.json"
  rm -rf "$HOME/.local/share/clipboard-winv"
fi

echo "==> Criando atalho Win+V e iniciando..."
pkill -f "/usr/bin/copiado" 2>/dev/null || true
sleep 0.5
copiado consertar >/dev/null

echo
echo "Pronto! Versão instalada: $(dpkg-query -W -f='${Version}' copiado). Aperte Win+V."
