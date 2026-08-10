#! /usr/bin/env python3 

import pyxel

class IntroScreen():
    def __init__(self):
        pyxel.init(500, 500, title="Fly-In")
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()

    def draw(self):
        pyxel.cls(0)
        pyxel.text(1, 1, "Hello to my Fly-In Project", 2)
        pyxel.blt(60, 60, 0, 0, 0, 38, 16)

IntroScreen()