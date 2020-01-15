start = 0
list = []
inc=0
counter=0
while inc <= 650:
    inc += 1
    counter += 1
    if counter >= 10:
        start += 10
        list.append(start)
        counter = 0
        
print list
        