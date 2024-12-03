import pygame
import random
import math
import copy
from pygame.locals import *

# Constants
BWIDTH = 20
BHEIGHT = 20
MESH_WIDTH = 1
BOARD_HEIGHT = 7
BOARD_UP_MARGIN = 40
BOARD_MARGIN = 2

WHITE = (255,255,255)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,80,255)
ORANGE = (255,69,0)
GOLD = (255,125,0)
PURPLE = (128,0,128)
CYAN = (0,255,255)
BLACK = (0,0,0)

MOVE_TICK = 1000
TIMER_MOVE_EVENT = USEREVENT+1
GAME_SPEEDUP_RATIO = 1.5
SCORE_LEVEL = 2000
SCORE_LEVEL_RATIO = 2
POINT_VALUE = 100
POINT_MARGIN = 10
FONT_SIZE = 25

class Block:
    def __init__(self,shape,x,y,screen,color,rotate_en):
        self.shape = []
        for sh in shape:
            bx = sh[0]*BWIDTH + x
            by = sh[1]*BHEIGHT + y
            block = pygame.Rect(bx,by,BWIDTH,BHEIGHT)
            self.shape.append(block)
        self.rotate_en = rotate_en
        self.x = x
        self.y = y
        self.diffx = 0
        self.diffy = 0
        self.screen = screen
        self.color = color
        self.diff_rotation = 0

    def draw(self):
        for bl in self.shape:
            pygame.draw.rect(self.screen,self.color,bl)
            pygame.draw.rect(self.screen,BLACK,bl,MESH_WIDTH)

    def get_rotated(self,x,y):
        rads = self.diff_rotation * (math.pi / 180.0)
        newx = x*math.cos(rads) - y*math.sin(rads)
        newy = y*math.cos(rads) + x*math.sin(rads)
        return (newx,newy)

    def move(self,x,y):
        self.diffx += x
        self.diffy += y
        self._update()

    def remove_blocks(self,y):
        new_shape = []
        for shape_i in range(len(self.shape)):
            tmp_shape = self.shape[shape_i]
            if tmp_shape.y < y:
                new_shape.append(tmp_shape)
                tmp_shape.move_ip(0,BHEIGHT)
            elif tmp_shape.y > y:
                new_shape.append(tmp_shape)
        self.shape = new_shape

    def has_blocks(self):
        return True if len(self.shape) > 0 else False

    def rotate(self):
        if self.rotate_en:
            self.diff_rotation = 90
            self._update()

    def _update(self):
        for bl in self.shape:
            origX = (bl.x - self.x)/BWIDTH
            origY = (bl.y - self.y)/BHEIGHT
            rx,ry = self.get_rotated(origX,origY)
            newX = rx*BWIDTH + self.x + self.diffx
            newY = ry*BHEIGHT + self.y + self.diffy
            newPosX = newX - bl.x
            newPosY = newY - bl.y
            bl.move_ip(newPosX,newPosY)
        self.x += self.diffx
        self.y += self.diffy
        self.diffx = 0
        self.diffy = 0
        self.diff_rotation = 0

    def backup(self):
        self.shape_copy = copy.deepcopy(self.shape)
        self.x_copy = self.x
        self.y_copy = self.y
        self.rotation_copy = self.diff_rotation

    def restore(self):
        self.shape = self.shape_copy
        self.x = self.x_copy
        self.y = self.y_copy
        self.diff_rotation = self.rotation_copy

    def check_collision(self,rect_list):
        for blk in rect_list:
            if len(blk.collidelistall(self.shape)):
                return True
        return False

