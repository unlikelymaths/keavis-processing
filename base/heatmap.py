from itertools import chain
from config import grid_size

def coordinate_distance(coords1, coords2):
    return pow(pow(coords1[0] - coords2[0], 2) + 
               pow(coords1[1] - coords2[1], 2), 0.5)

def merge_coordinates(coords1, coords2, weight1, weight2):
    total_weight = weight1 + weight2
    weight1 = weight1 / total_weight
    weight2 = weight2 / total_weight
    return (coords1[0] * weight1 + coords2[0] * weight2,
            coords1[1] * weight1 + coords2[1] * weight2)

class HeatmapEntry():
    def __init__(self, coords):
        self.coords = coords
        self.index = None

class Heatmap():
    
    def __init__(self):
        self.points = []
        self.grid = None

    def add(self, data):
        if isinstance(data, Heatmap):
            self.points = self.points + data.points
        elif isinstance(data, HeatmapEntry):
            self.points.append(data)
        else:
            self.points.append(HeatmapEntry(data))

    def min_pair(self, grid_info, last_pair, last_distance):
        min_pair = None
        min_distance = float('inf')
        for i in chain(range(last_pair[0],len(grid_info)), range(last_pair[0])):
            for j in range(i+1, len(grid_info)):
                distance = coordinate_distance(grid_info[i][0],grid_info[j][0])
                if distance < min_distance:
                    min_distance = distance
                    min_pair = (i,j)
                if distance <= last_distance * 1.2:
                    return (i,j), last_distance
        return min_pair, min_distance
    
    def merge_pair(self, grid_info, pair):
        i,j = pair
        coords1, weight1, entries1 = grid_info[i]
        coords2, weight2, entries2 = grid_info.pop(j)
        grid_info[i] = (merge_coordinates(coords1, coords2, weight1, weight2),
                        weight1 + weight2, entries1 + entries2)

    def reduce(self):
        grid_info = [(entry.coords,1,[entry]) for entry in self.points]
        last_distance = 1.e-5
        min_pair = (0,1)
        while len(grid_info) > grid_size:
            #print('Size: {}/{} (pair={}, last={})'.format(len(grid_info), grid_size, min_pair, last_distance))
            min_pair, last_distance = self.min_pair(grid_info, min_pair, last_distance)
            self.merge_pair(grid_info,min_pair)
        self.grid = [None,] * grid_size
        for index, grid_entry in enumerate(grid_info):
            self.grid[index] = grid_entry[0]
            for entry in grid_entry[2]:
                entry.index = index

    @property
    def weights(self):
        weights = [0,] * grid_size
        for point in self.points:
            weights[point.index] += 1
        return weights