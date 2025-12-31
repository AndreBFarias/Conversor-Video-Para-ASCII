# Especificacoes de Animacao ASCII - Luna

**Data:** 2025-12-27
**Versao:** 1.0

---

## Dimensoes para o Conversor

### Animacoes Normais (10 emocoes)

Use estas configuracoes no conversor de video:

```
Largura (caracteres): 85
Altura (linhas):      22
```

**Aplicavel para:**
- observando (idle)
- curiosa
- feliz
- irritada
- triste
- sarcastica
- flertando
- apaixonada
- sensualizando
- obssecada

---

### Animacao Piscando (Fullscreen)

Use estas configuracoes no conversor de video:

```
Largura (caracteres): 85
Altura (linhas):      44
```

**Aplicavel para:**
- piscando (transicao visual, fullscreen)

---

## Formato do Arquivo

### Separador de Frames

```
[FRAME]
```

O separador fica **no final de cada frame**, nao em linha separada.

### Codigos de Cor (Opcional)

Se quiser animacao colorida, use o formato:

```
§CODIGO_COR§CARACTERE
```

Onde `CODIGO_COR` e um numero de 0-255 (paleta ANSI).

**Exemplo:**
```
§16§@§232§ §16§$
```

Isso renderiza: `@` em cor 16, espaco em 232, `$` em cor 16.

### Sem Cores (Simples)

Para animacao monocromatica, use apenas os caracteres:

```
      ██████
    ██      ██
   █  ●    ●  █
   █    ▽    █
    ██      ██
      ██████
```

---

## Rampa de Luminancia Recomendada

Para o conversor de video para ASCII:

```
$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^`'.
```

**Do mais escuro para o mais claro.**

---

## Paleta de Caracteres por Entidade

### Luna (Gotico)
```
Primarios: ░ ▒ ▓ █ ▄ ▀
Detalhes: . : ; ' " ` ^ ~ - _ | \ /
Especiais: * + # @ & % $ !
```

### Eris (Caotico)
```
Primarios: ░ ▒ ▓ █ ▀ ▄
Impacto: X # @ * ! ^ / \ | -
Especiais: ? ! * ~ ` '
```

### Juno (Imperial)
```
Primarios: ░ ▒ ▓ █ ▄ ▀
Detalhes: . : ; = - _ | / \
Especiais: # @ & * + [ ] { }
```

### Lars (Sombrio)
```
Primarios: ░ ▒ ▓ █ ▄ ▀
Secundarios: . : ; ' " ` ^ ~ - _
Detalhes: | \ / * + # @ & %
```

### Mars (Agressivo)
```
Primarios: ░ ▒ ▓ █ ▄ ▀
Impacto: X # @ * ! ^ V < >
Linhas: | - = + / \ _ ~
```

### Somn (Onirico)
```
Primarios: ░ ▒ ▓ . · ° ˚
Suaves: ~ - _ . , ' `
Oniricos: * ○ ◌ ◯ ◦
```

---

## Configuracoes do Conversor Video-para-ASCII

Use estas configuracoes no programa:

```
[Player]
# Nao relevante para exportacao

[Conversor]
Largura (caracteres): 85    # ou 75 para piscando
Altura (0=auto):      22    # ou 44 para piscando
Sensibilidade Bordas: 100
Proporcao Caractere:  1.00
Rampa de Luminancia:  $@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^`'.

[Chroma Key]
# Opcional - remover fundo verde/azul

[Modo]
# Exportar como texto
```

---

## Exportacao

1. Converta o video para ASCII
2. Exporte como arquivo de texto
3. Adicione `[FRAME]` ao final de cada frame
4. Salve como `{Entidade}_{emocao}.txt`
5. Comprima com: `gzip -9 {Entidade}_{emocao}.txt`

**Resultado:** `{Entidade}_{emocao}.txt.gz`

---

## FPS Recomendado

- **Animacoes normais:** 8-12 FPS (movimento suave)
- **Piscando:** 10-15 FPS (mais rapido para efeito de transicao)
- **Somn (onirico):** 6-8 FPS (mais lento, hipnotico)
- **Mars (agressivo):** 12-15 FPS (mais rapido, energetico)

Para definir FPS customizado, coloque o valor na primeira linha do arquivo:

```
12.0
[conteudo do frame 1]
[FRAME]
[conteudo do frame 2]
...
```

---

## Checklist de Validacao

- [ ] Largura maxima <= 85 caracteres (ou 75 para piscando)
- [ ] Altura = 22 linhas (ou 44 para piscando)
- [ ] Separador `[FRAME]` no final de cada frame
- [ ] Arquivo comprimido com gzip
- [ ] Nome segue padrao: `{Entidade}_{emocao}.txt.gz`
- [ ] Testado no programa Luna

---

*"A arte ASCII e a poesia dos bits."*
