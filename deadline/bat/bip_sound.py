import winsound
import time

for i in range(3):
    # Play a bip sound with a frequency of 500 Hz for a duration of 1000 ms (1 second)
    winsound.Beep(500, 1000)
    
    # If it's not the last iteration, sleep for 1 second before playing the next bip
    if i < 2:
        time.sleep(1.5)


