#!/usr/bin/env bash
# Gera o pacote copiado_all.deb. Uso: empacotamento/gerar-deb.sh 1.2.3
set -e
VERSAO="${1:?informe a versão, ex.: 1.0.0}"
cd "$(dirname "$0")/.."
RAIZ=$(mktemp -d)
chmod 755 "$RAIZ"
trap 'rm -rf "$RAIZ"' EXIT

install -Dm755 copiado.py "$RAIZ/usr/bin/copiado"
install -Dm644 README.md "$RAIZ/usr/share/doc/copiado/README.md"
install -Dm644 /dev/stdin "$RAIZ/etc/xdg/autostart/copiado.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=Copiado
Comment=Histórico da área de transferência (Win+V)
Exec=copiado
NoDisplay=true
X-GNOME-Autostart-enabled=true
DESK

mkdir -p "$RAIZ/DEBIAN"
cat > "$RAIZ/DEBIAN/control" <<CTRL
Package: copiado
Version: $VERSAO
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-3.0, xdotool
Maintainer: Lucas Guerra <l.rayanguerra@gmail.com>
Homepage: https://github.com/lucasrguerra/copiado
Description: Histórico da área de transferência no estilo Windows 11
 Aperte Win+V para ver os últimos itens copiados e colar com um clique.
CTRL

mkdir -p dist
dpkg-deb --root-owner-group --build "$RAIZ" dist/copiado_all.deb
echo "Gerado: dist/copiado_all.deb ($VERSAO)"
