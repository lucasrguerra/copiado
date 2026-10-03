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

Guarda os 25 últimos itens (texto e imagens). Como no Windows, ao reiniciar o PC
só os itens **fixados** continuam; o resto existe apenas na memória.

## Privacidade e segurança

A área de transferência pode ter senhas, tokens e dados pessoais, então o Copiado:

- **Ignora senhas de gerenciadores de senha** (KeePassXC, Bitwarden, 1Password etc.),
  que marcam o que copiam pedindo para não entrar em histórico.
- **Só grava no disco os itens fixados**, em `~/.local/share/copiado/`, com
  permissão só para você (pasta `700`, arquivos `600`).
- **Não guarda textos acima de 1 MB nem imagens acima de 20 MB.**
- **Valida o arquivo de histórico** ao abrir: entradas estranhas ou imagens fora da
  pasta do Copiado são descartadas.
- **Não usa rede** e não executa nada do que foi copiado.

Para apagar tudo, inclusive os fixados: `copiado esquecer`

O instalador confere o checksum SHA-256 do pacote antes de instalar, e a esteira
de CI/CD roda o [Trivy](https://trivy.dev) (vulnerabilidades, segredos e configurações)
em todo push, em toda release e toda segunda-feira. Os resultados ficam na aba
**Security** do repositório.

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
