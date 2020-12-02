import os
import pygame
import random
import sys
import datetime
import time
import json
from random import shuffle


# creating the data structure for pieces
# setting up global vars
# functions
# - create_grid
# - draw_grid
# - draw_window
# - rotating shape in main
# - setting up the main

"""
10 x 20 square grid
shapes: S, Z, I, O, J, L, T
represented in order by 0 - 6
"""

pygame.font.init()

# GLOBALS VARS
s_width = 1024
s_height = 768
block_size = 30
num_columns = 10
num_rows = 22
play_width = block_size * num_columns  # meaning 300 // 10 = 30 width per block
play_height = block_size * num_rows  # meaning 600 // 20 = 20 height per block

top_left_x = (s_width - play_width) // 2
top_left_y = s_height - play_height

game_record = {}

#From https://codemyroad.wordpress.com/2013/04/14/tetris-ai-the-near-perfect-player/
heur_height = -0.51
heur_holes = -0.36
heur_bump = -0.18
huer_line = 0.76

# SHAPE FORMATS

S = [['.....',
      '......',
      '..00..',
      '.00...',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '...0.',
      '.....']]

Z = [['.....',
      '.....',
      '.00..',
      '..00.',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '.0...',
      '.....']]

I = [['..0..',
      '..0..',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '0000.',
      '.....',
      '.....',
      '.....']]

O = [['.....',
      '.....',
      '.00..',
      '.00..',
      '.....']]

J = [['.....',
      '.0...',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..00.',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '...0.',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '.00..',
      '.....']]

L = [['.....',
      '...0.',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '..00.',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '.0...',
      '.....'],
     ['.....',
      '.00..',
      '..0..',
      '..0..',
      '.....']]

T = [['.....',
      '..0..',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '..0..',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '..0..',
      '.....']]

# For each rotation each piece can do (starting with 0),
# these are the farthest left and right the piece can go.
ai_options = [[(1, 8), (0, 8)],  # S
              [(1, 8), (1, 9)],  # Z
              [(0, 9), (2, 8)],  # I
              [(1, 9)],  # O
              [(1, 8), (0, 8), (1, 8), (1, 9)],  # J
              [(1, 8), (0, 8), (1, 8), (1, 9)],  # L
              [(1, 8), (0, 8), (1, 8), (1, 9)]]  # T

# index 0 - 6 represent shape
shapes = [S, Z, I, O, J, L, T]
shape_colors = [(0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 255, 0), (255, 165, 0), (0, 0, 255), (128, 0, 128)]
shape_names = ["S", "Z", "I", "O", "J", "L", "T"]


class Piece(object):
    def __init__(self, x, y, shape, name):
        self.index = shapes.index(shape)
        self.x = x
        self.y = y
        self.shape = shape
        self.color = shape_colors[self.index]
        self.rotation = 0
        self.name = name


def create_grid(locked_pos={}):  # *
    '''Create a 2D List to contain the color
       of each slot of the playfield
       Black is used throughout the program
       to indicate a slot is empty, Any other
       color is considered occupied.'''
    grid = [[(0, 0, 0) for _ in range(num_columns)] for _ in range(num_rows)]

    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if (j, i) in locked_pos:
                c = locked_pos[(j, i)]
                grid[i][j] = c
    return grid


# Convert from the global list of strings above
# the the actual grid spaces currently occupied by the piece
def convert_shape_format(shape):
    '''# Convert from the global list of strings to
    the the actual grid spaces currently occupied by the piece'''
    positions = []
    format = shape.shape[shape.rotation % len(shape.shape)]

    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                positions.append((shape.x + j, shape.y + i))

    for i, pos in enumerate(positions):
        positions[i] = (pos[0] - 2, pos[1] - 4)

    return positions


