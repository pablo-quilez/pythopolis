# -----------------------------------------------------------------------------
# This is the main file of the project and contains the displaying logic
# -----------------------------------------------------------------------------

import pygame
import terrain

size = 100 # Size of the map grid
screen_size = [800, 600] # Window resolution

# This class pre-loads the tile images in memory to speed up displaying
# Image caching
class ImageLoader():
	def __init__(self):
		self.images = dict()
	# Loads from hard drive a tile image if it wasn't pre-cached before
	def load(self, type, size):
		if type in self.images and self.images[type].get_size()[0] == size:
			assert self.images[type].get_size()[0] == self.images[type].get_size()[1]
			return self.images[type]
		else:
			self.images[type] = pygame.image.load('tiles/' + type + '.png').convert()  
			self.images[type] = pygame.transform.scale(self.images[type], (size,size))
			return self.images[type]

# Tile class contains tile sprites
class Tile(pygame.sprite.Sprite):
	def __init__(self, x, y, type): 
		super(self.__class__, self).__init__()
		self.x = x # Tile map coordinate position
		self.y = y # Tile map coordinate position
		self.type = type # Tipe of tile based on terrain types (beach, river, sea, soil, snow, forest)
		self.image = imageLoader.load(type, max(1,screen_size[1] / size)) # Load the image resized according to the current zoom
		self.rect = self.image.get_rect()
		self.rect.x = self.x * self.image.get_size()[0] # Initial position is the grid position
		self.rect.y = self.y * self.image.get_size()[1]
	def get_x(self):
		return self.x
	def get_y(self):
		return self.y
	# Returns if a tile is inside the displaying screen
	# offset_x and offset_y are the offset to show in the map
	# For zooming the map.
	def is_inside(self, offset_x, offset_y, screen_size):
		tile_size = self.image.get_size()[0]
		tiles_on_screen = screen_size[1] / tile_size
		return self.x - offset_x >= 0 and self.y - offset_y >= 0 and self.x - offset_x < tiles_on_screen and self.y - offset_y < tiles_on_screen

# World contains a set of tiles, zooming factor and displaying position
class World():
	def __init__(self, world):
		self.world = world # The map
		self.tiles = pygame.sprite.Group()
		self.tile_size = screen_size[1] / size
		self.offset_x = 0
		self.offset_y = 0
		# Add sprites images according to its type
		for x in range(size):
			for y in range(size):
				tile = Tile(x,y, world[(x,y)]["terrain"])
				self.tiles.add(tile)

	# pygame drawing helper
	def draw(self, screen):
		draw_group = pygame.sprite.Group()
		for tile in self.tiles:
			if tile.is_inside(self.offset_x, self.offset_y, screen_size): # only draw visible tiles
				draw_group.add(tile)
		draw_group.update() # pygame function
		draw_group.draw(screen) # pygame function
	# Increase tile size in a factor of 2 until 16 pixels
	def zoom_in(self):
		self.tile_size = min(16, self.tile_size * 2)
		self.update_tile_size()
	# Reduces tile size in a factor of 2 until 1 pixel
	def zoom_out(self):
		self.tile_size = max(screen_size[1] / size, self.tile_size / 2)
		self.update_tile_size()
	# Update function called before draw to update all tiles sizes
	def update_tile_size(self):
		for tile in self.tiles:
			#tile.image = pygame.transform.scale(tile.image, (self.tile_size,self.tile_size))  
			tile.image = imageLoader.load(tile.type, self.tile_size)
			tile.rect = tile.image.get_rect()
			tile.rect.x = (tile.x - self.offset_x) * tile.image.get_size()[0]
			tile.rect.y = (tile.y - self.offset_y) * tile.image.get_size()[1]
	# Update function called before draw to update all tiles positions
	def update_tile_positions(self):
		for tile in self.tiles:
			tile.rect.x = (tile.x - self.offset_x) * tile.image.get_size()[0]
			tile.rect.y = (tile.y - self.offset_y) * tile.image.get_size()[1]

# Entry point
if __name__=="__main__":

	global imageLoader

	pygame.init() # pygame function
	screen = pygame.display.set_mode(screen_size) # Canvas
	pygame.display.set_caption("pythopolis") # Window title
	
	clock = pygame.time.Clock() # sleep rate

	imageLoader = ImageLoader() # image cache

	world = terrain.generateNewMap(size,size) # genarete the map. See terrain documentation
	world = World(world) # Create the world class

	pygame.key.set_repeat(1, 20) # Key repetions for moving the map in the display

	exit = False
	while not exit:
		# Event processing loop 
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				exit = True
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left click
				x,y = event.pos
				for sprite in world.tiles:
					if sprite.rect.collidepoint(x,y): 
						print sprite.get_x(), sprite.get_y()
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4: # Scroll down
				world.zoom_in()
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5: # Scroll up
				world.zoom_out()
			# Arrows
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_LEFT:
					world.offset_x = max(0, world.offset_x-1)
					world.update_tile_positions()
				if event.key == pygame.K_RIGHT:
					world.offset_x = min(size - screen_size[1] / world.tile_size, world.offset_x+1)
					world.update_tile_positions()
				if event.key == pygame.K_UP:
					world.offset_y = max(0, world.offset_y-1)
					world.update_tile_positions()
				if event.key == pygame.K_DOWN:
					world.offset_y = min(size - screen_size[1] / world.tile_size, world.offset_y+1)
					world.update_tile_positions()

			world.draw(screen) # Draw screen

		clock.tick(2) # 2 images per second
		pygame.display.flip()  # pygame function

	pygame.quit()
