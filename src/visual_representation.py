#! /usr/bin/env python3 

import pyxel

phase = 0

class IntroScreen():
    def __init__(self):
        pyxel.init(500, 500, title="Fly-In")
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()

    def draw(self):
        phase = 0

        for x in range(0, 128, 4):
            for y in range(0, 128, 4):
                dist = pyxel.sqrt((x - 64) ** 2 + (y - 64) ** 2)
                offset_x = pyxel.sin(dist * 20 + phase) * 2.5
                offset_y = pyxel.sin(offset_x * 25) * 2.5
                color = int(15 - dist * 0.2) % 16
                pyxel.circ(x + offset_x, y + offset_y, 1, color)

        phase += 360 / 30

        pyxel.flip()

while True:
    screen = IntroScreen()
    screen.draw()