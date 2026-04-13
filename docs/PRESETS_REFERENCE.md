# Referencia de Presets

Guia completo dos sistemas de presets disponiveis no Extase em 4R73.

## Rampas de Luminancia (ASCII Art)

As rampas de luminancia definem quais caracteres serao usados para representar diferentes niveis de brilho. Caracteres mais "densos" representam areas escuras, enquanto espacos representam areas claras.

### Presets Disponiveis

| Preset | Chars | Descricao | Uso Recomendado |
|--------|-------|-----------|-----------------|
| **Padrao** | 70 | Cobertura completa ASCII | Uso geral, maximo detalhe |
| **Simples** | 10 | Caracteres basicos | Videos com alto contraste |
| **Blocos** | 5 | Blocos solidos Unicode | Efeito retro, terminais UTF-8 |
| **Minimalista** | 5 | Conjunto reduzido | Arte minimalista, silhuetas |
| **Binario** | 7 | Estetica digital | Efeito Matrix/hacker |
| **Pontos** | 10 | Gradiente de pontos Unicode | Efeito halftone |
| **Letras** | 17 | Apenas A-Z por peso visual | Efeito tipografico |
| **Numeros** | 12 | Apenas 0-9 | Efeito digital/LED |
| **Setas** | 11 | Formas geometricas Unicode | Arte abstrata |

### Caracteres por Preset

```
Padrao:      $@B8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,"^`'.
Simples:     @%#*+=-:.
Blocos:      (blocos solidos Unicode graduados)
Minimalista: #=:.
Binario:     10!|:.
Pontos:      (circulos e pontos Unicode graduados)
Letras:      MWNXKOkxdolc;:,.
Numeros:     8906532147.
Setas:       (triangulos, quadrados, circulos Unicode)
```

### Como Escolher

1. **Para videos de pessoas/rostos**: Use "Padrao" ou "Simples"
2. **Para silhuetas simples**: Use "Minimalista" ou "Blocos"
3. **Para efeitos artisticos**: Experimente "Blocos", "Binario" ou "Setas"
4. **Para terminais sem UTF-8**: Use "Simples", "Letras" ou "Numeros"

---

## Paletas Fixas (Pixel Art)

Paletas fixas forcam o uso de um conjunto especifico de cores, criando efeitos retro ou tematicos.

### Paletas Retro (Hardware Real)

| Paleta | Cores | Hardware Original | Caracteristicas |
|--------|-------|-------------------|-----------------|
| **Game Boy** | 4 | Nintendo Game Boy | Verde monocromatico classico |
| **CGA** | 16 | IBM PC (1981) | Cores primarias saturadas |
| **NES** | 54 | Nintendo Entertainment System | Cores vibrantes de 8-bit |
| **Commodore 64** | 16 | Commodore 64 | Tom pastel caracteristico |
| **PICO-8** | 16 | Fantasy Console | Paleta curada para pixel art |

### Paletas Tematicas

| Paleta | Cores | Tema | Uso Ideal |
|--------|-------|------|-----------|
| **Escala de Cinza** | 8 | Monocromatico | Fotografia classica |
| **Sepia** | 8 | Vintage | Efeito antigo/nostalgico |
| **Cyberpunk** | 12 | Neon | Estetica futurista |
| **Dracula** | 11 | Editor de codigo | Tema escuro popular |
| **Monitor Verde** | 12 | CRT antigo | Efeito terminal retro |

### Cores por Paleta

#### Game Boy (4 cores)
```
RGB: (15,56,15), (48,98,48), (139,172,15), (155,188,15)
```

#### CGA (16 cores)
```
Preto, Azul, Verde, Ciano, Vermelho, Magenta, Marrom, Cinza Claro
Cinza Escuro, Azul Claro, Verde Claro, Ciano Claro, Vermelho Claro, Magenta Claro, Amarelo, Branco
```

#### PICO-8 (16 cores)
```
Preto, Azul Escuro, Roxo, Verde Escuro, Marrom, Cinza Escuro, Cinza Claro, Branco
Vermelho, Laranja, Amarelo, Verde, Azul, Lavanda, Rosa, Pessego
```

### Como Usar

1. Ative "Usar Paleta Fixa (Retro)" na aba Modo
2. Selecione a paleta desejada no combo
3. O conversor limitara as cores automaticamente

### Dicas de Uso

- **Para nostalgia de consoles**: Game Boy, NES ou C64
- **Para arte minimalista**: Escala de Cinza ou Sepia
- **Para estetica moderna**: Cyberpunk ou Dracula
- **Para efeito terminal**: Monitor Verde

---

## Configuracao via config.ini

Os presets sao salvos automaticamente no arquivo `config.ini`:

```ini
[Conversor]
luminance_preset = standard
luminance_ramp = $@B8&WM#*oahkbdpqwm...

[PixelArt]
use_fixed_palette = true
fixed_palette_name = gameboy
```

### Adicionando Presets Customizados

Edite `src/app/constants.py` para adicionar novos presets:

```python
LUMINANCE_RAMPS = {
    'meu_preset': {
        'name': 'Meu Preset Custom',
        'ramp': "ABC123..."
    },
    ...
}

FIXED_PALETTES = {
    'minha_paleta': {
        'name': 'Minha Paleta',
        'colors': [(R,G,B), (R,G,B), ...]
    },
    ...
}
```

---

## Proximas Versoes

Planejado para futuras atualizas:
- [ ] Preview visual das paletas na interface
- [ ] Importacao de paletas externas (.gpl, .ase)
- [ ] Editor visual de rampas de luminancia
- [ ] Presets por tipo de conteudo (rosto, paisagem, texto)
