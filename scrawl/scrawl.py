import sys
import pygame

class Scene:
    pass

class Sprite:
    pass

class Game:
    def run(self):
        pygame.init()
        self.screen = pygame.display.set_mode(size)
        pygame.display.set_caption(self.title)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            yield_list = {}
            for sprite in sprites:
                yield_return = sprite.main()
                if yield_return in yield_list:
                    yield_list[yield_return].append(sprite.main)
