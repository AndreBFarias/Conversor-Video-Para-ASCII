# Guia de Contribuição

Obrigado por considerar contribuir com o Extase em 4R73!

---

## Como Contribuir

### 1. Fork e Clone

```bash
# Fork no GitHub, depois:
git clone https://github.com/seu-usuario/Conversor-Video-Para-ASCII.git
cd Conversor-Video-Para-ASCII
```

### 2. Criar Branch

```bash
git checkout -b feature/minha-feature
# ou
git checkout -b fix/meu-bugfix
```

### 3. Instalar Dependências

```bash
./install.sh
source venv/bin/activate
```

### 4. Fazer Mudanças

- Escreva código limpo e documentado
- Siga o estilo do projeto (type hints, sem comentários no código)
- Teste suas mudanças localmente

### 5. Commit

Seguimos [Conventional Commits](https://conventionalcommits.org/):

```
<tipo>: <descrição curta>

<descrição longa opcional>

Resolves: #issue (se aplicável)
```

**Tipos válidos:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `refactor`: Refatoração de código
- `test`: Adição/modificação de testes
- `perf`: Melhoria de performance
- `chore`: Manutenção (build, dependências, etc)

**Exemplos:**
```
feat: Adicionar modo Matrix Rain com particle system

Implementa sistema de partículas GPU com 5000+ caracteres
interativos que colidem com a máscara de chroma key.

Resolves: #42
```

```
fix: Corrigir vazamento de memória no GPU converter

O buffer de frames anteriores não estava sendo liberado
corretamente após processamento.

Resolves: #38
```

### 6. Push e Pull Request

```bash
git push origin feature/minha-feature
```

Abra Pull Request no GitHub com:
- Título claro
- Descrição do que foi feito
- Screenshots/GIFs (se aplicável)
- Referência a issues relacionadas

---

## Padrões de Código

### Python

- **PEP 8** (com exceções do projeto)
- **Type hints** obrigatórios
- **Docstrings** em funções públicas
- **Sem comentários** dentro de funções (código deve ser autoexplicativo)

```python
def converter_frame(frame: np.ndarray, config: dict) -> np.ndarray:
    luminance = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ascii_chars = map_luminance_to_chars(luminance)
    return ascii_chars
```

### Documentação

- Documentação técnica em `docs/`
- Logs de desenvolvimento em `Dev_log/` (não commitado)
- Atualizar `INDEX.md` ao adicionar novos módulos

---

## Testes

### Rodar Tests

```bash
pytest tests/
```

### Escrever Tests

```python
# tests/test_converter.py

def test_converter_basic():
    config = load_test_config()
    result = iniciar_conversao('test_video.mp4', 'output', config)
    assert result is not None
```

---

## Issues

### Reportar Bug

Use o template `.github/ISSUE_TEMPLATE/bug_report.md`:
- Descreva o problema
- Passos para reproduzir
- Comportamento esperado vs atual
- Ambiente (OS, GPU, Python version)
- Logs relevantes

### Sugerir Feature

Use o template `.github/ISSUE_TEMPLATE/feature_request.md`:
- Descreva a funcionalidade
- Por que seria útil
- Como deveria funcionar

---

## Código de Conduta

### Comportamento Esperado

- Linguagem respeitosa e inclusiva
- Feedback construtivo
- Foco no melhor para o projeto
- Respeito a opiniões divergentes

### Comportamento Inaceitável

- Assédio, intimidação, discriminação
- Ataques pessoais ou trolling
- Spam ou autopromoção

### Aplicação

Violações serão moderadas pelos mantenedores.

---

## Perguntas?

- Abra uma issue com label `question`
- Entre em contato: noreply@example.com

---

**Obrigado por contribuir!**
