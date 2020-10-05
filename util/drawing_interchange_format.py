import io
from zipfile import ZipFile

from pathlib import Path
import cv2
import dxfgrabber
import numpy as np
from PIL import Image

import settings


class DrawingInterchangeFormat:

    def __init__(self, path_project: Path, materials: dict):
        self.dxf = dxfgrabber.readfile(path_project.joinpath('model2d.dxf'))
        self.folder = path_project.joinpath('maps')
        self.filenames = {
            'mod': str(self.folder.joinpath('model.png')),
            'per': str(self.folder.joinpath('permittivity.png')),
            'con': str(self.folder.joinpath('conductivity.png')),
            'den': str(self.folder.joinpath('density.png'))
        }
        self.width = settings.Img.width
        self.height = settings.Img.height
        self.materials = materials
        self.mm_per_px = None
        self.material_obj_names = []
        for material in materials:
            self.material_obj_names.append(material['object_name'].upper())

    def print(self) -> None:
        dxf = self.dxf
        entity_layers = []
        for ent in dxf.entities:
            if ent.layer not in entity_layers:
                entity_layers.append(ent.layer)
        print('  ' + '-' * 80)
        print('  filename: ', dxf.filename)
        print('  dxf version: ', dxf.dxfversion)
        print('  encoding: ', dxf.encoding)
        print('  headers: ', dxf.header)
        print('  #layers: ', len(dxf.layers))
        print('  layer names: ', dxf.layers.names())
        print('  #styles: ', len(dxf.styles))
        print('  style names: ', dxf.styles.names())
        print('  #line types: ', len(dxf.linetypes))
        print('  line type names', dxf.linetypes.names())
        print('  #blocks: ', len(dxf.blocks))
        print('  #objects: ', len(dxf.objects))
        print('  entities: ', len(dxf.entities))
        print('  entity-layers: ', entity_layers)
        for ent in dxf.entities:
            print('    ' + ent.dxftype + ' ' + ent.layer)
            ii = 0
            for point in ent.points:
                print('      [%02i] % 10.5f % 10.5f % 10.5f'
                      % (ii, point[0], point[1], point[2]))
                ii = ii + 1
        print('  ' + '-' * 80)

    def save(self, mm_per_px) -> None:
        self.mm_per_px = mm_per_px

        # create 'maps' folder if it doesn't exist yet
        if not Path(self.folder).exists():
            Path(self.folder).mkdir()

        # generate maps
        maps = self._generate_maps()

        # save them
        for key in maps:
            cv2.imwrite(self.filenames[key], maps[key])

    def _generate_maps(self):

        # extract lines from entities
        objects = {}
        for ent in self.dxf.entities:
            if ent.layer not in objects:
                objects[ent.layer] = _Object()
            objects[ent.layer].lines.append(_Line(ent))

        # combine lines into shapes,
        #   one object consists out of 1 or multiple shapes
        max_iter = 100
        for _, obj in objects.items():
            n_lines = len(obj.lines)
            for idx in range(max_iter):
                obj.combine_lines(0.1)
                # break loop if number of lines did not decrease
                if len(obj.lines) == n_lines:
                    break
                n_lines = len(obj.lines)

        # combine lines
        for _, obj in objects.items():
            obj.combine_lines(0.1)

        # create empty permittivity, conductivity & density maps
        img_shape = (settings.Img.height, settings.Img.width)
        img_shape_col = (settings.Img.height, settings.Img.width, 3)
        img_mod = np.ones(img_shape_col, np.uint8) * settings.DXF.background
        img_per = np.ones(img_shape, np.uint8) * settings.DXF.per0
        img_con = np.ones(img_shape, np.uint8) * settings.DXF.con0
        img_den = np.ones(img_shape, np.uint8) * settings.DXF.den0

        # draw shapes in the maps
        for name, obj in objects.items():
            m = self.materials[self.material_obj_names.index(name)]
            cm = (255 * m['red'], 255 * m['green'], 255 * m['blue'])
            cp = 255 * m['permittivity'] * settings.DXF.scalar_permittivity
            cc = 255 * m['conductivity'] * settings.DXF.scalar_conductivity
            cd = 255 * m['density'] * settings.DXF.scalar_density

            for line in obj.lines:
                pnts = [line.pixels(self.mm_per_px)]
                cv2.fillPoly(img_mod, pnts, color=cm)
                cv2.fillPoly(img_per, pnts, color=cp)
                cv2.fillPoly(img_con, pnts, color=cc)
                cv2.fillPoly(img_den, pnts, color=cd)

        return {'mod': img_mod, 'per': img_per, 'con': img_con, 'den': img_den}


