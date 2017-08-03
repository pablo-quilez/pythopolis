# -----------------------------------------------------------------------------
# This file contains the tools for terraing generating
# -----------------------------------------------------------------------------
# The map is stored as dictionary:
#   dic[(x,y)]["elevation"] = float
#   dic[(x,y)]["terrain"] = string --> beach, forest, snow, soil, sea, river
# This map format will be referred as map
# A tile is a tuple (x,y) referring a map position
# size is a tuple (x,y) containing the size of the map
# -----------------------------------------------------------------------------

import random
import copy
import sys

# Returns a filled new map
# Pre:  rows, columns as number of rows and columns of the map
#       x_level_start/_end is an integer between -255 and 255 to set the altitude of different
#       type of terrain. For example, everything under sea_level will be filled with salt water
def generateNewMap(rows, columns, sea_level = -64, tree_level_start = 32, tree_level_end = 156, snow_level = 192):

    sys.setrecursionlimit(rows * columns) # Necessary to allow large maps generation

    # Generate at least 10 mountain summits in order to have some rivers
    ok = True
    while (ok):

        print "Regenerating because more summits are needed"

        # Diamont height algorithm, initialize height in 4 corners randomly
        map = dict()
        map[(0,0)] = {"elevation": random.randint(-256,256)}
        map[(0,columns-1)] = {"elevation": random.randint(-256,256)}
        map[(rows-1,0)] = {"elevation": random.randint(-256,256)}
        map[(rows-1,columns-1)] = {"elevation": random.randint(-256,256)}

        # Generate all heights in the map
        generate_heights(map,(rows,columns),0,0,rows-1,columns-1)
        # 10 summits in order to have more beautiful maps. 
        # TODO: this can be done more efficiently.
        ok = len(get_mountain_summits(map, (rows,columns), snow_level)) < 10

    # Rivers are generating following a gradient-descend self-made algorithm
    generate_rivers(map, (rows, columns), sea_level, snow_level)

    # Mark the tiles according to elevation
    for row in range (0,rows):
        for column in range (0,columns):
            if "terrain" not in map[(row,column)]:
                if map[(row,column)]["elevation"] > sea_level:
                    if (map[(row,column)]["elevation"] > sea_level) and (map[(row,column)]["elevation"] < sea_level + 10):
                        map[(row,column)]["terrain"] = "beach"
                    elif (map[(row,column)]["elevation"] > tree_level_start) and (map[(row,column)]["elevation"] < tree_level_end):
                        map[(row,column)]["terrain"] = "forest"
                    elif (map[(row,column)]["elevation"] > snow_level):
                        map[(row,column)]["terrain"] = "snow"
                    else:
                        map[(row,column)]["terrain"] = "soil"
                else:
                    map[(row,column)]["terrain"] = "sea"

    # Generate trees surrounding rivers and lakes
    print "Generating trees...",
    for x in map:
        if map[x]["terrain"] == "river":
            paint_trees_near_river(map, (rows,columns), x)
    print "generated"

    return map

# Marks trees in the map surrounding a given river tile
# Pre:  map, size, river_tile as standard
#       tiles_near_allowance is how far we paint trees up from the water
# Post: modifies the map
# TODO: do it more efficiently by distance to water and not up-from water
def paint_trees_near_river(map, size, river_tile, tiles_near_allowance = 5):
    group = set([river_tile])
    for x in range(tiles_near_allowance):
        group = get_superneighbours(map, size, group)
    for x in group:
        if map[x]["terrain"] == "soil":
            map[x]["terrain"] = "forest"

# Returns if tile x is inside the grid
def is_inside(size, x):
    return x[0] > 0 and x[1] > 0 and x[0] < size[0] and x[1] < size[1]

# Return neighbours tiles of a tile
# Post: a set() containing neighbour tiles
def get_neighbours(map, size, tile):
    neighbours = set()
    for x in [tile[0] - 1, tile[0], tile[0] + 1]:
        for y in [tile[1] - 1, tile[1], tile[1] + 1]:
            if is_inside(size, (x,y)):
                neighbours.add((x,y))
    return neighbours

# Post: Returns a set() containing all neighbours of a group of tiles including the group
def get_superneighbours(mak, size, group):
    neighbours = set()
    for x in group:
        neighbours = neighbours.union(get_neighbours(map, size, x))
    return neighbours.difference(group)