def valid_space(shape, grid):
    '''Use convert_shape_format() to get all grid spaces
       the piece is trying to occupy. Then check if any
       are out of bounds or occupied.
       Return False if they are or True if not'''
    accepted_pos = [[(j, i) for j in range(num_columns) if grid[i][j] == (0, 0, 0)] for i in range(num_rows)]
    accepted_pos = [j for sub in accepted_pos for j in sub]  # convert to 1D array

    formatted = convert_shape_format(shape)
    for pos in formatted:
        if pos not in accepted_pos:
            if pos[1] > -1:
                return False
    return True


def check_lost(positions):
    '''Return Ture if any part of the piece is above
       the grid'''
    for pos in positions:
        x, y = pos
        if y < 1:
            return True
    return False


def get_shape():
    '''Pick a random shape'''
    selection = random.randrange(7)
    # selection = 0
    return Piece(num_columns // 2, 0, shapes[selection], shape_names[selection])

def get_tile():
    tiles = list(range(7))
    while True:
        shuffle(tiles)
        for tile in tiles:
            yield Piece(5, 0, shapes[tile], shape_names[tile])

class PeekableQueue:
    def __init__(self, item_getter, maxpeek=50):
        self.getter = item_getter
        self.maxpeek = maxpeek
        self.b = [next(item_getter) for _ in range(maxpeek)]
        self.i = 0

    def pop(self):
        result = self.b[self.i]
        self.b[self.i] = next(self.getter)
        self.i += 1
        if self.i >= self.maxpeek:
            self.i = 0
        return result

    def peek(self, n):
        if not 0 <= n <= self.maxpeek:
            raise ValueError("bad peek argument %r" % n)
        nthruend = self.maxpeek - self.i
        if n <= nthruend:
            result = self.b[self.i : self.i + n]
        else:
            result = self.b[self.i:] + self.b[:n - nthruend]
        return result


def draw_text_middle(text, size, color, surface):
    '''Draw large text in the middle of the screen'''
    font = pygame.font.SysFont("comicsans", size, bold=True)
    label = font.render(text, True, color)

    surface.blit(label, (
        top_left_x + play_width / 2 - (label.get_width() / 2), top_left_y + play_height / 2 - (label.get_height() / 2)))


def draw_grid(surface, grid):
    '''Draw the lines horizontal and vertical that define the play space'''
    sx = top_left_x
    sy = top_left_y
    for i in range(len(grid)):
        pygame.draw.line(surface, (128, 128, 128), (sx, sy + i * block_size), (sx + play_width, sy + i * block_size))
        for j in range(len(grid[i])):
            pygame.draw.line(surface, (128, 128, 128), (sx + j * block_size, sy),
                             (sx + j * block_size, sy + play_height))

def clear_rows(grid, locked):
    inc = False
    ind = []
    for i in range(len(grid) - 1, -1, -1):
        row = grid[i]
        if (0, 0, 0) not in row:
            inc = True
            ind.append(i) # Used to indexing which row had been removed
            for j in range(len(row)):
                try:
                    del locked[(j, i)]
                except:
                    continue

    if inc:
        for key in sorted(list(locked), key = lambda x: x[1])[::-1]:
            x, y = key
            increment = 0
            for d in ind:
                if y < d:
                    increment += 1
            if ( increment ) > 0:
                newKey = (x, y + increment)
                locked[newKey] = locked.pop(key)
    return inc



def draw_next_shape(shape, surface):
    '''Draw the next shape on the right side
       of the screen'''
    font = pygame.font.SysFont('comicsans', 30)
    label = font.render('Next Shape', True, (255, 255, 255))

    sx = top_left_x + play_width + 50
    sy = top_left_y + play_height / 2 - 100
    format = shape.shape[shape.rotation % len(shape.shape)]

    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                pygame.draw.rect(surface, shape.color,
                                 (sx + j * block_size, sy + i * block_size, block_size, block_size), 0)

    surface.blit(label, (sx + 10, sy - 30))


def draw_labels(surface, height=0, gaps=0, bumpiness=0, score=0, last_score=0, height_list = [], gaps_list = []):
    '''Write all the data on the left side of the screen'''
    font = pygame.font.SysFont('comicsans', 30)
    label = font.render('Score: ' + str(score), True, (255, 255, 255))
    sx = top_left_x + play_width + 50
    sy = top_left_y + play_height / 2
    surface.blit(label, (sx + 20, sy + 60))

    label = font.render('High Score: ' + str(last_score), True, (255, 255, 255))
    sx = 1
    sy = 5
    surface.blit(label, (sx + 20, sy + 60))

    label = font.render(str(height_list), True, (255, 255, 255))
    sx = 1
    sy = 100
    surface.blit(label, (sx + 20, sy + 60))

    label = font.render('Ag Height: ' + str(height), True, (255, 255, 255))
    sx = 1
    sy = 125
    surface.blit(label, (sx + 20, sy + 60))

    label = font.render(str(gaps_list), True, (255, 255, 255))
    sx = 1
    sy = 175
    surface.blit(label, (sx + 20, sy + 60))

    label = font.render('Ag Gaps:   ' + str(gaps), True, (255, 255, 255))
    sx = 1
    sy = 200
    surface.blit(label, (sx + 20, sy + 60))

    label = font.render('Bumpiness: ' + str(bumpiness), True, (255, 255, 255))
    sx = 1
    sy = 250
    surface.blit(label, (sx + 20, sy + 60))


def clear_window(surface):
    '''Blank out the screen'''
    surface.fill((0, 0, 0))


def draw_window(surface, grid):
    '''Draw all static pieces in the playfield
       then draw the grid over them'''
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            pygame.draw.rect(surface, grid[i][j],
                             (top_left_x + j * block_size, top_left_y + i * block_size, block_size, block_size), 0)

    pygame.draw.rect(surface, (255, 0, 0), (top_left_x, top_left_y, play_width, play_height), 4)

    draw_grid(surface, grid)
    # pygame.display.update()


def get_heuristics(grid):
    '''Search each column from the top for the
       first (highest) occupied slot,
       then count any empty spaces after that.
       Bumpiness is then calculated by summing
       the absolute value of the difference
       betweeen each column and the next'''
    tops = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    gaps = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for column in range(num_columns):
        count = num_rows
        gap_count = 0
        found_top = False
        for row in range(num_rows):
            if grid[row][column] != (0, 0, 0):
                if not found_top:
                    tops[column] = count
                    found_top = True
            else:
                if found_top:
                    gap_count += 1
            count -= 1
        gaps[column] = gap_count

    ag_height = sum(tops)
    ag_gaps = sum(gaps)
    bumpiness = 0
    for i in range(len(tops) - 1):
        bumpiness += abs(tops[i] - tops[i+1])
    #print(ag_height, ag_gaps, bumpiness)
    return ag_height, ag_gaps, bumpiness, tops, gaps


def update_score(nscore):
    '''Write the high score to text doc'''
    score = max_score()
    with open('scores.txt', 'w') as f:
        if nscore > int(score):
            f.write(str(nscore))
        else:
            f.write(str(score))


def max_score():
    '''Read high score from text doc'''
    with open('scores.txt', 'r') as f:
        lines = f.readlines()
        score = lines[0].strip()
    return score


def write_log(log):
    '''Dump the play record to a text doc
       named for the date and time the
       game started'''
    filename = log["Time"] + ".txt"
    with open(filename, 'w') as f:
        f.write(json.dumps(log))


def get_user_input(current_piece, grid):
    '''Move the current piece according to the
       user's inputs then return the action to
       be recorded in the log.
       If user clicks the window close X run
       must be set to False to flag the main loop'''
    run = True
    action = None
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
            #pygame.display.quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                main_menu(win)
            if event.key == pygame.K_LEFT:
                current_piece.x -= 1
                action = "Left"
                if not (valid_space(current_piece, grid)):
                    current_piece.x += 1
                    action = None
            if event.key == pygame.K_RIGHT:
                current_piece.x += 1
                action = "Right"
                if not (valid_space(current_piece, grid)):
                    current_piece.x -= 1
                    action = None
            if event.key == pygame.K_DOWN:
                current_piece.y += 1
                if not (valid_space(current_piece, grid)):
                    current_piece.y -= 1
            if event.key == pygame.K_UP:
                current_piece.rotation += 1
                action = "Rotate"
                if not (valid_space(current_piece, grid)):
                    current_piece.rotation -= 1
                    action = None
            #print("X",current_piece.x)
    return run, action


def get_ai_input(current_piece, grid, surface, vizAI):
    #print("Cur:", current_piece.index)
    possible_actions = ai_options[current_piece.index]
    rot = 0
    best_score = -sys.maxsize - 1
    best_action = None
    for action in possible_actions:
        for move in range(action[0], action[1]+1):
            current_piece.rotation = rot
            current_piece.x = move
            current_piece.y = 0
            while valid_space(current_piece, grid):
                current_piece.y += 1
            current_piece.y -= 1
            #print("Rot", current_piece.rotation, "X", current_piece.x, "Locked at ", current_piece.y)
            formatted = convert_shape_format(current_piece)
            piece_min = 500
            piece_max = -500
            for pos in formatted:
                #print(pos)
                if pos[1] < piece_min:
                    piece_min = pos[1]
                if pos[1] > piece_max:
                    piece_max = pos[1]
                grid[pos[1]][pos[0]] = (255, 255, 255)
            line_score = 0
            for i in range(piece_min, piece_max + 1):
                if (0,0,0) not in grid[i]:
                    line_score += 1
            if vizAI:
                draw_window(surface, grid)
                pygame.display.update()
                time.sleep(0.1)
            heuristics = get_heuristics(grid)
            placement_score = heuristics[0] * heur_height + heuristics[1] * heur_holes + heuristics[2] * heur_bump
            placement_score += line_score * huer_line
            if placement_score > best_score:
                for pos in formatted:
                    grid[pos[1]][pos[0]] = (255, 0, 0)
                if vizAI:
                    draw_window(surface, grid)
                    pygame.display.update()
                    time.sleep(0.5)
                best_score = placement_score
                best_action = []
                for i in range(rot):
                    best_action.append("Rot")
                base_pos = num_columns // 2
                amount_to_move = base_pos - move
                if amount_to_move < 0:
                    amount_to_move *= -1
                    for i in range(amount_to_move):
                        best_action.append("Right")
                elif amount_to_move > 0:
                    for i in range(amount_to_move):
                        best_action.append("Left")
            for pos in formatted:
                grid[pos[1]][pos[0]] = (0, 0, 0)
            #print(heuristics)
        rot += 1

    # Reset Piece
    current_piece.rotation = 0
    current_piece.x = num_columns // 2
    current_piece.y = 0

    #print(best_action)
    return best_action


def main(win, ai_mode, vizAI, showGame):
    last_score = max_score()
    locked_positions = {}
    grid = create_grid(locked_positions)

    change_piece = False
    run = True
    piece_generator = PeekableQueue(get_tile())
    current_piece = piece_generator.pop()
    next_piece = (piece_generator.peek(1))[0]
    ai_best_action = []
    if ai_mode:
        ai_best_action = get_ai_input(current_piece, grid, win, vizAI)

    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = 0.27
    if ai_mode:
        fall_speed = 0.0
    level_time = 0
    score = 0

    game_record = {}
    date_time = datetime.datetime.now()
    dt = str(date_time.month) + "_" + str(date_time.day) + "_" + str(date_time.hour) + "_" + str(
        date_time.minute) + "_" + str(date_time.second)
    #print("Now:", dt)
    game_record["Time"] = dt
    piece_num = 0
    piece_record = {}
    game_record[str(piece_num)] = piece_record
    game_record[str(piece_num)]["Cur"] = current_piece.name
    game_record[str(piece_num)]["Next"] = next_piece.name
    #print(game_record)
    move_record = []
    height = 0
    gaps = 0
    bumpiness = 0
    height_list = []
    gaps_list = []
    ai_moves_so_far = 0
    while run:
        clear_window(win)
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        level_time += clock.get_rawtime()
        clock.tick()

        #if level_time / 1000 > 5:
        #    level_time = 0
        #    if fall_speed > 0.12:
        #        fall_speed -= 0.005

        if fall_time / 1000 > fall_speed:
            if ai_mode:
                if ai_moves_so_far < len(ai_best_action):
                    move = ai_best_action[ai_moves_so_far]
                    if move == "Rot":
                        current_piece.rotation += 1
                    elif move == "Left":
                        current_piece.x -= 1
                    elif move == "Right":
                        current_piece.x += 1
                    move_record.append(move)
                    ai_moves_so_far += 1
            fall_time = 0
            current_piece.y += 1
            if not (valid_space(current_piece, grid)) and current_piece.y > 0:
                current_piece.y -= 1
                change_piece = True

        if not ai_mode:
            run, action = get_user_input(current_piece, grid)
            if not run:
                pygame.display.quit()
            if action:
                move_record.append(action)
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    pygame.display.quit()

        shape_pos = convert_shape_format(current_piece)

        for i in range(len(shape_pos)):
            x, y = shape_pos[i]
            if y > -1:
                grid[y][x] = current_piece.color

        if change_piece:
            for pos in shape_pos:
                p = (pos[0], pos[1])
                locked_positions[p] = current_piece.color

            game_record[str(piece_num)]["Moves"] = move_record
            move_record = []

            prevScore = score
            score += clear_rows(grid, locked_positions)
            #if score != prevScore and score % 100 == 0:
                #print(score, "in", time.strftime("%H:%M:%S", time.gmtime(level_time // 1000)))
            grid = create_grid(locked_positions)
            game_record[str(piece_num)]["Score"] = score

            piece_num += 1
            current_piece = piece_generator.pop()
            next_piece = (piece_generator.peek(1))[0]
            game_record[str(piece_num)] = {}
            game_record[str(piece_num)]["Cur"] = current_piece.name
            game_record[str(piece_num)]["Next"] = next_piece.name

            height, gaps, bumpiness, height_list, gaps_list = get_heuristics(grid)
            if ai_mode:
                ai_best_action = get_ai_input(current_piece, grid, win, vizAI)
                ai_moves_so_far = 0
            #print(game_record)

            change_piece = False

            #score += baseScore * (baseScore/2) * 10
            #tops, gaps = get_tops_and_gaps(grid)
            #print("Tops:", tops)
            #print("Gaps:", gaps)

        if showGame:
            draw_window(win, grid)
            draw_next_shape(next_piece, win)
            draw_labels(win, height, gaps, bumpiness, score, last_score, height_list, gaps_list)
            pygame.display.update()

        if check_lost(locked_positions):
            print(score, "in", time.strftime("%H:%M:%S", time.gmtime(level_time // 1000)))
            write_log(game_record)
            if showGame:
                draw_text_middle("GAME OVER", 80, (192, 192, 192), win)
                pygame.display.update()
                pygame.time.delay(1500)
            run = False
            update_score(score)
            sys.exit(0) 
            main_menu(win)
            


def main_menu(win):
    inAImode = False
    visualizeAI = False
    showGame = True

    #print('Number of arguments:', len(sys.argv), 'arguments.')
    #print('Argument List:', str(sys.argv))
    if len(sys.argv) > 1 and sys.argv[1] == "ai":
        print("Accept")
        inAImode = True
        if len(sys.argv) > 2:
            if sys.argv[2] == "v":
                visualizeAI = True
            elif sys.argv[2] == "nv":
                showGame = False
    main(win, inAImode, visualizeAI, showGame)

    """"
    run = True
    while run:
        win.fill((0, 0, 0))
        draw_text_middle('Press any key to play.', 60, (255, 255, 255), win)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                main(win)
    pygame.display.quit()
    """
if len(sys.argv) > 1 and sys.argv[1] == "ai":
        if len(sys.argv) > 2:
            if sys.argv[2] == "nv":
                os.environ['SDL_VIDEODRIVER'] = 'dummy'
win = pygame.display.set_mode((s_width, s_height))
pygame.display.set_caption("Tetris")
main_menu(win)  # start game
