# Metricas do Projeto Luna

> **TL;DR:** Estatisticas de codigo, performance e saude do projeto Luna, atualizadas periodicamente.

## Contexto

Este documento apresenta metricas quantitativas do projeto para acompanhar crescimento, identificar areas de atencao e medir progresso. Atualizado a cada release ou mudanca significativa.

---

## Linhas de Codigo por Modulo

| Modulo | Arquivos | Linhas | Responsabilidade |
|--------|----------|--------|------------------|
| src/soul | 16 | 4.584 | Motor IA (consciencia, voz, visao) |
| src/ui | 10 | 2.349 | Interface TUI (widgets, animacoes) |
| src/tools | 12 | 1.266 | Scripts utilitarios |
| src/core | 4 | 551 | Logica compartilhada (sessoes, animacao) |
| src/data_memory | 4 | 350 | Embeddings e memoria vetorial |
| main.py | 1 | 975 | Orquestrador principal |
| config.py | 1 | 225 | Configuracoes centralizadas |
| **TOTAL** | **48** | **10.300** | - |

## Distribuicao por Categoria

```
src/soul/      ████████████████████░░░  44.5%  (Motor IA)
src/ui/        ██████████░░░░░░░░░░░░░  22.8%  (Interface)
src/tools/     █████░░░░░░░░░░░░░░░░░░  12.3%  (Utilitarios)
main.py        ████░░░░░░░░░░░░░░░░░░░   9.5%  (Orquestrador)
src/core/      ██░░░░░░░░░░░░░░░░░░░░░   5.3%  (Logica)
src/data_memory█░░░░░░░░░░░░░░░░░░░░░░   3.4%  (Memoria)
config.py      █░░░░░░░░░░░░░░░░░░░░░░   2.2%  (Config)
```

---

## Tamanho do Projeto

| Metrica | Valor |
|---------|-------|
| Tamanho total (sem venv) | 42 MB |
| Arquivos Python (.py) | 51 |
| Arquivos Markdown (.md) | 35+ |
| Arquivos CSS (.tcss) | 1 |
| Shell scripts (.sh) | 3 |

---

## Dependencias

| Categoria | Arquivo | Quantidade |
|-----------|---------|------------|
| Principal | requirements.txt | 24 pacotes |
| TTS (separado) | requirements_tts.txt | 15 pacotes |
| **TOTAL** | - | **39 pacotes** |

### Dependencias Criticas

| Pacote | Versao | Funcao |
|--------|--------|--------|
| textual | >=0.40.0 | Framework TUI |
| google-generativeai | >=0.3.0 | API Gemini |
| faster-whisper | >=0.9.0 | Speech-to-Text |
| sentence-transformers | >=2.2.0 | Embeddings |
| opencv-python | >=4.8.0 | Visao computacional |
| face-recognition | >=1.3.0 | Reconhecimento facial |

---

## Placeholders e Divida Tecnica

| Tag | Quantidade | Status |
|-----|------------|--------|
| EMPTY_PASS | 2 | Funcoes vazias para implementar |
| NOT_IMPLEMENTED | 1 | Funcionalidade pendente |
| NOTE | 1 | Anotacoes de atencao |
| **TOTAL** | **4** | - |

Ver detalhes em: [PLACEHOLDERS.md](../04-implementation/PLACEHOLDERS.md)

---

## Performance (v3.2.0)

| Metrica | Valor | Meta |
|---------|-------|------|
| Latencia voz-a-voz | ~5.7s | <4.5s |
| Cache hit rate | ~42% | >50% |
| Tempo de startup | ~8s | <5s |
| RAM em uso | ~800MB | <700MB |

Ver detalhes em: [PERFORMANCE.md](./PERFORMANCE.md)

---

## Cobertura de Testes

| Modulo | Cobertura | Status |
|--------|-----------|--------|
| src/soul | Parcial | Scripts isolados |
| src/ui | Minima | Testes visuais manuais |
| src/core | Parcial | Testes unitarios basicos |
| src/tools | Alta | Scripts de teste incluidos |

**Meta v4.0:** Atingir >= 60% de cobertura com pytest

---

## Tendencias

### Crescimento de Codigo

| Versao | Linhas | Delta |
|--------|--------|-------|
| v1.0.0 | ~2.500 | - |
| v2.0.0 | ~5.000 | +100% |
| v3.0.0 | ~8.500 | +70% |
| v3.2.0 | ~10.300 | +21% |

### Complexidade por Release

| Versao | Arquivos | Modulos | Threads |
|--------|----------|---------|---------|
| v1.0.0 | 12 | 3 | 1 |
| v2.0.0 | 25 | 5 | 4 |
| v3.0.0 | 40 | 7 | 7 |
| v3.2.0 | 51 | 8 | 7 |

---

## Como Atualizar Estas Metricas

```bash
# Contar linhas por modulo
find src/soul -name "*.py" | xargs wc -l | tail -1
find src/ui -name "*.py" | xargs wc -l | tail -1

# Listar placeholders
python src/tools/find_placeholders.py

# Tamanho do projeto
du -sh --exclude=venv --exclude=.git .

# Total de arquivos Python
find . -name "*.py" -not -path "./venv*" | wc -l
```

---

## Links Relacionados

- [PERFORMANCE.md](./PERFORMANCE.md) - Metricas de latencia e recursos
- [CODE_STATS.md](./CODE_STATS.md) - Estatisticas detalhadas de codigo
- [MILESTONES.md](./MILESTONES.md) - Marcos do projeto
- [PLACEHOLDERS.md](../04-implementation/PLACEHOLDERS.md) - TODOs e divida tecnica
- [TECHNICAL_DEBT.md](../05-future/TECHNICAL_DEBT.md) - Plano de refatoracao

---
*Ultima atualizacao: 2025-12-20*
