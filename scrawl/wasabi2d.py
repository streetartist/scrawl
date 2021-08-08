import wasabi2d as w2d

scene = w2d.Scene()
scene.background = 0.9, 0.9, 1.0

scene.layers[0].set_effect('dropshadow')
circle = scene.layers[0].add_circle(
    radius=30,
    pos=(400, 300),
    color='red',
)

@w2d.event
def on_mouse_move(pos):
    circle.pos = pos

w2d.run()
