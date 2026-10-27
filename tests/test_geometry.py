import importlib.util
from pathlib import Path
import math
import unittest

spec = importlib.util.spec_from_file_location('geometry',Path(__file__).resolve().parents[1]/'node_zip_ties'/'geometry.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


class GeometryTests(unittest.TestCase):
    def test_three_lanes_and_rotated_tangents(self):
        t = dict(pos=[100,50],angle=math.pi/2,members=['a','b','c'])
        self.assertEqual(g.lane(t,'b',4.5)[0],(100,50))
        self.assertAlmostEqual(g.lane(t,'a',4.5)[0][0],104.5)
        tangent = g.lane(t,'b',4.5)[1]
        self.assertAlmostEqual(tangent[0],0)
        self.assertAlmostEqual(tangent[1],1)

    def test_curve_intersection_not_bounding_box(self):
        c = [(0,0),(0,100),(100,100),(100,0)]
        self.assertIsNone(g.curve_hit((45,10),(55,10),[c]))
        self.assertIsNotNone(g.curve_hit((50,60),(50,90),[c]))

    def test_marker_hit_rotated_head_and_cut(self):
        t = dict(pos=[0,0],angle=math.pi/2,members=['a','b','c'])
        self.assertTrue(g.marker_hit(t,(0,0)))
        self.assertFalse(g.marker_hit(t,(100,0)))
        self.assertTrue(g.marker_cut(t,(-20,0),(20,0)))

    def test_parallel_segments_and_endpoint(self):
        self.assertIsNone(g.intersection((0,0),(1,0),(0,1),(1,1)))
        self.assertEqual(g.intersection((0,0),(1,0),(1,0),(1,1)),1)

    def test_folded_head_geometry_matches_picking(self):
        t = dict(pos=[20,30],angle=.7,members=['a','b','c'],scale=1.5)
        polys = g.marker(t,8,8)
        self.assertEqual(len(polys),4)
        self.assertGreater(len(polys[2]),8)  # rounded tip, not a square head
        tangent,normal = g.axes(t['angle'])
        h = g.half_length(t,8)
        tip_centre = g.add(t['pos'],g.mul(normal,h+8))
        self.assertTrue(g.marker_hit(t,tip_centre,8,8))
        self.assertTrue(g.marker_cut(t,g.add(tip_centre,g.mul(tangent,-12)),g.add(tip_centre,g.mul(tangent,12)),8,8))
        # A point in the rounded tip's missing corner must not be clickable.
        corner = g.add(t['pos'],g.add(g.mul(tangent,.47*8),g.mul(normal,h+1.7*8)))
        self.assertFalse(g.marker_hit(t,corner,8,8))


if __name__ == '__main__':
    unittest.main()
