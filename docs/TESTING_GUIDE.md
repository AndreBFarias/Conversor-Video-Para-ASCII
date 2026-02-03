# TESTING GUIDE - Protocolo de Validação Visual

## Objetivo

Este documento define o protocolo para validar sprints através de testes visuais da interface gráfica.

---

## Protocolo de Testing Visual

### 1. Preparação

Antes de iniciar os testes:

```bash
cd /home/andrefarias/Desenvolvimento/Conversor-Video-Para-ASCII
source venv/bin/activate
python3 main.py &
```

### 2. Captura de Screenshots

O testador deve usar ferramentas de automacao para:

1. **Tirar screenshot da interface**
2. **Ler a screenshot** para entender estado atual
3. **Interagir com elementos** (clicar, preencher campos)
4. **Tirar nova screenshot** após ação
5. **Validar resultado** comparando estados

---

## Casos de Teste por Feature

### Sprint 1: Preview Automático

**Objetivo:** Verificar que preview NÃO abre automaticamente.

**Steps:**
1. Fechar aplicação se estiver aberta
2. Abrir aplicação
3. Selecionar um vídeo (botão "Selecionar Arquivo")
4. Clicar em "Calibrar Chroma Key"
5. **Screenshot 1:** Tirar print do calibrador assim que abrir
6. Aguardar 3 segundos
7. **Screenshot 2:** Tirar print novamente
8. **Validação:** Verificar que NENHUM terminal preview foi aberto

**Duplo Clique:**
9. Fazer duplo clique na área de resultado (preview ASCII)
10. Aguardar 2 segundos
11. **Screenshot 3:** Tirar print mostrando terminal preview aberto
12. **Validação:** Terminal preview deve estar aberto e maximizado

**Resultado Esperado:**
- Screenshots 1 e 2: Apenas calibrador visível
- Screenshot 3: Calibrador + terminal preview lado a lado

---

### Sprint 2: Sistema de Gravação

**Objetivo:** Validar gravação MP4 e ASCII.

#### Teste 2.1: Gravação MP4

**Steps:**
1. Abrir calibrador com vídeo selecionado
2. **Screenshot 1:** Estado inicial (botão MP4 normal)
3. Clicar no botão "MP4" (island-recording)
4. Aguardar 1 segundo
5. **Screenshot 2:** Botão MP4 com borda vermelha pulsante
6. **Validação:** Verificar classe CSS "recording-active"
7. Aguardar 5 segundos
8. Clicar novamente no botão MP4
9. Aguardar 2 segundos
10. **Screenshot 3:** Popup de gravação finalizada
11. **Validação:** Verificar que popup tem botões "Ver Pasta", "Reproduzir", "Fechar"
12. Clicar em "Ver Pasta"
13. **Screenshot 4:** Gerenciador de arquivos aberto em ~/Vídeos
14. **Validação:** Arquivo screencast_*.mp4 presente

**Validação Técnica:**
```bash
# Verificar arquivo existe
ls -lh ~/Vídeos/screencast_*.mp4

# Verificar duração (deve ser ~5 segundos)
ffprobe ~/Vídeos/screencast_*.mp4 2>&1 | grep Duration

# Verificar FPS (deve ser ~30)
ffprobe ~/Vídeos/screencast_*.mp4 2>&1 | grep fps

# Verificar áudio (deve ter stream de áudio)
ffprobe ~/Vídeos/screencast_*.mp4 2>&1 | grep "Stream.*Audio"
```

**Resultado Esperado:**
- Arquivo MP4 criado em ~/Vídeos
- Duração: 5-6 segundos
- FPS: 25-30 (não 4!)
- Áudio: presente
- Resolução: igual à área ASCII (não tela inteira)

#### Teste 2.2: Gravação ASCII

**Steps:**
1. Abrir calibrador
2. Clicar no botão "TXT" (island-recording)
3. **Screenshot 1:** Botão TXT com borda vermelha
4. Aguardar 5 segundos
5. Clicar novamente
6. **Screenshot 2:** Popup de gravação finalizada
7. Clicar em "Reproduzir"
8. Aguardar 2 segundos
9. **Screenshot 3:** Player ASCII aberto reproduzindo

**Validação Técnica:**
```bash
# Verificar arquivo existe
ls -lh ~/Vídeos/*.txt

# Verificar conteúdo (deve ter frames ASCII)
head -n 50 ~/Vídeos/*.txt
```

**Resultado Esperado:**
- Arquivo .txt criado em ~/Vídeos
- Contém frames ASCII coloridos (códigos ANSI)
- Player reproduz corretamente

