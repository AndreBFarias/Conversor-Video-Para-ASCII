# Política de Segurança

## Versões Suportadas

Apenas a versão mais recente recebe atualizações de segurança.

| Versão | Suporte |
|--------|---------|
| 1.0.x  | Sim Suportada |
| < 1.0  | Nao Não suportada |

---

## Reportar uma Vulnerabilidade

### Processo

Se você descobrir uma vulnerabilidade de segurança, por favor:

1. **NÃO abra uma issue pública**
2. Envie email para: **security@example.com**
3. Inclua:
   - Descrição da vulnerabilidade
   - Passos para reproduzir
   - Versão afetada
   - Impacto potencial
   - Sugestão de correção (se tiver)

### O que esperar

- **Confirmação:** Dentro de 48 horas
- **Avaliação:** Dentro de 7 dias (classificação de severidade)
- **Correção:** Cronograma baseado na severidade
  - **Crítica:** Patch emergencial em 24-48h
  - **Alta:** Patch em 7 dias
  - **Média:** Próxima release (1-2 semanas)
  - **Baixa:** Próxima release menor

### Divulgação

- **Responsável:** Não divulgue publicamente até que um patch seja lançado
- **Crédito:** Você será creditado no changelog (se desejar)
- **CVE:** Para vulnerabilidades críticas, solicitaremos CVE ID

---

## Escopo de Segurança

### Dentro do Escopo

- Execução arbitrária de código
- Vazamento de informações sensíveis
- Injeção (SQL, command, path traversal)
- Deserialização insegura
- Vulnerabilidades de dependências críticas

### Fora do Escopo

- DoS local (aplicação desktop, esperado)
- Issues de UX/UI sem impacto de segurança
- Vulnerabilidades em versões não suportadas
- Dependências opcionais (CUDA, CuPy)

---

## Melhores Práticas para Usuários

### Instalação Segura

```bash
# Sempre verifique checksums de releases
sha256sum extase-em-4r73_1.0.0_amd64.deb
# Compare com SHA256 oficial no GitHub Releases
```

### Uso Seguro

- **Não rode como root** (exceto para instalação)
- **Mantenha atualizado** (releases de segurança prioritários)
- **Valide inputs** (vídeos de fontes confiáveis)
- **Revise config.ini** (evite paths absolutos maliciosos)

### Dados Sensíveis

- **Chroma key:** Configurações não contêm dados sensíveis
- **Logs:** Podem conter paths de arquivos (não compartilhe publicamente)
- **Vídeos:** Aplicação não transmite dados pela rede

---

## Dependências

Monitoramos vulnerabilidades em:

- Python (>= 3.10)
- NumPy
- OpenCV
- GTK3
- CuPy (opcional)

Atualizações de segurança são aplicadas assim que disponíveis.

---

## Histórico de Segurança

Nenhuma vulnerabilidade reportada até o momento.

---

## Contato

**Email de Segurança:** security@example.com
**Resposta em:** 48 horas
**Criptografia:** PGP disponível sob requisição

---

**Última Atualização:** 2026-01-13
