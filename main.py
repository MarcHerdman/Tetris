import pygame
import random
import sys
import datetime
import json
import os


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
s_width = 800
s_height = 700
play_width = 300  # meaning 300 // 10 = 30 width per block
play_height = 600  # meaning 600 // 20 = 20 height per block
block_size = 30
num_columns = 10
num_rows = 20

top_left_x = (s_width - play_width) // 2
top_left_y = s_height - play_height

game_record = {}

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

shapes = [S, Z, I, O, J, L, T]
shape_colors = [(0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 255, 0), (255, 165, 0), (0, 0, 255), (128, 0, 128)]
shape_names = ["S", "Z", "I", "O", "J", "L", "T"]

# index 0 - 6 represent shape


class Piece(object):
    def __init__(self, x, y, shape, name):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = shape_colors[shapes.index(shape)]
        self.rotation = 0
        self.name = name


def create_grid(locked_pos={}):  # *
    grid = [[(0, 0, 0) for _ in range(10)] for _ in range(20)]

    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if (j, i) in locked_pos:
                c = locked_pos[(j, i)]
                grid[i][j] = c
    return grid


def convert_shape_format(shape):
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
    accepted_pos = [[(j, i) for j in range(10) if grid[i][j] == (0, 0, 0)] for i in range(20)]
    accepted_pos = [j for sub in accepted_pos for j in sub]  # convert to 1D array

    formatted = convert_shape_format(shape)

    for pos in formatted:
        if pos not in accepted_pos:
            if pos[1] > -1:
                return False
    return True


def check_lost(positions):
    for pos in positions:
        x, y = pos
        if y < 1:
            return True

    return False


def get_shape():
    selection = random.randrange(7)
    return Piece(5, 0, shapes[selection], shape_names[selection])

def get_tile():
    from random import shuffle
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
    font = pygame.font.SysFont("comicsans", size, bold=True)
    label = font.render(text, True, color)

    surface.blit(label, (
        top_left_x + play_width / 2 - (label.get_width() / 2), top_left_y + play_height / 2 - (label.get_height() / 2)))


def draw_grid(surface, grid):
    sx = top_left_x
    sy = top_left_y

    for i in range(len(grid)):
        pygame.draw.line(surface, (128, 128, 128), (sx, sy + i * block_size), (sx + play_width, sy + i * block_size))
        for j in range(len(grid[i])):
            pygame.draw.line(surface, (128, 128, 128), (sx + j * block_size, sy),
                             (sx + j * block_size, sy + play_height))


def clear_rows(grid, locked):
    inc = 0
    for i in range(len(grid) - 1, -1, -1):  # Loop backwards
        row = grid[i]
        if (0, 0, 0) not in row:
            inc += 1
            ind = i
            for j in range(len(row)):
                try:
                    del locked[(j, i)]
                except:
                    continue

    if inc > 0:
        for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
            x, y = key
            if y < ind:
                newKey = (x, y + inc)
                locked[newKey] = locked.pop(key)

    return inc


def draw_next_shape(shape, surface):
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


def draw_window(surface, grid, score=0, last_score=0):
    surface.fill((0, 0, 0))

    font = pygame.font.SysFont('comicsans', 60)
    label = font.render('Tetris', True, (255, 255, 255))

    surface.blit(label, (top_left_x + play_width / 2 - (label.get_width() / 2), 30))

    font = pygame.font.SysFont('comicsans', 30)
    label = font.render('Score: ' + str(score), True, (255, 255, 255))
    sx = top_left_x + play_width + 50
    sy = top_left_y + play_height / 2
    surface.blit(label, (sx + 20, sy + 60))

    label = font.render('High Score: ' + str(last_score), True, (255, 255, 255))
    sx = top_left_x - 225
    sy = top_left_y + play_height / 2

    surface.blit(label, (sx + 20, sy + 60))

    for i in range(len(grid)):
        for j in range(len(grid[i])):
            pygame.draw.rect(surface, grid[i][j],
                             (top_left_x + j * block_size, top_left_y + i * block_size, block_size, block_size), 0)

    pygame.draw.rect(surface, (255, 0, 0), (top_left_x, top_left_y, play_width, play_height), 4)

    draw_grid(surface, grid)
    # pygame.display.update()


