#!/usr/bin/env python3
"""Copiado: histórico da área de transferência no estilo Windows 11 (Win+V).

Uso:
  copiado             inicia em segundo plano (vigia o Ctrl+C)
  copiado show        abre a janelinha do histórico
  copiado esquecer    apaga todo o histórico, inclusive os fixados
  copiado consertar   recria o atalho Win+V e inicia o app se estiver parado
  copiado ajuda       mostra esta ajuda
"""
import hashlib
import json
import os
import subprocess
import sys
import time

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkX11", "3.0")
from gi.repository import Gdk, GdkPixbuf, GdkX11, Gio, GLib, Gtk, Pango  # noqa: E402

MAX_ITENS = 25
LARGURA, ALTURA = 380, 480
PASTA = os.path.join(GLib.get_user_data_dir(), "copiado")
ARQ_HIST = os.path.join(PASTA, "historico.json")
MAX_TEXTO = 1024 * 1024          # textos maiores que 1 MB não são guardados
MAX_IMAGEM = 20 * 1024 * 1024    # imagens maiores que 20 MB (PNG) também não

CSS = b"""
#fundo {
  background-color: rgba(32, 32, 32, 0.97);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}
#titulo { color: #ffffff; font-size: 15px; font-weight: 600; }
#limpar {
  color: #9fc9ff; background: transparent; border: none; box-shadow: none;
  font-size: 12px; padding: 4px 8px; border-radius: 6px;
}
#limpar:hover { background-color: rgba(255, 255, 255, 0.06); }
list { background: transparent; }
row { background: transparent; padding: 0; outline: none; }
row:focus, row:hover, row:selected { background: transparent; }
.cartao {
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 10px 12px;
  margin: 3px 0;
}
row:hover .cartao { background-color: rgba(255, 255, 255, 0.09); }
row:focus .cartao, row:selected .cartao {
  background-color: rgba(255, 255, 255, 0.09);
  border-color: #4cc2ff;
}
.texto { color: #f3f3f3; font-size: 13px; }
.icone {
  background: transparent; border: none; box-shadow: none;
  color: #a0a0a0; padding: 2px 4px; min-width: 0; min-height: 0; border-radius: 4px;
}
.icone:hover { background-color: rgba(255, 255, 255, 0.10); color: #ffffff; }
.fixado, .fixado:hover { color: #4cc2ff; }
#vazio { color: #a0a0a0; font-size: 13px; }
scrollbar { background: transparent; border: none; }
scrollbar slider { background-color: rgba(255,255,255,0.25); border-radius: 4px; min-width: 4px; }
"""


def item_valido(item):
    """Aceita só itens bem formados; imagens só dentro da nossa pasta."""
    if not isinstance(item, dict) or not isinstance(item.get("dado"), str):
        return False
    if item.get("tipo") == "texto":
        return len(item["dado"]) <= MAX_TEXTO
    if item.get("tipo") == "imagem":
        caminho = os.path.realpath(item["dado"])
        return (os.path.dirname(caminho) == os.path.realpath(PASTA)
                and caminho.endswith(".png") and os.path.isfile(caminho))
    return False


