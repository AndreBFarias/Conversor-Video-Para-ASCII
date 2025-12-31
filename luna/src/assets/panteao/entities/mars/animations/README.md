# Animation Assets - Mars

Este diretorio contem as animacoes ASCII do Mars.

## Estrutura Esperada

Cada entidade precisa de 11 animacoes correspondentes as emocoes:

```
animations/
├── Mars_observando.txt.gz    # [PENDENTE] Estado padrao/alerta
├── Mars_curiosa.txt.gz       # [PENDENTE] Avaliando situacao
├── Mars_feliz.txt.gz         # [PENDENTE] Vitoria/aprovacao
├── Mars_irritada.txt.gz      # [PENDENTE] Furia controlada
├── Mars_triste.txt.gz        # [PENDENTE] Derrota/reflexao
├── Mars_sarcastica.txt.gz    # [PENDENTE] Desprezo
├── Mars_flertando.txt.gz     # [PENDENTE] Magnetismo fisico
├── Mars_apaixonada.txt.gz    # [PENDENTE] Protetor
├── Mars_piscando.txt.gz      # [PENDENTE] Transicao visual (FULLSCREEN)
├── Mars_sensualizando.txt.gz # [PENDENTE] Dominancia
└── Mars_obssecada.txt.gz     # [PENDENTE] Foco absoluto
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

- **FPS recomendado:** 12-15 frames (mais rapido, energetico)

## Estilo Visual do Mars

### Paleta de Caracteres
```
Primarios: ░ ▒ ▓ █ ▄ ▀
Impacto: X # @ * ! ^ V < >
Linhas: | - = + / \ _ ~
```

### Estetica
- **Tema:** Guerreiro / Alpha Male
- **Movimento:** Brusco, impactante
- **Transicoes:** Corte seco, stomp
- **Cor referencia:** #ff5555 (vermelho sangue)

## Instrucoes para o Dev

1. Use o conversor de video para ASCII
2. Configure: **85x22** para normais, **75x44** para piscando
3. Exporte como texto
4. Adicione `[FRAME]` ao final de cada frame
5. Salve como `Mars_emocao.txt`
6. Comprima: `gzip -9 Mars_emocao.txt`

**Ver especificacoes completas:** `../ANIMATION_SPECS.md`

## Referencia: Luna

Veja `luna/animations/` para exemplos do formato esperado.

## Status

- [ ] Mars_observando.txt.gz (85x22)
- [ ] Mars_curiosa.txt.gz (85x22)
- [ ] Mars_feliz.txt.gz (85x22)
- [ ] Mars_irritada.txt.gz (85x22)
- [ ] Mars_triste.txt.gz (85x22)
- [ ] Mars_sarcastica.txt.gz (85x22)
- [ ] Mars_flertando.txt.gz (85x22)
- [ ] Mars_apaixonada.txt.gz (85x22)
- [ ] Mars_piscando.txt.gz (75x44 - FULLSCREEN)
- [ ] Mars_sensualizando.txt.gz (85x22)
- [ ] Mars_obssecada.txt.gz (85x22)