class _Line:
    def __init__(self, ent):
        if ent.mode == 'spline2d':

            # obtain points
            points = np.array(ent.points)

            # discard unused dimension
            points = points[:, [0, 1]]

            # swap columns, so that x: width, z:height
            points[:, 0], points[:, 1] = points[:, 1], points[:, 0].copy()

        elif ent.mode == 'polyline2d':
            # only occurrence of this should be the circular boundary
            # with radius r, located at the center (0,0)
            points = self.arc_to_line(ent)

        else:
            raise Exception('ERROR: unknown mode encountered %s' %
                            ent.mode)

        self.points = points

    def start(self):
        return self.points[0, :]

    def end(self):
        return self.points[-1, :]

    def reverse(self):
        self.points = np.flipud(self.points)

    def pixels(self, mm_per_px):
        width, height = settings.Img.width, settings.Img.height

        # points are currently in [mm], convert it to [px]
        points = self.points / mm_per_px

        # align coordinate origin (0, 0) with center of image
        points = points + np.array([height / 2, width / 2])

        # round [px] to int values
        points = points.astype(np.int32)

        # remove duplicate points
        _, ids = np.unique(points, axis=0, return_index=True)
        points = points[np.sort(ids)]

        # change shape to the desired shape of cv2
        points = points.reshape((-1, 1, 2))

        return points

    @staticmethod
    def arc_to_line(ent):
        points = np.array([]).reshape((-1, 2))
        for v1, v2 in zip(ent.vertices[:-1], ent.vertices[1:]):
            d = _distance_3d(v1.location, v2.location)
            angle = 4 * np.arctan(v1.bulge)
            r = np.abs(d / (2 * np.sin(0.5 * angle)))

            # convert each location to angle relative to origin (0, 0)
            theta_start = np.arctan2(v1.location[0], v1.location[1])
            theta_end = theta_start - angle

            # generate points
            theta = np.linspace(theta_start, theta_end, settings.DXF.n_arc)
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            xy = np.vstack([x, y]).T

            # add points to list
            points = np.append(points, xy, 0)

        # return points
        return points


class _Object:
    def __init__(self):
        self.lines = []

    def combine_lines(self, thr):
        # loop through lines
        idx = 0
        while (idx + 1) < len(self.lines):

            # check if line[idx+1] can be added at the end of line[idx]
            if _distance(self.lines[idx].end(),
                         self.lines[idx + 1].start()) < thr:
                self._append_lines(idx, idx + 1)
                continue

            # check if line[idx+1] can be added at the start of line [idx]
            if _distance(self.lines[idx + 1].end(),
                         self.lines[idx].start()) < thr:
                self._append_lines(idx + 1, idx)
                continue

            # check the same but with the reverse
            self.lines[idx + 1].reverse()
            if _distance(self.lines[idx].end(),
                         self.lines[idx + 1].start()) < thr:
                self._append_lines(idx, idx + 1)
                continue

            idx += 1

    def _append_lines(self, idx1, idx2):
        # append points
        self.lines[idx1].points = np.append(
            self.lines[idx1].points,
            self.lines[idx2].points,
            axis=0
        )
        # set new end point
        self.lines[idx1].end = self.lines[idx2].end
        # remove second line
        del self.lines[idx2]


def _distance(point1, point2):
    return np.sum((point1 - point2) ** 2) ** 0.5


def _distance_3d(v1, v2):
    dx = v1[0] - v2[0]
    dy = v1[1] - v2[1]
    dz = v1[2] - v2[2]
    return (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
