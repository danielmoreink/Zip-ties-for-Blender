"""Frozen guide geometry for tie sliding between immediate neighbours."""
from bisect import bisect_right
from math import hypot
from . import geometry as g, routing, sockets


def lengths(points):
    result = [0.0]
    for a,b in zip(points,points[1:]):
        result.append(result[-1]+hypot(*g.sub(b,a)))
    return result


def at_distance(points,cumulative,distance):
    distance = max(0,min(cumulative[-1],distance))
    i = min(len(points)-2,max(0,bisect_right(cumulative,distance)-1))
    span = cumulative[i+1]-cumulative[i]
    factor = (distance-cumulative[i])/span if span else 0
    return g.add(points[i],g.mul(g.sub(points[i+1],points[i]),factor))


def project(points,position):
    """Closest point on a frozen polyline; never extend past its endpoints."""
    best = None
    for a,b in zip(points,points[1:]):
        delta = g.sub(b,a)
        denom = g.dot(delta,delta)
        factor = max(0,min(1,g.dot(g.sub(position,a),delta)/denom)) if denom else 0
        point = g.add(a,g.mul(delta,factor))
        offset = g.sub(point,position)
        score = g.dot(offset,offset)
        if best is None or score < best[0]:
            best = score,point
    return best[1] if best else tuple(position)


def slide_guide(tree,tie,context):
    """Sample only links between the surrounding ties or endpoint sockets.

    The current incoming link, three helper centres, and outgoing link form
    each member's local span. Average member positions at signed arc distance
    from the centre. Freeze the guide before any movement to avoid feedback.
    """
    strands = []
    for key in tie['members']:
        chain = routing.path(tree,key)
        indices = [i for i,l in enumerate(chain)
                   if l.to_node.get(routing.TIE)==tie['id'] and routing.managed(l.to_node)]
        if not indices:
            continue
        span = chain[min(indices):max(indices)+2]
        points = []
        center = None
        for link in span:
            samples = g.sample(sockets.controls(link,context))
            points.extend(samples if not points else samples[1:])
            if link.to_node.get(routing.TIE)==tie['id'] and link.to_node.get(routing.SLOT)==1:
                center = len(points)-1
        if center is None or len(points)<2:
            continue
        cumulative = lengths(points)
        strands.append((points,cumulative,cumulative[center]))
    if not strands:
        return [tuple(tie['pos']),tuple(tie['pos'])]
    from .preferences import prefs
    clearance = max(12,prefs(context).width)+4
    lo = min(0,-min(s[2] for s in strands)+clearance)
    hi = max(0,min(s[1][-1]-s[2] for s in strands)-clearance)
    distances = [lo*(1-i/96) for i in range(96)]+[0]+[hi*i/96 for i in range(1,97)]
    guide = []
    for distance in distances:
        points = [at_distance(p,c,c0+distance) for p,c,c0 in strands]
        guide.append(tuple(sum(p[k] for p in points)/len(points) for k in (0,1)))
    offset = g.sub(tie['pos'],guide[96])
    return [g.add(p,offset) for p in guide]
