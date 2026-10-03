# Copiado

O histórico da área de transferência do Windows, no Linux Mint.
Aperte **Win+V** e ele aparece, no visual do Windows 11.
Clique em um item e ele é colado na hora.

## Instalar

```bash
curl -fsSL https://raw.githubusercontent.com/lucasrguerra/copiado/main/instalar.sh | bash
```

Baixa o pacote `.deb` mais recente das [Releases](https://github.com/lucasrguerra/copiado/releases),
instala, cria o atalho Win+V e já deixa rodando. Pede sua senha (sudo).
Para **atualizar**, rode o mesmo comando de novo.

## Usar

| Ação | Como |
|---|---|
| Abrir / fechar | **Win+V** |
| Colar um item | clique, ou setas + **Enter** |
| Fixar (não some ao limpar) | ícone de alfinete |
| Apagar um item | ícone da lixeira ou tecla **Delete** |
| Apagar tudo (menos os fixados) | **Limpar tudo** |
| Fechar sem colar | **Esc** ou clicar fora |

Guarda os 25 últimos itens (texto e imagens) e continua lá depois de reiniciar o PC.

## Desinstalar

```bash
curl -fsSL https://raw.githubusercontent.com/lucasrguerra/copiado/main/desinstalar.sh | bash
```

## Se algo der errado

- **Win+V não abre nada:** faça o Cinnamon recarregar os atalhos:
  ```bash
  gsettings set org.cinnamon.desktop.keybindings custom-list "[]"; gsettings set org.cinnamon.desktop.keybindings custom-list "['custom0']"
  ```
  Se ainda assim não abrir, veja se outro atalho usa Win+V em
  *Configurações do Sistema → Teclado → Atalhos*.
- **Abre, mas o histórico está vazio:** o app pode não estar rodando. Rode
  `copiado &`

## Publicar uma versão nova

```bash
git tag v1.0.1 && git push origin v1.0.1
```

O GitHub Actions gera o `copiado_all.deb`, testa a instalação e publica a release.
Para gerar o pacote localmente: `empacotamento/gerar-deb.sh 1.0.1` (sai em `dist/`).
