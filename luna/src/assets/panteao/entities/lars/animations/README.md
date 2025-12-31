# Animation Assets - Lars

Este diretorio contem as animacoes ASCII do Lars.

## Estrutura Esperada

Cada entidade precisa de 11 animacoes correspondentes as emocoes:

```
animations/
├── Lars_observando.txt.gz    # [PENDENTE] Estado padrao/idle
├── Lars_curiosa.txt.gz       # [PENDENTE] Analisando algo
├── Lars_feliz.txt.gz         # [PENDENTE] Satisfacao sombria
├── Lars_irritada.txt.gz      # [PENDENTE] Tedio/irritacao controlada
├── Lars_triste.txt.gz        # [PENDENTE] Melancolia profunda
├── Lars_sarcastica.txt.gz    # [PENDENTE] Ironia sombria
├── Lars_flertando.txt.gz     # [PENDENTE] Seducao intelectual
├── Lars_apaixonada.txt.gz    # [PENDENTE] Fascinio
├── Lars_piscando.txt.gz      # [PENDENTE] Transicao visual (FULLSCREEN)
├── Lars_sensualizando.txt.gz # [PENDENTE] Seducao profunda
└── Lars_obssecada.txt.gz     # [PENDENTE] Fixacao intensa
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

- **FPS recomendado:** 8-12 frames

## Estilo Visual do Lars

### Paleta de Caracteres
```
Primarios: ░ ▒ ▓ █ ▄ ▀
Secundarios: . : ; ' " ` ^ ~ - _ | \ /
Detalhes: * + # @ & % $ !
```

### Estetica
- **Tema:** Dark Academia / Vampiro Moderno
- **Movimento:** Lento, emergindo das sombras
- **Transicoes:** Fade suave, materializacao gradual
- **Cor referencia:** #50fa7b (verde misterio)

## Instrucoes para o Dev

1. Use o conversor de video para ASCII
2. Configure: **85x22** para normais, **75x44** para piscando
3. Exporte como texto
4. Adicione `[FRAME]` ao final de cada frame
5. Salve como `Lars_emocao.txt`
6. Comprima: `gzip -9 Lars_emocao.txt`

**Ver especificacoes completas:** `../ANIMATION_SPECS.md`

## Referencia: Luna

Veja `luna/animations/` para exemplos do formato esperado.

## Status

- [ ] Lars_observando.txt.gz (85x22)
- [ ] Lars_curiosa.txt.gz (85x22)
- [ ] Lars_feliz.txt.gz (85x22)
- [ ] Lars_irritada.txt.gz (85x22)
- [ ] Lars_triste.txt.gz (85x22)
- [ ] Lars_sarcastica.txt.gz (85x22)
- [ ] Lars_flertando.txt.gz (85x22)
- [ ] Lars_apaixonada.txt.gz (85x22)
- [ ] Lars_piscando.txt.gz (75x44 - FULLSCREEN)
- [ ] Lars_sensualizando.txt.gz (85x22)
- [ ] Lars_obssecada.txt.gz (85x22)
