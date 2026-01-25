
import sys
import os
sys.path.append(os.getcwd())
try:
    import scrawl.engine
    print(f"File: {scrawl.engine.__file__}")
    print(f"Package Dir: {scrawl.engine.PACKAGE_DIR}")
    font_path = scrawl.engine.get_resource_path('LXGWWenKai-Medium.ttf')
    print(f"Font Path: {font_path}")
    print(f"Exists: {os.path.exists(font_path)}")

    import pygame
    pygame.font.init()
    try:
        f = pygame.font.Font(font_path, 20)
        print("Font loaded successfully")
    except Exception as e:
        print(f"Font load failed: {e}")
except ImportError as e:
    print(f"Import failed: {e}")