#### Teste 2.3: Botão Term

**Objetivo:** Verificar que botão Term funciona como duplo clique.

**Steps (Vídeo):**
1. Abrir calibrador com vídeo selecionado
2. **Screenshot 1:** Estado inicial
3. Clicar no botão "Term"
4. Aguardar 2 segundos
5. **Screenshot 2:** Terminal preview aberto
6. **Validação:** Calibrador continua aberto, terminal preview lado a lado

**Steps (Webcam):**
1. Abrir calibrador SEM selecionar vídeo (usa webcam)
2. **Screenshot 1:** Calibrador com webcam
3. Clicar no botão "Term"
4. Aguardar 3 segundos
5. **Screenshot 2:** Terminal preview aberto, calibrador FECHADO
6. **Validação:** Apenas terminal preview visível (calibrador fechou para liberar webcam)

**Resultado Esperado:**
- Vídeo: Calibrador + Preview simultâneos
- Webcam: Calibrador fecha → Preview abre com webcam

---

## Template de Relatório Comercial

Após executar os testes, gerar um relatório em `Dev_log/Commercial_Report_Sprint_X.md`:

```markdown
# Relatório Comercial - Sprint X

**Data:** YYYY-MM-DD
**Testador:** [Nome do Testador]
**Ambiente:** Pop!_OS 22.04, Python 3.10, GTK 3.0

---

## Resumo Executivo

[2-3 linhas sobre o que foi testado e resultado geral]

---

## Testes Realizados

### Feature 1: [Nome]

**Status:** [OK] Aprovado / [FALHOU] Falhou / [PARCIAL] Parcial

**Screenshots:**

![Estado Inicial](caminho/screenshot_1.png)
*Legenda: Estado inicial da interface*

![Após Ação](caminho/screenshot_2.png)
*Legenda: Resultado após clicar em X*

**Validação:**
- [x] Critério 1
- [x] Critério 2
- [ ] Critério 3 (falhou)

**Observações:**
[Detalhes técnicos, bugs encontrados, sugestões]

---

### Feature 2: [Nome]

[...]

---

## Métricas

- **Testes Executados:** X
- **Aprovados:** Y
- **Falhados:** Z
- **Taxa de Sucesso:** Y/X%

---

## Bugs Encontrados

### Bug 1: [Título]
**Severidade:** Alta / Média / Baixa
**Descrição:** [...]
**Steps to Reproduce:** [...]
**Screenshot:** [...]

---

## Recomendações

1. [...]
2. [...]

---

## Conclusão

[Opinião final sobre a qualidade da sprint]
```

---

## Checklist de Validação de Sprint

Antes de aprovar uma sprint, verificar:

### Funcionalidade
- [ ] Todos os casos de teste passaram
- [ ] Não há erros no console/logs
- [ ] Performance aceitável (FPS, tempo de resposta)

### Interface
- [ ] Elementos visuais corretos (cores, bordas, ícones)
- [ ] Feedback visual claro (botões, estados, loading)
- [ ] Não há elementos sobrepostos ou cortados

### Arquivos
- [ ] Arquivos gerados no local correto
- [ ] Nomes de arquivo seguem padrão
- [ ] Conteúdo dos arquivos válido

### Documentação
- [ ] Dev_log atualizado
- [ ] README atualizado se necessário
- [ ] Commits linkados à issue/sprint

---

## Comandos Úteis para Validação

### Verificar Logs
```bash
tail -f logs/*.log
```

### Verificar Processos
```bash
ps aux | grep "extase\|python.*main.py"
```

### Verificar Arquivos Gerados
```bash
ls -lht ~/Vídeos | head -10
```

### Verificar Configuração
```bash
cat config.ini | grep -A 5 "ChromaKey"
```

### Forçar Limpeza
```bash
pkill -f "python.*main.py"
rm -f ~/Vídeos/screencast_*.mp4
```

---

## Situações Especiais

### Teste Falhou
1. Capturar screenshot do erro
2. Verificar logs em `logs/`
3. Reproduzir erro 2x para confirmar
4. Documentar no relatório
5. Criar issue no Dev_log

### Performance Degradada
1. Monitorar CPU/RAM com `htop`
2. Tirar screenshot do htop
3. Documentar FPS real vs esperado
4. Sugerir otimizações

### Interface Quebrada
1. Screenshot do problema
2. Verificar GTK warnings no terminal
3. Inspecionar .glade se necessário
4. Documentar inconsistência visual

---

**Última Atualização:** 2026-01-12
