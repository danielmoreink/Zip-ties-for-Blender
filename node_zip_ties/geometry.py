"""Pure geometry; coordinates are node-editor units, angles counterclockwise.

Routing and lane ordering adapted from comfyui-zip-ties (MIT), Safzan Pirani.
"""
from math import cos, sin, hypot


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, n):
    return (a[0] * n, a[1] * n)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def axes(angle):
    return (cos(angle), sin(angle)), (-sin(angle), cos(angle))


def lane(tie, key, spacing):
    tangent, normal = axes(tie['angle'])
    offset = (tie['members'].index(key) - (len(tie['members']) - 1) / 2) * spacing * tie.get('scale',1.0)
    return add(tie['pos'], mul(normal, offset)), tangent


def sample(curve, count=48):
    a, b, c, d = curve
    result = []
    for i in range(count + 1):
        t = i / count
        u = 1 - t
        result.append(tuple(u**3*a[k] + 3*u*u*t*b[k] + 3*u*t*t*c[k] + t**3*d[k] for k in (0, 1)))
    return result


def intersection(p, q, r, s):
    u, v, w = sub(q, p), sub(s, r), sub(r, p)
    cross = lambda a, b: a[0]*b[1] - a[1]*b[0]
    den = cross(u, v)
    if abs(den) < 1e-10:
        return None
    t, j = cross(w, v)/den, cross(w, u)/den
    return t if 0 <= t <= 1 and 0 <= j <= 1 else None


def curve_hit(p, q, curves):
    hits = []
    for curve in curves:
        points = sample(curve)
        for a, b in zip(points, points[1:]):
            t = intersection(p, q, a, b)
            if t is not None:
                delta = sub(b, a)
                length = hypot(*delta) or 1
                hits.append((t, mul(delta, 1 / length)))
    return min(hits, key=lambda h: h[0]) if hits else None


def half_length(tie, spacing):
    return ((len(tie['members']) - 1) * spacing / 2 + 3) * tie.get('scale',1.0)


def marker(tie, spacing=4.5, width=5):
    tangent, normal = axes(tie['angle'])
    h = half_length(tie, spacing)
    def transform(x, y):
        return add(tie['pos'], add(mul(tangent, x), mul(normal, y)))
    strap = [transform(x, y) for x, y in [(-width/2,-h),(width/2,-h),(width/2,h),(-width/2,h)]]
    collar = [transform(x,y) for x,y in [(-.67*width,h-.1*width),(.67*width,h-.1*width),
                                        (.67*width,h+.9*width),(-.67*width,h+.9*width)]]
    # Convex rounded-top flap. Positive normal is the locking-head end.
    left,right = -.47*width,.47*width
    bottom,top,radius = h+.05*width,h+1.7*width,.16*width
    tip = [(left,bottom),(right,bottom),(right,top-radius)]
    for i in range(1,7):
        angle = i/6*1.5707963267948966
        tip.append((right-radius+radius*cos(angle),top-radius+radius*sin(angle)))
    tip.append((left+radius,top))
    for i in range(1,7):
        angle = 1.5707963267948966+i/6*1.5707963267948966
        tip.append((left+radius+radius*cos(angle),top-radius+radius*sin(angle)))
    front = [(left,bottom),(right,bottom),(right,h+.55*width),(left,h+.55*width)]
    return strap,collar,[transform(x,y) for x,y in tip],[transform(x,y) for x,y in front]


def marker_hit(tie, p, spacing=4.5, width=5, pad=0):
    for poly in marker(tie,spacing,width):
        signs = []
        for a,b in zip(poly,poly[1:]+poly[:1]):
            edge,d = sub(b,a),sub(p,a)
            signs.append(edge[0]*d[1]-edge[1]*d[0])
            if pad>0:
                length = dot(edge,edge)
                t = max(0,min(1,dot(d,edge)/length)) if length else 0
                closest = sub(p,add(a,mul(edge,t)))
                if dot(closest,closest)<=pad*pad:
                    return True
        if all(s>=-1e-8 for s in signs) or all(s<=1e-8 for s in signs):
            return True
    return False


def marker_cut(tie, p, q, spacing=4.5, width=5):
    if marker_hit(tie, p, spacing, width) or marker_hit(tie, q, spacing, width):
        return True
    return any(intersection(p, q, a, b) is not None for poly in marker(tie, spacing, width)
               for a, b in zip(poly, poly[1:]+poly[:1]))
