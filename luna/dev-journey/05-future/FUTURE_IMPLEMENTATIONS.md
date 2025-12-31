# Futuras Implementacoes - Luna

Este arquivo documenta funcionalidades planejadas para implementacao futura.

---

## 1. Memorizacao de Voz do Usuario

### Descricao
Implementar um sistema de memorizacao de voz similar ao reconhecimento facial existente.
Permitira que Luna reconheca usuarios pela voz, mesmo quando a webcam nao esta ativa.

### Proposta Tecnica
- Criar `src/soul/memoria_voz.py` seguindo a estrutura de `src/soul/memoria.py`
- Usar embeddings de voz via modelo speaker recognition (ex: SpeechBrain, ECAPA-TDNN)
- Armazenar vetores de caracteristicas vocais em `src/data_memory/vozes.json`
- Integrar com `src/soul/comunicacao.py` para identificacao durante transcricao

### Estrutura Proposta
```python
class MemoriaDeVozes:
    def __init__(self, db_path: str = None):
        # Similar a MemoriaDeRostos
        pass

    def registrar_voz(self, nome: str, embedding: np.ndarray) -> bool:
        # Registra embedding de voz associado a um nome
        pass

    def identificar_voz(self, embedding: np.ndarray, tolerance: float = 0.3) -> tuple:
        # Identifica usuario pelo embedding de voz
        pass
```

### Dependencias Necessarias
- `speechbrain` ou modelo similar para embeddings de voz
- Integracao com pipeline de audio existente

### Status
- [ ] Pesquisar melhores modelos de speaker recognition leves
- [ ] Definir formato de armazenamento
- [ ] Implementar classe MemoriaDeVozes
- [ ] Integrar com OuvidoSussurrante
- [ ] Testar com multiplos usuarios

---

## 2. Reconhecimento Facial (Existente - Verificado)

### Status Atual
O reconhecimento facial JA ESTA implementado e funcionando:
- `src/soul/memoria.py` - Classe MemoriaDeRostos
- `src/soul/visao.py` - Usa MemoriaDeRostos para identificar pessoas
- Armazena em `src/data_memory/rostos.json`

### Funcionalidades
- Detecta rostos novos e conhecidos
- Registra rostos com nomes via comando de voz
- Persiste embeddings em JSON
- Integrado com olhar_inteligente()

---

## Historico de Atualizacoes

| Data | Descricao |
|------|-----------|
| 2025-12-07 | Arquivo criado durante refatoracao v3.0 |
| 2025-12-07 | Documentada necessidade de memorizacao de voz |
