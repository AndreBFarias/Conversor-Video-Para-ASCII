#!/bin/bash

LEGACY_FILE="src/tools/legacy_files.txt"
MAX_LINES=300

echo "========================================"
echo "   PROGRESSO DA MODULARIZACAO"
echo "========================================"
echo ""

if [ ! -f "$LEGACY_FILE" ]; then
    echo "ERRO: $LEGACY_FILE nao encontrado"
    exit 1
fi

P0_COUNT=0
P1_COUNT=0
P2_COUNT=0
DONE_COUNT=0
TOTAL=0

echo "ARQUIVOS LEGADOS (>$MAX_LINES linhas):"
echo "----------------------------------------"

while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^#.*$ ]] && continue
    [[ -z "$line" ]] && continue

    if [ -f "$line" ]; then
        lines=$(wc -l < "$line")
        TOTAL=$((TOTAL + 1))

        if [ "$lines" -gt 700 ]; then
            priority="P0"
            P0_COUNT=$((P0_COUNT + 1))
            color="\033[0;31m"
        elif [ "$lines" -gt 500 ]; then
            priority="P1"
            P1_COUNT=$((P1_COUNT + 1))
            color="\033[0;33m"
        elif [ "$lines" -gt 300 ]; then
            priority="P2"
            P2_COUNT=$((P2_COUNT + 1))
            color="\033[0;93m"
        else
            priority="OK"
            DONE_COUNT=$((DONE_COUNT + 1))
            color="\033[0;32m"
        fi

        printf "${color}[%s] %4d  %s\033[0m\n" "$priority" "$lines" "$line"
    else
        echo "[NOT FOUND] $line"
    fi
done < "$LEGACY_FILE"

echo ""
echo "========================================"
echo "RESUMO:"
echo "----------------------------------------"
echo "P0 (>700 linhas):  $P0_COUNT arquivos"
echo "P1 (500-700):      $P1_COUNT arquivos"
echo "P2 (300-500):      $P2_COUNT arquivos"
echo "Concluidos (<300): $DONE_COUNT arquivos"
echo "----------------------------------------"
echo "Total legados:     $TOTAL arquivos"

REMAINING=$((TOTAL - DONE_COUNT))
if [ "$REMAINING" -eq 0 ]; then
    echo ""
    echo "PARABENS! Todos os arquivos foram modularizados!"
    echo "Remova legacy_files.txt quando pronto."
    exit 0
else
    PROGRESS=$((DONE_COUNT * 100 / TOTAL))
    echo "Progresso:         $PROGRESS%"
    echo ""
    echo "Proximos passos:"
    echo "1. Trabalhar nos arquivos P0 primeiro"
    echo "2. Ver issues: gh issue list --label 'god-mode-fix'"
fi