def get_tops_and_gaps(grid):
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

    return tops, gaps


def update_score(nscore):
    score = max_score()


    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    myfile = os.path.join(THIS_FOLDER, 'scores.txt')

    with open(myfile, 'w') as f:
        if nscore > int(score):
            f.write(str(nscore))
        else:
            f.write(str(score))


def max_score():
    
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    myfile = os.path.join(THIS_FOLDER, 'scores.txt')

    with open(myfile, 'r') as f:
        lines = f.readlines()
        score = lines[0].strip()
    return score


def write_log(log):
    filename = log["Time"] + ".txt"
    with open(filename, 'w') as f:
        f.write(json.dumps(log))


def get_user_input(current_piece, grid):
    run = True
    action = None
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
            #pygame.display.quit()
        if event.type == pygame.KEYDOWN:
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
    return run, action


def get_ai_input(current_piece, grid):
    action = random.choice(["Nan", "Rot", "Left", "Right"])
    if action == "Rot":
        current_piece.rotation += 1
        if not (valid_space(current_piece, grid)):
            current_piece.rotation -= 1
    elif action == "Left":
        current_piece.x -= 1
        if not (valid_space(current_piece, grid)):
            current_piece.x += 1
    elif action == "Right":
        current_piece.x += 1
        if not (valid_space(current_piece, grid)):
            current_piece.x -= 1

def main(win, ai_mode):
    last_score = max_score()
    locked_positions = {}
    #grid = create_grid(locked_positions)

    change_piece = False
    run = True
    piece_generator = PeekableQueue(get_tile())
    current_piece = piece_generator.pop()
    next_piece = (piece_generator.peek(1))[0]
    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = 0.27
    level_time = 0
    score = 0

    game_record = {}
    date_time = datetime.datetime.now()
    dt = str(date_time.month) + "_" + str(date_time.day) + "_" + str(date_time.hour) + "_" + str(
        date_time.minute) + "_" + str(date_time.second)
    print("Now:", dt)
    game_record["Time"] = dt
    piece_num = 0
    piece_record = {}
    game_record[str(piece_num)] = piece_record
    game_record[str(piece_num)]["Cur"] = current_piece.name
    game_record[str(piece_num)]["Next"] = next_piece.name
    print(game_record)
    move_record = []

    while run:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        #level_time += clock.get_rawtime()
        clock.tick()

        #if level_time / 1000 > 5:
        #    level_time = 0
        #    if fall_speed > 0.12:
        #        fall_speed -= 0.005

        if fall_time / 1000 > fall_speed:
            if ai_mode:
                get_ai_input(current_piece, grid)
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

            score += clear_rows(grid, locked_positions) * 10
            game_record[str(piece_num)]["Score"] = score

            piece_num += 1
            current_piece = piece_generator.pop()
            next_piece = (piece_generator.peek(1))[0]
            game_record[str(piece_num)] = {}
            game_record[str(piece_num)]["Cur"] = current_piece.name
            game_record[str(piece_num)]["Next"] = next_piece.name
            #print(game_record)

            change_piece = False

            #score += baseScore * (baseScore/2) * 10
            #tops, gaps = get_tops_and_gaps(grid)
            #print("Tops:", tops)
            #print("Gaps:", gaps)

        draw_window(win, grid, score, last_score)
        draw_next_shape(next_piece, win)
        pygame.display.update()

        if check_lost(locked_positions):
            write_log(game_record)
            draw_text_middle("GAME OVER", 80, (192, 192, 192), win)
            pygame.display.update()
            pygame.time.delay(1500)
            run = False
            update_score(score)
            main_menu(win)


def main_menu(win):
    inAImode = False
    print('Number of arguments:', len(sys.argv), 'arguments.')
    print('Argument List:', str(sys.argv))
    if len(sys.argv) > 1 and sys.argv[1] == "ai":
        print("Accept")
        inAImode = True
    main(win, inAImode)

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

win = pygame.display.set_mode((s_width, s_height))
pygame.display.set_caption("Tetris")
main_menu(win)  # start game
