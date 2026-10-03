#!/usr/bin/env bash
# Instala (ou atualiza) o Copiado a partir do pacote publicado no GitHub
set -e
URL="https://github.com/lucasrguerra/copiado/releases/latest/download/copiado_all.deb"
BASE=org.cinnamon.desktop.keybindings
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "==> Baixando a versão mais recente..."
curl -fsSL -o "$TMP/copiado_all.deb" "$URL"
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

echo "==> Criando atalho Win+V..."
LISTA=$(gsettings get $BASE custom-list)
ID=""
for i in $(python3 -c "import ast,sys; print(' '.join(ast.literal_eval(sys.argv[1].replace('@as ',''))))" "$LISTA"); do
  B=$(gsettings get "$BASE.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/$i/" binding)
  [ "$B" = "['<Super>v']" ] && ID=$i && break
done
if [ -z "$ID" ]; then
  for i in $(seq 0 99); do
    echo "$LISTA" | grep -q "'custom$i'" || { ID="custom$i"; break; }
  done
  LISTA=$(python3 -c "import ast,sys; l=ast.literal_eval(sys.argv[1].replace('@as ','')); l.append('$ID'); print(l)" "$LISTA")
fi
SCHEMA="$BASE.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/$ID/"
gsettings set "$SCHEMA" name "Copiado"
gsettings set "$SCHEMA" command "copiado show"
gsettings set "$SCHEMA" binding "['<Super>v']"
# só agora registra a lista (e força o Cinnamon a recarregar os atalhos)
gsettings set $BASE custom-list "[]"
sleep 0.5
gsettings set $BASE custom-list "$LISTA"

echo "==> Iniciando..."
pkill -x copiado 2>/dev/null || pkill -f "/usr/bin/copiado" 2>/dev/null || true
setsid copiado >/dev/null 2>&1 &

echo
echo "Pronto! Versão instalada: $(dpkg-query -W -f='${Version}' copiado). Aperte Win+V."
