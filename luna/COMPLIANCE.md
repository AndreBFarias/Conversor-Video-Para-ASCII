# COMPLIANCE.md - Conformidade Legal e Etica

```
STATUS: ATIVO | VERSION: 1.0 | LANG: PT-BR
```

---

## 1. LICENCA E DISTRIBUICAO

### 1.1 Licenca do Projeto
- **Licenca:** GNU General Public License v3.0 (GPLv3)
- **Implicacoes:**
  - Codigo fonte aberto e livre
  - Modificacoes devem manter a mesma licenca
  - Uso comercial permitido com atribuicao
  - Nenhuma garantia implicita

### 1.2 Atribuicao
- O projeto e **anonimo por design**
- Nenhum contribuidor individual e creditado no codigo
- Contribuicoes sao comunitarias e impessoais

---

## 2. SERVICOS EXTERNOS E APIS

### 2.1 Regras de Uso
Todo servico externo (APIs, modelos, etc) deve seguir estas regras:

| Regra | Descricao |
|-------|-----------|
| **Sem identificadores** | IDs de contas, voice_ids, tokens nao devem ser versionados |
| **Variaveis de ambiente** | Credenciais sempre via .env (nunca hardcoded) |
| **Documentacao generica** | Nao mencionar contas especificas ou planos pagos |

### 2.2 Servicos Permitidos
| Servico | Uso | Restricoes |
|---------|-----|------------|
| Google Gemini | LLM chat | API key via .env |
| Ollama | LLM local | Nenhuma |
| Coqui TTS | Voz local | Modelos locais apenas |
| Chatterbox | Voz local | Modelos locais apenas |
| ElevenLabs | Voz cloud | API key + voice_id via .env |
| Faster-Whisper | STT local | Modelos locais apenas |

### 2.3 Dados Proibidos no Repositorio
Os seguintes dados **NUNCA** devem ser versionados:

```
BLOQUEADO:
├── API keys (GOOGLE_API_KEY, ELEVENLABS_API_KEY, etc)
├── Voice IDs especificos (identificam contas pagas)
├── Design prompts de voz (descrevem como recriar vozes)
├── Tokens de autenticacao
├── IDs de usuario/conta
├── Embeddings treinados com dados proprietarios
└── Qualquer identificador tracavel a pessoa/conta
```

---

## 3. VOZES E AUDIO

### 3.1 Politica de Vozes
- Vozes sao tratadas como **assets anonimos**
- Nenhuma voz identifica sua origem de criacao
- Arquivos de referencia (.wav) sao distribuidos comprimidos
- Modelos treinados (.pt) sao derivados de referencias locais

### 3.2 Atribuicao de Vozes
- Vozes NAO sao creditadas a servicos especificos
- Caracteristicas vocais sao descritas genericamente
- Nenhum "design prompt" e armazenado

### 3.3 Uso Etico
- Vozes NAO devem imitar pessoas reais sem consentimento
- Vozes sinteticas devem ser claramente identificaveis como IA
- Uso para deepfake ou fraude e **estritamente proibido**

---

## 4. INTELIGENCIA ARTIFICIAL

### 4.1 Uso de IA no Desenvolvimento
O uso de ferramentas de IA para desenvolvimento e **bem-vindo e encorajado**, desde que:

1. Codigo gerado siga as mesmas regras de qualidade
2. Nenhuma ferramenta de IA seja creditada no codigo
3. Outputs sejam revisados antes de commit
4. Testes sejam validados

### 4.2 Anonimato de Contribuicoes
```
PROIBIDO em codigo e commits:
├── Nomes de ferramentas IA (Claude, GPT, Gemini, etc)
├── "by AI" / "AI-generated" / "Feito por IA"
├── Assinaturas de servicos
├── Creditos a contribuidores especificos
└── Mencoes a planos pagos de servicos
```

### 4.3 Dados de Treinamento
- Nenhum dado proprietario e usado para treinamento
- Embeddings sao gerados localmente
- Memorias sao armazenadas apenas localmente

---

## 5. PRIVACIDADE E DADOS

### 5.1 Dados do Usuario
- Dados do usuario sao armazenados **apenas localmente**
- Nenhum dado e enviado para servidores externos (exceto APIs de chat/TTS)
- Sessoes e memorias ficam em `src/data_memory/`

### 5.2 Telemetria
- **Nenhuma telemetria** e coletada pelo projeto
- Nenhum analytics ou tracking
- Logs sao apenas locais e rotacionados

### 5.3 Dados Sensiveis
Os seguintes dados sao considerados sensiveis:

| Dado | Tratamento |
|------|------------|
| Conversas | Local apenas, nunca versionadas |
| Perfil de usuario | Local, em .gitignore |
| Memorias | Local, em .gitignore |
| Embeddings pessoais | Local, em .gitignore |

---

## 6. VERIFICACAO AUTOMATICA

### 6.1 Pre-commit Hooks
O projeto usa hooks automaticos para garantir conformidade:

| Hook | Verifica |
|------|----------|
| `check-anonymity` | Nomes de IAs, servicos, pessoas |
| `check-test-data` | Dados pessoais em testes |
| `check-external-ids` | Voice IDs, API keys hardcoded |
| `detect-private-key` | Chaves privadas no codigo |

### 6.2 Comandos de Validacao
```bash
# Verificar anonimato
bash scripts/check_anonymity.sh

# Verificar dados externos
bash scripts/check_external_ids.sh

# Validacao completa
bash scripts/validate_all.sh
```

---

## 7. RESPONSABILIDADES

### 7.1 Contribuidores
Ao contribuir, voce concorda que:
- Seu codigo sera licenciado sob GPLv3
- Voce nao sera creditado individualmente
- Seu codigo seguira as regras deste documento

### 7.2 Usuarios
Ao usar o projeto, voce concorda que:
- O uso e por sua conta e risco
- Nenhuma garantia e oferecida
- Voce e responsavel pelo uso etico

### 7.3 Mantenedores
O projeto se compromete a:
- Manter o codigo aberto e livre
- Nao coletar dados dos usuarios
- Seguir as regras deste documento

---

## 8. VIOLACOES

### 8.1 Reportando Violacoes
Se encontrar violacao de compliance:
1. Abra issue com label `compliance`
2. Descreva a violacao encontrada
3. Nao inclua dados sensiveis no report

### 8.2 Consequencias
Violacoes podem resultar em:
- Revert de commits
- Remocao de assets problematicos
- Ban de contribuidores em casos graves

---

## 9. ATUALIZACOES

Este documento pode ser atualizado. Mudancas significativas serao:
- Anunciadas em CHANGELOG.md
- Revisadas pela comunidade
- Versionadas junto com o projeto

---

*"Transparencia e a melhor politica de seguranca."*
