import heat2d

engine = heat2d.Engine()

@engine.add
class Main(heat2d.Stage):

    def created(self):
        print("Main stage is initialized!")

    def update(self):
        

engine.run()