# Post: Returns if elevation of a tile is a local maximum
def is_local_max(map, size, tile):
    maximum = map[tile]["elevation"]
    for n in get_neighbours(map, size, tile):
        if map[n]["elevation"] > maximum : return False
    return True

# Post: Returns a list conatining all mountain summits (peaks)
def get_mountain_summits(map, size, snow_level):
    summits = set()
    for x in map:
        if is_local_max(map,size, x):
            if map[x]["elevation"] >= snow_level: 
                summits.add(x)
    return summits

# Rivers are generated using backtracking algorithm. 
# Path continues until it cannot, then we go back 1 step and
# tries to find the next possibility.
# Post: Modifies the map
def generate_rivers(map, size, sea_level, snow_level, max_number_of_rivers = 10):
    summits = get_mountain_summits(map, size, snow_level) # Get mountain summits with snow
    if len(summits) > max_number_of_rivers:
        summits = random.sample(summits, max_number_of_rivers)
    k = 1
    for s in summits:
        print "Generating river " + str(k) + " of " + str(len(summits)) + "...",
        generate_rivers_r(map, size, sea_level, snow_level, s, None, set()) 
        print "generated"
        k+=1

# Recursive part of the algorithm
# Post: modifies the map
def generate_rivers_r(map, size, sea_level, snow_level, tile, parent, v):
    if map[tile]["elevation"] <= sea_level: return True
    if parent == None or map[tile]["elevation"] < map[parent]["elevation"]:
        v.add(tile)
        map[tile]["terrain"] = "river"
        non_visited_neighbours = get_neighbours(map, size, tile).difference(v)
        visited = set()
        while non_visited_neighbours:   
            m = get_min(map, size, non_visited_neighbours)
            visited.add(m)
            if generate_rivers_r(map, size, sea_level, snow_level, m, tile, v):
                return True
            non_visited_neighbours = get_neighbours(map, size, tile).difference(visited).difference(v)
    return False

# Pre: returns the tile with the lowest elevation of a given iterable of tiles
def get_min(map, size, group):
    return min(group, key=lambda x:map[x]['elevation']) 

# This function generates the height map following diamond-square algorithm 
# Pre:  size as tuple (x,y)
#       map is an empty dic[(x,y)]["elevation"] = float except of the edges
#       the elevation of the four given edges must be pre-filled in the map
# Post: Returns a map of heights as a dictionary dic[(x,y)]["elevation"] = float
# https://en.wikipedia.org/wiki/Diamond-square_algorithm
def generate_heights(map,size, origin_row,origin_column,target_row,target_column):

    middle_row = int(origin_row + (target_row - origin_row)/2.0)
    middle_column = int(origin_column + (target_column - origin_column)/2.0)

    p_row = (target_row - origin_row) / float(size[0])
    p_column = (target_column - origin_column) / float(size[1])
    p_max = (p_column + p_row) / 2.0

    k = True

    c1 = map[(origin_row,origin_column)]["elevation"]
    c2 = map[(origin_row,target_column)]["elevation"]
    c3 = map[(target_row,origin_column)]["elevation"]
    c4 = map[(target_row,target_column)]["elevation"]

    if not (middle_row,middle_column) in map:
        map[(middle_row,middle_column)] = {"elevation": p_max*random.uniform(-256,256)+(c1 + c2 + c3 + c4) / 4.0}
        k = False
    if not (origin_row,middle_column) in map:
        map[(origin_row,middle_column)] = {"elevation": p_max*random.uniform(-256,256)+(c1 + c2) / 2.0 }
        k = False
    if not (target_row,middle_column) in map:
        map[(target_row,middle_column)] = {"elevation": p_max*random.uniform(-256,256)+(c3 + c4) / 2.0 }
        k = False
    if not (middle_row,origin_column) in map:
        map[(middle_row,origin_column)] = {"elevation": p_max*random.uniform(-256,256)+(c1 + c3) / 2.0 }
        k = False
    if not (middle_row,target_column) in map:
        map[(middle_row,target_column)] = {"elevation": p_max*random.uniform(-256,256)+(c2 + c4) / 2.0 }
        k = False

    if not k:
        generate_heights(map,size,int(origin_row),int(origin_column),int(middle_row),int(middle_column))
        generate_heights(map,size,int(origin_row),int(middle_column),int(middle_row),int(target_column))
        generate_heights(map,size,int(middle_row),int(origin_column),int(target_row),int(middle_column))
        generate_heights(map,size,int(middle_row),int(middle_column),int(target_row),int(target_column))