class Historico:
    def __init__(self):
        # só o próprio usuário pode ler o histórico (pasta 700, arquivos 600)
        os.umask(0o077)
        os.makedirs(PASTA, mode=0o700, exist_ok=True)
        os.chmod(PASTA, 0o700)
        for nome in os.listdir(PASTA):
            caminho = os.path.join(PASTA, nome)
            if os.path.isfile(caminho) and not os.path.islink(caminho):
                os.chmod(caminho, 0o600)
        self.itens = []  # {"tipo": "texto"|"imagem", "dado": str, "fixo": bool}
        try:
            with open(ARQ_HIST) as f:
                carregados = json.load(f)
            if isinstance(carregados, list):
                # como no Windows: ao ligar o PC, só os fixados continuam
                self.itens = [{"tipo": i["tipo"], "dado": i["dado"], "fixo": True}
                              for i in carregados if item_valido(i) and i.get("fixo") is True]
        except (OSError, ValueError):
            pass
        self.salvar()

    def salvar(self):
        # só os fixados vão para o disco; o resto fica apenas na memória
        fixos = [i for i in self.itens if i["fixo"]]
        tmp = ARQ_HIST + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(fixos, f, ensure_ascii=False)
        os.replace(tmp, ARQ_HIST)
        usadas = {i["dado"] for i in self.itens if i["tipo"] == "imagem"}
        for nome in os.listdir(PASTA):
            caminho = os.path.join(PASTA, nome)
            if nome.endswith(".png") and caminho not in usadas:
                os.remove(caminho)

    def esquecer_tudo(self):
        """Apaga o histórico inteiro, inclusive os fixados."""
        self.itens = []
        self.salvar()

    def adicionar(self, tipo, dado):
        antigo = next((i for i in self.itens if i["tipo"] == tipo and i["dado"] == dado), None)
        fixo = antigo["fixo"] if antigo else False
        if antigo:
            self.itens.remove(antigo)
        self.itens.insert(0, {"tipo": tipo, "dado": dado, "fixo": fixo})
        soltos = [i for i in self.itens if not i["fixo"]]
        for extra in soltos[MAX_ITENS:]:
            self.itens.remove(extra)
        self.salvar()

    def remover(self, item):
        self.itens.remove(item)
        self.salvar()

    def limpar(self):
        self.itens = [i for i in self.itens if i["fixo"]]
        self.salvar()


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="io.github.copiado",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.hist = None
        self.janela = None
        self.ignorar = None  # conteúdo que nós mesmos colocamos

    # ---------- ciclo de vida ----------
    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.hold()
        self.hist = Historico()
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.clip.connect("owner-change", self.ao_copiar)
        self.criar_janela()

    def do_command_line(self, linha):
        args = linha.get_arguments()[1:]
        if "show" in args:
            self.mostrar()
        elif "esquecer" in args:
            self.hist.esquecer_tudo()
            if self.janela.get_visible():
                self.preencher()
        return 0

    # ---------- captura ----------
    def ao_copiar(self, clip, _evento):
        if clip.wait_is_image_available():
            img = clip.wait_for_image()
            if img is None:
                return
            dados = img.save_to_bufferv("png", [], [])[1]
            if len(dados) > MAX_IMAGEM:
                return
            nome = hashlib.sha256(dados).hexdigest()[:32] + ".png"
            caminho = os.path.join(PASTA, nome)
            if caminho == self.ignorar:
                return
            if not os.path.exists(caminho):
                fd = os.open(caminho, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, "wb") as f:
                    f.write(dados)
            self.hist.adicionar("imagem", caminho)
        else:
            texto = clip.wait_for_text()
            if (not texto or not texto.strip() or len(texto) > MAX_TEXTO
                    or texto == self.ignorar):
                return
            self.hist.adicionar("texto", texto)
        if self.janela.get_visible():
            self.preencher()

    # ---------- janela ----------
    def criar_janela(self):
        j = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.add_window(j)
        j.set_decorated(False)
        j.set_resizable(False)
        j.set_skip_taskbar_hint(True)
        j.set_skip_pager_hint(True)
        j.set_keep_above(True)
        j.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        j.set_default_size(LARGURA, ALTURA)
        visual = j.get_screen().get_rgba_visual()
        if visual:
            j.set_visual(visual)
        j.set_app_paintable(True)
        j.connect("draw", self.limpar_fundo)
        j.connect("key-press-event", self.ao_tecla)
        j.connect("focus-out-event", lambda *_: self.esconder())
        j.connect("delete-event", lambda *_: self.esconder() or True)

        caixa = Gtk.Box()
        caixa.set_name("fundo")
        fundo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for m in ("top", "bottom", "start", "end"):
            getattr(fundo, f"set_margin_{m}")(12)
        caixa.pack_start(fundo, True, True, 0)

        topo = Gtk.Box(spacing=8)
        titulo = Gtk.Label(label="Área de transferência", xalign=0)
        titulo.set_name("titulo")
        limpar = Gtk.Button(label="Limpar tudo")
        limpar.set_name("limpar")
        limpar.connect("clicked", lambda *_: (self.hist.limpar(), self.preencher()))
        topo.pack_start(titulo, True, True, 0)
        topo.pack_end(limpar, False, False, 0)

        self.lista = Gtk.ListBox()
        self.lista.set_selection_mode(Gtk.SelectionMode.NONE)
        self.lista.connect("row-activated", lambda _l, row: self.colar(row.item))
        rolagem = Gtk.ScrolledWindow()
        rolagem.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        rolagem.add(self.lista)

        self.vazio = Gtk.Label(
            label="Nada aqui ainda\n\nCopie algo com Ctrl+C e ele\naparecerá neste histórico.",
            justify=Gtk.Justification.CENTER)
        self.vazio.set_name("vazio")

        self.pilha = Gtk.Stack()
        self.pilha.add_named(rolagem, "lista")
        self.pilha.add_named(self.vazio, "vazio")

        fundo.pack_start(topo, False, False, 0)
        fundo.pack_start(self.pilha, True, True, 0)
        j.add(caixa)
        self.janela = j

    @staticmethod
    def limpar_fundo(_w, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(0)  # CLEAR
        cr.paint()
        cr.set_operator(2)  # OVER
        return False

    def cartao(self, item):
        row = Gtk.ListBoxRow()
        row.item = item
        caixa = Gtk.Box(spacing=8)
        caixa.get_style_context().add_class("cartao")

        if item["tipo"] == "imagem":
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(item["dado"], 300, 110, True)
                conteudo = Gtk.Image.new_from_pixbuf(pb)
                conteudo.set_halign(Gtk.Align.START)
            except GLib.Error:
                conteudo = Gtk.Label(label="[imagem]", xalign=0)
        else:
            texto = item["dado"].strip()
            if len(texto) > 400:
                texto = texto[:400] + "…"
            conteudo = Gtk.Label(label=texto, xalign=0, yalign=0)
            conteudo.set_line_wrap(True)
            conteudo.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            conteudo.set_lines(3)
            conteudo.set_ellipsize(Pango.EllipsizeMode.END)
            conteudo.set_max_width_chars(1)
            conteudo.get_style_context().add_class("texto")

        botoes = Gtk.Box(spacing=2)
        botoes.set_valign(Gtk.Align.START)
        fixar = Gtk.Button.new_from_icon_name("view-pin-symbolic", Gtk.IconSize.MENU)
        fixar.set_tooltip_text("Desafixar" if item["fixo"] else "Fixar")
        fixar.get_style_context().add_class("icone")
        if item["fixo"]:
            fixar.get_style_context().add_class("fixado")
        fixar.connect("clicked", self.alternar_fixo, item)
        apagar = Gtk.Button.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.MENU)
        apagar.set_tooltip_text("Excluir")
        apagar.get_style_context().add_class("icone")
        apagar.connect("clicked", lambda *_: (self.hist.remover(item), self.preencher()))
        botoes.pack_start(fixar, False, False, 0)
        botoes.pack_start(apagar, False, False, 0)

        caixa.pack_start(conteudo, True, True, 0)
        caixa.pack_end(botoes, False, False, 0)
        row.add(caixa)
        return row

    def alternar_fixo(self, _btn, item):
        item["fixo"] = not item["fixo"]
        self.hist.salvar()
        self.preencher()

    def preencher(self):
        for filho in self.lista.get_children():
            self.lista.remove(filho)
        for item in self.hist.itens:
            self.lista.add(self.cartao(item))
        self.lista.show_all()
        self.pilha.set_visible_child_name("lista" if self.hist.itens else "vazio")
        primeira = self.lista.get_row_at_index(0)
        if primeira:
            primeira.grab_focus()

    def mostrar(self):
        if self.janela.get_visible():
            self.esconder()
            return
        self.preencher()
        # posiciona perto do mouse, sem sair da tela
        tela = Gdk.Display.get_default()
        _s, x, y = tela.get_default_seat().get_pointer().get_position()[0:3]
        geo = tela.get_monitor_at_point(x, y).get_workarea()
        x = max(geo.x + 8, min(x - LARGURA // 2, geo.x + geo.width - LARGURA - 8))
        y = max(geo.y + 8, min(y - 40, geo.y + geo.height - ALTURA - 8))
        self.janela.move(x, y)
        self.janela.show_all()
        self.pilha.set_visible_child_name("lista" if self.hist.itens else "vazio")
        gw = self.janela.get_window()
        gw.focus(GdkX11.x11_get_server_time(gw))
        self.janela.present_with_time(GdkX11.x11_get_server_time(gw))

    def esconder(self):
        self.janela.hide()
        return False

    def ao_tecla(self, _w, ev):
        if ev.keyval == Gdk.KEY_Escape:
            self.esconder()
            return True
        if ev.keyval == Gdk.KEY_Delete:
            row = self.janela.get_focus()
            if isinstance(row, Gtk.ListBoxRow):
                self.hist.remover(row.item)
                self.preencher()
            return True
        return False

    # ---------- colar ----------
    def colar(self, item):
        if item["tipo"] == "imagem":
            try:
                self.clip.set_image(GdkPixbuf.Pixbuf.new_from_file(item["dado"]))
            except GLib.Error:
                return
        else:
            self.clip.set_text(item["dado"], -1)
        self.clip.store()
        self.ignorar = item["dado"]
        # sobe o item para o topo, como no Windows
        self.hist.itens.remove(item)
        self.hist.itens.insert(0, item)
        self.hist.salvar()
        self.esconder()
        GLib.timeout_add(150, self.enviar_ctrl_v)

    def enviar_ctrl_v(self):
        tecla = "ctrl+v"
        try:
            classe = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowclassname"],
                capture_output=True, text=True, timeout=1).stdout.lower()
            if any(t in classe for t in ("term", "tilix", "kitty", "alacritty", "konsole")):
                tecla = "ctrl+shift+v"
            subprocess.run(["xdotool", "key", "--clearmodifiers", tecla], timeout=2)
        except (OSError, subprocess.SubprocessError):
            pass
        GLib.timeout_add(500, self.liberar_ignorar)
        return False

    def liberar_ignorar(self):
        self.ignorar = None
        return False


# ---------- comandos de manutenção (não abrem janela) ----------
ATALHOS = "org.cinnamon.desktop.keybindings"
CAMINHO_ATALHO = "/org/cinnamon/desktop/keybindings/custom-keybindings/{}/"


def gsettings(*args):
    return subprocess.run(["gsettings", *args], capture_output=True,
                          text=True, check=True).stdout.strip()


def ler_lista(valor):
    # gsettings devolve algo como "['custom0']" ou "@as []"
    return json.loads(valor.replace("@as ", "").replace("'", '"'))


def esquema(ident):
    return f"{ATALHOS}.custom-keybinding:" + CAMINHO_ATALHO.format(ident)


def configurar_atalho():
    """Cria (ou corrige) o atalho Win+V e faz o Cinnamon recarregá-lo."""
    lista = ler_lista(gsettings("get", ATALHOS, "custom-list"))
    ident = next((i for i in lista
                  if gsettings("get", esquema(i), "binding") == "['<Super>v']"), None)
    if ident is None:
        ident = next(f"custom{n}" for n in range(1000) if f"custom{n}" not in lista)
        lista.append(ident)
    gsettings("set", esquema(ident), "name", "Copiado")
    gsettings("set", esquema(ident), "command", "copiado show")
    gsettings("set", esquema(ident), "binding", "['<Super>v']")
    # o Cinnamon só relê os atalhos quando a lista muda
    gsettings("set", ATALHOS, "custom-list", "[]")
    time.sleep(0.5)
    gsettings("set", ATALHOS, "custom-list", json.dumps(lista).replace('"', "'"))
    return ident


def remover_atalho():
    lista = ler_lista(gsettings("get", ATALHOS, "custom-list"))
    nossos = [i for i in lista if "copiado" in gsettings("get", esquema(i), "command")]
    for ident in nossos:
        gsettings("reset-recursively", esquema(ident))
    restantes = [i for i in lista if i not in nossos]
    gsettings("set", ATALHOS, "custom-list", json.dumps(restantes).replace('"', "'"))


def esta_rodando():
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)
    resp = bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus",
                         "org.freedesktop.DBus", "NameHasOwner",
                         GLib.Variant("(s)", ("io.github.copiado",)),
                         GLib.VariantType("(b)"), Gio.DBusCallFlags.NONE, -1, None)
    return resp.unpack()[0]


