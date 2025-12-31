# Terminal Sandbox - Sistema de Seguranca para Execucao de Comandos

## Visao Geral

O modulo `src/core/terminal_sandbox/` implementa um sistema de sandboxing para execucao segura de comandos de terminal. Ele classifica comandos por nivel de risco e aplica politicas de confirmacao e bloqueio para proteger o sistema de comandos destrutivos.

## Problema Resolvido

Quando a LLM gera comandos de terminal, ha risco de:
- Comandos destrutivos (`rm -rf /`)
- Escalacao de privilegios nao autorizada (`sudo`)
- Operacoes irreversiveis (`git push --force`)
- Modificacao de arquivos de sistema

O sandbox transforma a execucao de "arma carregada" para ferramenta segura com validacao em multiplas camadas.

## Arquitetura

```
src/core/terminal_sandbox/
├── __init__.py          # Exports publicos
├── models.py            # Enums e dataclasses
├── patterns.py          # Listas de padroes (blocked, critical, safe)
├── sandbox.py           # Classe TerminalSandbox
└── helpers.py           # Funcoes de conveniencia
```

## Niveis de Risco

| Nivel | Descricao | Comportamento |
|-------|-----------|---------------|
| `SAFE` | Comandos na whitelist (ls, git, cat, etc.) | Executa direto |
| `MODERATE` | Comandos fora da whitelist | Depende do `strict_mode` |
| `CRITICAL` | Comandos destrutivos (rm, sudo, kill, docker rm) | Requer confirmacao ou bloqueia |
| `DANGEROUS` | Comandos de sistema (iptables, crontab -r) | Bloqueado em strict mode |
| `BLOCKED` | Padroes cataclismicos (rm -rf /, fork bomb) | Sempre bloqueado |

## Modos de Execucao

### INTERACTIVE (Padrao)

Comandos criticos pedem confirmacao ao usuario via callback:

```python
def confirm_callback(command: str, risk: CommandRisk, reason: str) -> bool:
    print(f"Confirmar execucao de: {command}?")
    print(f"Risco: {risk.value} - {reason}")
    return input("(s/n): ").lower() == 's'

sandbox = TerminalSandbox(confirm_callback=confirm_callback)
sandbox.execute_sandboxed("rm -rf /tmp/old_files")
# Usuario ve: "Confirmar execucao de: rm -rf /tmp/old_files?"
```

### AUTONOMOUS

Comandos criticos sao automaticamente bloqueados:

```python
sandbox = TerminalSandbox(execution_mode=ExecutionMode.AUTONOMOUS)
exit_code, stdout, stderr = sandbox.execute_sandboxed("sudo apt update")
# exit_code = -1
# stderr = "[SANDBOX] Comando critico bloqueado em modo autonomo"
```

## Padroes de Comandos

### BLOCKED_PATTERNS (Nunca executam)

```python
BLOCKED_PATTERNS = [
    r"rm\s+(-rf?|--recursive)?\s*[/~]$",  # rm -rf /
    r"mkfs\.",                              # Formatar disco
    r"dd\s+if=.*/dev/",                     # Escrita em dispositivos
    r":\s*\(\s*\)\s*\{",                    # Fork bomb
    r"curl.*\|\s*(ba)?sh",                  # Pipe to bash
    r"/etc/passwd",                         # Arquivos sensiveis
    ...
]
```

### CRITICAL_PATTERNS (Requerem confirmacao)

```python
CRITICAL_PATTERNS = [
    (r"rm\s+(-[rfi]+\s+)?", "Remocao de arquivos"),
    (r"sudo\s+", "Execucao com privilegios elevados"),
    (r"docker\s+(rm|rmi|system\s+prune)", "Remocao de containers"),
    (r"git\s+push\s+.*--force", "Push forcado ao repositorio"),
    (r"kill\s+", "Encerrar processos"),
    ...
]
```

### SAFE_COMMANDS (Whitelist)

```python
SAFE_COMMANDS = {
    "ls", "pwd", "cd", "cat", "head", "tail",
    "grep", "find", "wc", "sort", "uniq", "diff",
    "git", "python", "python3", "pip", "pip3",
    "node", "npm", "npx", "yarn",
    "curl", "wget", "tar", "zip", "unzip",
    "ruff", "pytest", "mypy", "black", "isort",
    ...
}
```

## Uso Basico

### Analise de Comando

```python
from src.core.terminal_sandbox import TerminalSandbox, CommandRisk

sandbox = TerminalSandbox()
result = sandbox.analyze_command("rm -rf /tmp/test")

print(result.risk)                 # CommandRisk.CRITICAL
print(result.requires_confirmation)  # True
print(result.reason)               # "Comando critico: Remocao de arquivos"
```

