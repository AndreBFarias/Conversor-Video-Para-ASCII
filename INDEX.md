# Mapa do Projeto (Extase em 4R73 v2.1.0)

Este arquivo serve como guia de navegação rápida para a estrutura do projeto.

## 🧭 Documentação Principal

| Arquivo | Descrição |
|---------|-----------|
| **[README.md](README.md)** | Visão geral, instalação e uso básico. |
| **[docs/INDEX.md](docs/INDEX.md)** | **Índice Técnico Detalhado**: Arquitetura, fluxos e referência de código. |
| **[docs/CHANGELOG.md](docs/CHANGELOG.md)** | Histórico de versões e mudanças. |
| **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** | Guia para colaboradores. |

## 📂 Estrutura de Diretórios

- **`/src`**: Código fonte da aplicação.
    - **`app/`**: Lógica principal GTK e Actions.
    - **`core/`**: Conversores (GPU/CPU), Calibrador, Player.
    - **`gui/`**: Interfaces gráficas (`.glade`).
- **`/docs`**: Documentação completa do projeto.
- **`/debian`** & **`/packaging`**: Scripts e configurações para geração do pacote `.deb`.
- **`/tests`**: Testes unitários e de integração.

## 🚀 Scripts Importantes

- `main.py`: Ponto de entrada da aplicação.
- `install.sh`: Script de instalação automatizada (Ubuntu/Debian).
- `uninstall.sh`: Remove a aplicação e limpa configurações.
- `scripts/build_deb.sh`: Gera o pacote instalável `.deb`.

---
*Para detalhes técnicos profundos sobre a arquitetura, consulte o [Índice Técnico](docs/INDEX.md).*
