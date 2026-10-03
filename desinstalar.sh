#!/usr/bin/env bash
# Remove o Copiado e o atalho Win+V
BASE=org.cinnamon.desktop.keybindings
LISTA=$(gsettings get $BASE custom-list)
for ID in $(python3 -c "import ast,sys; print(' '.join(ast.literal_eval(sys.argv[1].replace('@as ',''))))" "$LISTA"); do
  SCHEMA="$BASE.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/$ID/"
  if gsettings get "$SCHEMA" command | grep -q copiado; then
    LISTA=$(python3 -c "import ast,sys; l=ast.literal_eval(sys.argv[1].replace('@as ','')); print([x for x in l if x!='$ID'])" "$LISTA")
    gsettings set $BASE custom-list "$LISTA"
    gsettings reset-recursively "$SCHEMA"
  fi
done
pkill -f "/usr/bin/copiado" 2>/dev/null
sudo apt-get remove -y copiado
rm -rf "$HOME/.local/share/copiado"
echo "Copiado removido. (O histórico salvo também foi apagado.)"