class Tetris:
    def __init__(self,bx,by):
        
        self.resx = bx*BWIDTH+2*BOARD_HEIGHT+BOARD_MARGIN
        self.resy = by*BHEIGHT+2*BOARD_HEIGHT+BOARD_MARGIN
        self.board_up = pygame.Rect(0,BOARD_UP_MARGIN,self.resx,BOARD_HEIGHT)
        self.board_down = pygame.Rect(0,self.resy-BOARD_HEIGHT,self.resx,BOARD_HEIGHT)
        self.board_left = pygame.Rect(0,BOARD_UP_MARGIN,BOARD_HEIGHT,self.resy)
        self.board_right = pygame.Rect(self.resx-BOARD_HEIGHT,BOARD_UP_MARGIN,BOARD_HEIGHT,self.resy)
        self.blk_list = []
        self.start_x = math.ceil(self.resx/2.0)
        self.start_y = BOARD_UP_MARGIN + BOARD_HEIGHT + BOARD_MARGIN
        self.block_data = (
            ([[0,0],[1,0],[2,0],[3,0]],RED,True),
            ([[0,0],[1,0],[0,1],[-1,1]],GREEN,True),
            ([[0,0],[1,0],[2,0],[2,1]],BLUE,True),
            ([[0,0],[0,1],[1,0],[1,1]],ORANGE,False),
            ([[-1,0],[0,0],[0,1],[1,1]],GOLD,True),
            ([[0,0],[1,0],[2,0],[1,1]],PURPLE,True),
            ([[0,0],[1,0],[2,0],[0,1]],CYAN,True),
        )
        self.blocks_in_line = bx if bx%2 == 0 else bx-1
        self.blocks_in_pile = by
        self.score = 0
        self.speed = 1
        self.score_level = SCORE_LEVEL
        self.next_block_data = self.get_random_block_data()

    def run(self):
        pygame.init()
        pygame.font.init()
        self.myfont = pygame.font.SysFont(pygame.font.get_default_font(),FONT_SIZE)
        self.screen = pygame.display.set_mode((self.resx,self.resy))
        pygame.display.set_caption("Tetris")
        self.set_move_timer()
        self.done = False
        self.game_over = False
        self.new_block = True
        self.print_status_line()
        
        while not(self.done) and not(self.game_over):
            self.get_block()
            self.game_logic()
            self.draw_game()
            
        if self.game_over:
            self.print_game_over()
        pygame.font.quit()
        pygame.display.quit()

    def get_random_block_data(self):
        return random.choice(self.block_data)

    def apply_action(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.unicode == 'q'):
                self.done = True
            pygame.key.set_repeat(150, 50)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_DOWN:
                    self.active_block.move(0,BHEIGHT)
                if ev.key == pygame.K_LEFT:
                    self.active_block.move(-BWIDTH,0)
                if ev.key == pygame.K_RIGHT:
                    self.active_block.move(BWIDTH,0)
                if ev.key == pygame.K_UP:
                    self.active_block.rotate()
                if ev.key == pygame.K_p:
                    self.pause()
            if ev.type == TIMER_MOVE_EVENT:
                self.active_block.move(0,BHEIGHT)

    def set_move_timer(self):
        speed = math.floor(MOVE_TICK / self.speed)
        speed = max(1,speed)
        pygame.time.set_timer(TIMER_MOVE_EVENT,speed)

    def pause(self):
        self.print_center(["PAUSE","Press \"p\" to continue"])
        pygame.display.flip()
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_p:
                    return

    def print_center(self,str_list):
        max_xsize = max([tmp[0] for tmp in map(self.myfont.size,str_list)])
        self.print_text(str_list,self.resx/2-max_xsize/2,self.resy/2)

    def print_text(self,str_lst,x,y):
        prev_y = 0
        for string in str_lst:
            size_x,size_y = self.myfont.size(string)
            txt_surf = self.myfont.render(string,False,WHITE)
            self.screen.blit(txt_surf,(x,y+prev_y))
            prev_y += size_y

    def print_status_line(self):
        string = ["SCORE: {0}   SPEED: {1}x".format(self.score,self.speed)]
        self.print_text(string,POINT_MARGIN,POINT_MARGIN)

    def print_game_over(self):
        self.print_center(["Game Over","Press \"q\" to exit"])
        pygame.display.flip()
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.unicode == 'q'):
                    return

    def game_logic(self):
        self.active_block.backup()
        self.apply_action()
        down_board = self.active_block.check_collision([self.board_down])
        any_border = self.active_block.check_collision([self.board_left,self.board_up,self.board_right])
        block_any = self.block_colides()
        if down_board or any_border or block_any:
            self.active_block.restore()
        self.active_block.backup()
        self.active_block.move(0,BHEIGHT)
        can_move_down = not self.block_colides()
        self.active_block.restore()
        if not can_move_down and (self.start_x == self.active_block.x and self.start_y == self.active_block.y):
            self.game_over = True
        if down_board or not can_move_down:
            self.new_block = True
            self.detect_line()

    def block_colides(self):
        for blk in self.blk_list:
            if blk == self.active_block:
                continue
            if(blk.check_collision(self.active_block.shape)):
                return True
        return False

    def detect_line(self):
        for shape_block in self.active_block.shape:
            tmp_y = shape_block.y
            tmp_cnt = self.get_blocks_in_line(tmp_y)
            if tmp_cnt != self.blocks_in_line:
                continue
            self.remove_line(tmp_y)
            self.score += self.blocks_in_line * POINT_VALUE
            if self.score > self.score_level:
                self.score_level *= SCORE_LEVEL_RATIO
                self.speed *= GAME_SPEEDUP_RATIO
                self.set_move_timer()

    def remove_line(self,y):
        for block in self.blk_list:
            block.remove_blocks(y)
        self.blk_list = [blk for blk in self.blk_list if blk.has_blocks()]

    def get_blocks_in_line(self,y):
        tmp_cnt = 0
        for block in self.blk_list:
            for shape_block in block.shape:
                tmp_cnt += (1 if y == shape_block.y else 0)
        return tmp_cnt

    def draw_board(self):
        pygame.draw.rect(self.screen, WHITE, self.board_up)
        pygame.draw.rect(self.screen, WHITE, self.board_down)
        pygame.draw.rect(self.screen, WHITE, self.board_left)
        pygame.draw.rect(self.screen, WHITE, self.board_right)
        
        grid_color = (50, 50, 50)
        x = self.board_left[0] + 7
        while x <= self.resx:
            pygame.draw.line(self.screen, grid_color, (x, BOARD_UP_MARGIN), (x, self.resy - BOARD_HEIGHT))
            x += BWIDTH
        y = BOARD_UP_MARGIN + 8
        while y <= self.resy - BOARD_HEIGHT:
            pygame.draw.line(self.screen, grid_color, (0, y), (self.resx, y))
            y += BHEIGHT
        self.print_status_line()

    def get_block(self):
        if self.new_block:
            data = self.next_block_data  
            self.active_block = Block(data[0], self.start_x, self.start_y, self.screen, data[1], data[2])
            self.blk_list.append(self.active_block)
            self.next_block_data = self.get_random_block_data() 
            self.new_block = False

    def draw_next_block_preview(self):
        preview_x = self.resx - 6 * BWIDTH + 50
        preview_y = 2 * BOARD_MARGIN
                
        shape, color, _ = self.next_block_data
        for sh in shape:
            bx = preview_x + sh[0] * BWIDTH
            by = preview_y + sh[1] * BHEIGHT
            block = pygame.Rect(bx, by, BWIDTH, BHEIGHT)
            pygame.draw.rect(self.screen, color, block)
            pygame.draw.rect(self.screen, BLACK, block, MESH_WIDTH)

    def draw_game(self):
        self.screen.fill(BLACK)
        self.draw_board()
        self.draw_next_block_preview()
        for blk in self.blk_list:
            blk.draw()
        pygame.display.flip()

if __name__ == "__main__":
    Tetris(16,30).run()
