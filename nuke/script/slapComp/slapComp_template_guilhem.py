import sys, nuke

start_frame = 996
last_frame = 1000


ru = nuke.nodes.Read(file = sys.argv[2], first=start_frame, last=last_frame)

rd = nuke.nodes.Read(file = sys.argv[1], first=start_frame, last=last_frame)

m = nuke.nodes.Merge(operation='over')
m.setInput(0, ru)
m.setInput(1, rd)

w = nuke.nodes.Write(file = sys.argv[3])

w.setInput(0, m)

nuke.execute("Write1", start_frame, last_frame)