def iniciar_em_segundo_plano():
    subprocess.Popen([sys.executable, os.path.realpath(__file__)],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(30):
        time.sleep(0.2)
        if esta_rodando():
            return True
    return False


def consertar():
    try:
        ident = configurar_atalho()
        print(f"✓ Atalho Win+V configurado e recarregado ({ident}).")
    except (OSError, subprocess.CalledProcessError) as erro:
        print(f"✗ Não consegui configurar o atalho: {erro}")
        return 1
    if esta_rodando():
        print("✓ O Copiado já está rodando.")
    elif iniciar_em_segundo_plano():
        print("✓ O Copiado estava parado e foi iniciado.")
    else:
        print("✗ Não consegui iniciar o Copiado. Rode 'copiado' para ver o erro.")
        return 1
    print("Pronto! Aperte Win+V.")
    print("Se ainda não abrir, veja se outro atalho usa Win+V em")
    print("Configurações do Sistema → Teclado → Atalhos.")
    return 0


def main(argv):
    comando = argv[1] if len(argv) > 1 else ""
    if comando in ("ajuda", "-h", "--help"):
        print(__doc__.strip())
        return 0
    if comando == "consertar":
        return consertar()
    if comando == "instalar-atalho":
        configurar_atalho()
        return 0
    if comando == "remover-atalho":
        remover_atalho()
        return 0
    if comando not in ("", "show", "esquecer"):
        print(f"Comando desconhecido: {comando}\n")
        print(__doc__.strip())
        return 2
    return App().run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
