import matplotlib.pyplot as plt

def generatePoints(n):
    import random as r
    r.seed(100)
    
    res = []
    for i in range(n):
        pt = [r.randint(0,300) for _ in [0, 1]]
        if [pt] not in res:
            res += [pt]
    return res

def norm(x, y):
    return (x*x+y*y)**.5

def dotProductNormed(x1, y1, x2, y2):
    return (x1*x2+y1*y2)/norm(x1, y1)/norm(x2, y2)

def cross(x1, y1, x2, y2):
    return x1*y2 - x2*y1

def graham(n, points):
    if n<3: return
    nframe = 0
    points.sort(key = lambda x: x[1])
    first = points[0]
    rest = points[1:]
    rest.sort(key = lambda x: -dotProductNormed(x[0]-points[0][0], x[1]-points[0][1], 1, 0))
    points = [first] + rest
    stack = [points[0], points[1]]
    i=2
    while i<n:
        x0, y0 = stack[-2][0], stack[-2][1]
        x1, y1 = stack[-1][0], stack[-1][1]
        x2, y2 = points[i][0], points[i][1]
        if cross(x1-x0, y1-y0, x2-x0, y2-y0)<0:
            stack.pop()
        else:
            stack += [points[i]]
            i+=1

    return stack

n = 90
pts = generatePoints(n)
l = []
y = []
for i in graham(n, pts):
  l.append(i[0])
  y.append(i[1])
graham(n, pts)
l.append(92)
y.append(2)
plt.plot(l, y) 
plt.show() 
