import sys, nuke


ru = nuke.nodes.Read(file = sys.argv[1], first=0996, last=1000)

rd = nuke.nodes.Read(file = sys.argv[2], first=0996, last=1000)

m = nuke.nodes.Merge()
m.setInput(0, ru)
m.setInput(1, rd)

w = nuke.nodes.Write(file = sys.argv[3])

w.setInput(0, m)

nuke.execute("Write1", 996, 1000)

