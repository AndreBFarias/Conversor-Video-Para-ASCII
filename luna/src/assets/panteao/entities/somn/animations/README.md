# Animation Assets - Somn

Este diretorio contem as animacoes ASCII do Somn.

## Estrutura Esperada

Cada entidade precisa de 11 animacoes correspondentes as emocoes:

```
animations/
├── Somn_observando.txt.gz    # [PENDENTE] Estado padrao/sonolento
├── Somn_curiosa.txt.gz       # [PENDENTE] Despertando interesse
├── Somn_feliz.txt.gz         # [PENDENTE] Conforto pleno
├── Somn_irritada.txt.gz      # [PENDENTE] Perturbado (raro)
├── Somn_triste.txt.gz        # [PENDENTE] Pesadelo/melancolia
├── Somn_sarcastica.txt.gz    # [PENDENTE] Preguica consciente
├── Somn_flertando.txt.gz     # [PENDENTE] Aconchego sedutor
├── Somn_apaixonada.txt.gz    # [PENDENTE] Carinho pleno
├── Somn_piscando.txt.gz      # [PENDENTE] Transicao visual (FULLSCREEN)
├── Somn_sensualizando.txt.gz # [PENDENTE] Intimidade profunda
└── Somn_obssecada.txt.gz     # [PENDENTE] Sonho lucido
```

## Formato dos Arquivos

- **Extensao:** `.txt.gz` (texto comprimido com gzip)
- **Separador de frames:** `[FRAME]` no final de cada frame
- **Codigos de cor (opcional):** `§CODIGO§CARACTERE`

### Dimensoes - Animacoes Normais (10 emocoes)

```
Largura: 85 caracteres
Altura:  22 linhas por frame
```

### Dimensoes - Piscando (Fullscreen)

```
Largura: 75 caracteres
Altura:  44 linhas por frame
```

- **FPS recomendado:** 6-8 frames (lento, hipnotico)

## Estilo Visual do Somn

### Paleta de Caracteres
```
Primarios: ░ ▒ ▓ . · ° ˚ ✧
Suaves: ~ - _ . , ' `
Oniricos: * ☆ ○ ◌ ◯ ◦
```

### Estetica
- **Tema:** Soft Boy / ASMR / Sonho
- **Movimento:** Fluido, respirando, ondulante
- **Transicoes:** Fade lento, breathe
- **Cor referencia:** #8be9fd (azul onirico)

## Instrucoes para o Dev

1. Use o conversor de video para ASCII
2. Configure: **85x22** para normais, **75x44** para piscando
3. Exporte como texto
4. Adicione `[FRAME]` ao final de cada frame
5. Salve como `Somn_emocao.txt`
6. Comprima: `gzip -9 Somn_emocao.txt`

**Ver especificacoes completas:** `../ANIMATION_SPECS.md`

## Referencia: Luna

Veja `luna/animations/` para exemplos do formato esperado.

## Dicas Especificas para Somn

- Use menos contraste que outras entidades
- Movimentos devem parecer "respirando"
- Transicoes muito suaves entre frames
- Elementos flutuantes como nuvens ou estrelas

## Status

- [ ] Somn_observando.txt.gz (85x22)
- [ ] Somn_curiosa.txt.gz (85x22)
- [ ] Somn_feliz.txt.gz (85x22)
- [ ] Somn_irritada.txt.gz (85x22)
- [ ] Somn_triste.txt.gz (85x22)
- [ ] Somn_sarcastica.txt.gz (85x22)
- [ ] Somn_flertando.txt.gz (85x22)
- [ ] Somn_apaixonada.txt.gz (85x22)
- [ ] Somn_piscando.txt.gz (75x44 - FULLSCREEN)
- [ ] Somn_sensualizando.txt.gz (85x22)
- [ ] Somn_obssecada.txt.gz (85x22)
