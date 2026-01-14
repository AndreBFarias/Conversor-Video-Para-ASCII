#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.realtime_ascii import main as realtime_main

if __name__ == '__main__':
    print("Abrindo webcam ASCII em tempo real...")
    print("Pressione 'q' para sair")
    realtime_main()
