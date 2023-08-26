from time import sleep

# I was bored, ignore this.

while True: # Play until closed
    for char in "\|/-": # animation chars
        print(char, end="\r", flush=True) # Print frame plus a carrage return
        sleep(0.1) # Sleep so you can actually see the animation.