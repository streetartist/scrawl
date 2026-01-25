
class Sprite:
    def __init__(self):
        self.visible = True

def task_func(obj):
    # Simulating what might happen in a task loop
    try:
        if not obj.visible: # This line would cause 'str' object has no attribute 'visible' if obj is a string
            pass
    except AttributeError as e:
        print(f"Caught expected error: {e}")

# Simulate the error scenario
obj = "I am a string, not a sprite"
task_func(obj)
