#!/usr/bin/env python
import sys, unittest
import flvscreen

class TestFlvScreen(unittest.TestCase):

    def testBasic(self):
        Z = '\x00\x00\x00'*4
        screen = flvscreen.FlvScreen(2, 3, 3)
        def get(blks):
            return [ screen.get(x,y) for (x,y) in blks ]
        self.assertEqual(screen.block_size, 2)
        self.assertEqual(screen.block_width, 3)
        self.assertEqual(screen.block_height, 3)
        self.assertEqual(screen.pixel_width, 6)
        self.assertEqual(screen.pixel_height, 6)
        screen.dump()
        changed = screen.changed()
        self.assertEqual(changed, [(0,2),(1,2),(2,2), (0,1),(1,1),(2,1), (0,0),(1,0),(2,0)])
        self.assertEqual(get(changed),
                         [Z,Z,Z, Z,Z,Z, Z,Z,Z])
        screen.reset()
        screen.dump()
        changed = screen.changed()
        self.assertEqual(changed, [])
        self.assertEqual(get(changed), [])
        self.assertEqual(screen.blit_rgba(0,0,1,1, '\x11\x22\x33\x00'), 1)
        screen.dump()
        changed = screen.changed()
        self.assertEqual(changed, [(0,0)])
        self.assertEqual(get(changed),
                         ['\x00\x00\x00\x00\x00\x00\x33\x22\x11\x00\x00\x00'])
        self.assertEqual(screen.blit_rgba(0,0,1,1, '\x11\x22\x33\x00'), 0)
        screen.dump()
        changed = screen.changed()
        self.assertEqual(changed, [(0,0)])
        self.assertEqual(screen.blit_rgba(1,1,1,1, '\x44\x55\x66\x00'), 1)
        screen.dump()
        changed = screen.changed()
        self.assertEqual(changed, [(0,0)])
        self.assertEqual(get(changed),
                         ['\x00\x00\x00\x66\x55\x44\x33\x22\x11\x00\x00\x00'])
        screen.reset()
        self.assertEqual(screen.blit_rgba(1,1,2,2, '\x44\x55\x66\x00\x22\x22\x22\x00\x33\x33\x33\x00\x44\x44\x44\x00'), 2)
        screen.dump()
        changed = screen.changed()
        self.assertEqual(changed, [(0,1),(1,1),(1,0)])
        self.assertEqual(get(changed),
                         ['\x00\x00\x00\x00\x00\x00\x00\x00\x00\x33\x33\x33',
                          '\x00\x00\x00\x00\x00\x00\x44\x44\x44\x00\x00\x00',
                          '\x22\x22\x22\x00\x00\x00\x00\x00\x00\x00\x00\x00'])
        screen.reset()
        self.assertEqual(screen.blit_rgba(2,2,3,2, '\xaa\xaa\xaa\x00\xbb\xbb\xbb\x00\xcc\xcc\xcc\x00\xdd\xdd\xdd\x00\xee\xee\xee\x00\xff\xff\xff\x00'), 2)
        screen.dump()
        changed = screen.changed()
        self.assertEqual(changed, [(1,1),(2,1)])
        self.assertEqual(get([(1,1)]),
                         ['\xdd\xdd\xdd\xee\xee\xee\xaa\xaa\xaa\xbb\xbb\xbb'])
        self.assertEqual(get([(2,1)]),
                         ['\xff\xff\xff\x00\x00\x00\xcc\xcc\xcc\x00\x00\x00'])
        screen.reset()
        self.assertEqual(screen.blit_rgba(-1,-1,2,2, '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), 1)
        self.assertEqual(screen.blit_rgba(5,5,2,2, '\x99\x99\x99\x00\x99\x99\x99\x00\x99\x99\x99\x00\x99\x99\x99\x00'), 1)
        screen.dump()
        changed = screen.changed()
        self.assertEqual(changed, [(2,2), (0,0)])
        self.assertEqual(get(changed),
                         ['\x00\x00\x00\x99\x99\x99\x00\x00\x00\x00\x00\x00',
                          '\x00\x00\x00\x66\x55\x44\x00\x00\x00\x00\x00\x00'])
        self.assertRaises(TypeError, lambda : screen.get(1))
        self.assertRaises(TypeError, lambda : screen.get(1,''))
        self.assertRaises(flvscreen.FlvError, lambda : screen.get(-1,-1))
        self.assertRaises(flvscreen.FlvError, lambda : screen.blit_rgba(0,0,1,1, ''))
        return

    def testFLV2RGBA(self):
        self.assertEqual(flvscreen.flv2rgba(2, 2, '123456abcdef'),
                         'cba\x00fed\x00321\x00654\x00')
        self.assertRaises(flvscreen.FlvError, lambda : flvscreen.flv2rgba(2, 2, '12'))
        return

if __name__ == '__main__': unittest.main()