### Execucao Segura

```python
from src.core.terminal_sandbox import execute_safe, is_command_safe

# Verificar antes de executar
if is_command_safe("ls -la"):
    exit_code, stdout, stderr = execute_safe("ls -la")

# Obter resumo de risco
from src.core.terminal_sandbox import get_command_risk
result = get_command_risk("sudo apt update")
print(result.risk.value)  # "critical"
```

### Configurar Modo Autonomo

```python
from src.core.terminal_sandbox import set_sandbox_mode, ExecutionMode

# Para agentes autonomos (sem interacao humana)
set_sandbox_mode(ExecutionMode.AUTONOMOUS)

# Qualquer comando critico sera automaticamente bloqueado
```

### Callback de Confirmacao

```python
from src.core.terminal_sandbox import set_confirm_callback, CommandRisk

def ui_confirm(command: str, risk: CommandRisk, reason: str) -> bool:
    # Mostrar dialog na UI
    from src.ui.dialogs import show_confirmation_dialog
    return show_confirmation_dialog(
        title="Confirmar Comando Critico",
        message=f"Comando: {command}\nRisco: {risk.value}\n{reason}",
    )

set_confirm_callback(ui_confirm)
```

## Validacoes Adicionais

### Validacao de Path

```python
sandbox = TerminalSandbox()

# Apenas paths seguros sao permitidos
sandbox.validate_path("~")       # True
sandbox.validate_path("/tmp")    # True
sandbox.validate_path("/etc")    # False
```

### Limite de Tamanho

Comandos com mais de 1024 caracteres sao bloqueados para prevenir ataques de buffer.

### Timeout

```python
# Maximo de 120 segundos
exit_code, stdout, stderr = sandbox.execute_sandboxed(
    "long_running_command",
    timeout=60,  # Sera respeitado ate o maximo de 120
)
```

## Ambiente Seguro

O sandbox cria um ambiente de execucao restrito:

```python
safe_env = {
    "HOME": str(Path.home()),
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    # LD_PRELOAD, LD_LIBRARY_PATH removidos
}
```

## Logging de Comandos Negados

```python
sandbox = TerminalSandbox(confirm_callback=deny_callback)
sandbox.execute_sandboxed("rm test.txt")

# Ver comandos que foram negados
denied = sandbox.get_denied_commands()
print(denied)  # ["rm test.txt"]

# Limpar log
sandbox.clear_denied_commands()
```

## Integracao com TerminalExecutor

O `TerminalExecutor` usa o sandbox internamente:

```python
from src.core.terminal_executor import TerminalExecutor

executor = TerminalExecutor()
# Todas as execucoes passam pelo sandbox
exit_code, stdout, stderr = executor.execute("ls -la")
```

## Metricas

O sandbox registra:
- Comandos bloqueados por padrao
- Comandos negados pelo usuario
- Tempo de execucao
- Exit codes

## Testes

52 testes em `src/tests/test_terminal_sandbox.py`:

- TestCommandRisk: 2 testes
- TestExecutionMode: 1 teste
- TestSandboxResult: 1 teste
- TestTerminalSandboxInit: 3 testes
- TestAnalyzeCommand: 13 testes
- TestExecutionModes: 5 testes
- TestConfirmationCallback: 7 testes
- TestExecuteSandboxed: 5 testes
- TestHelperFunctions: 3 testes
- TestRiskSummary: 1 teste
- TestPatterns: 3 testes
- TestPathValidation: 3 testes
- TestTimeoutSanitization: 4 testes

## Exemplo Completo

```python
from src.core.terminal_sandbox import (
    TerminalSandbox,
    ExecutionMode,
    CommandRisk,
)

def safe_terminal_agent():
    # Criar sandbox em modo autonomo para agente
    sandbox = TerminalSandbox(execution_mode=ExecutionMode.AUTONOMOUS)

    commands = [
        "ls -la",           # SAFE - executa
        "git status",       # SAFE - executa
        "rm old_file.txt",  # CRITICAL - bloqueado
        "sudo apt update",  # CRITICAL - bloqueado
    ]

    for cmd in commands:
        result = sandbox.analyze_command(cmd)

        if result.risk == CommandRisk.SAFE:
            exit_code, stdout, _ = sandbox.execute_sandboxed(cmd)
            print(f"[OK] {cmd}: {stdout[:50]}")
        else:
            print(f"[BLOQUEADO] {cmd}: {result.reason}")

# Output:
# [OK] ls -la: total 120\n...
# [OK] git status: On branch main\n...
# [BLOQUEADO] rm old_file.txt: Comando critico: Remocao de arquivos
# [BLOQUEADO] sudo apt update: Comando critico: Execucao com privilegios elevados
```
