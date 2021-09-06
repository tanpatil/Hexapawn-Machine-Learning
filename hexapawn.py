import random
import sys
from copy import deepcopy
import pickle
import os

WRAP=55
WHITE=1
BLACK=-1
EMPTY=0

class HexpawnException(Exception):
    pass

class IllegalCoordinate(HexpawnException):
    pass

class IllegalMove(HexpawnException):
    pass

fh=open("MovesetPermutations.txt","r")
MoveSet=fh.readlines()
InitialMoveSet=MoveSet[0:19]
InitialMoveSetVar=''
for permutation in InitialMoveSet:
    InitialMoveSetVar+=permutation.rstrip(',\n')+','
InitialMoveSetVar=InitialMoveSetVar.rstrip(',')
InitialMoves=tuple(eval(InitialMoveSetVar))
MoveSetConfigs=MoveSet[19:38]
ConfigMoveSetVar=''
for permutation in MoveSetConfigs:
    ConfigMoveSetVar+=permutation.rstrip(',\n')+','
ConfigMoveSetVar=ConfigMoveSetVar.rstrip(',')
ConfigMoveSet=tuple(eval(ConfigMoveSetVar))
fh.close()

initialWinsLosses={"Wins":0,"Losses":0}

try:
    fh=open("Scores.dat","rb+")
except FileNotFoundError:
    f=open("Scores.dat","wb")
    pickle.dump(initialWinsLosses,f)
    f.close()
    fh=open("Scores.dat","rb+")

WinLoose=pickle.load(fh)
fh.close()

def update(WinOrLoose):
    f=open("Scores.dat","rb+")
    f1=open("temp.dat","wb")
    data=pickle.load(f)
    if WinOrLoose=='Win':
        newvar=data["Wins"]
        data['Wins']=newvar+1
        pickle.dump(data,f1)
        f.close()
        f1.close()
    elif WinOrLoose=='Loose':
        newvar=data["Losses"]
        data['Losses']=newvar+1
        pickle.dump(data,f1)
        f.close()
        f1.close()
    os.remove("Scores.dat")
    os.rename("temp.dat","Scores.dat")
 
class Game:
    _initial_moves = InitialMoves

    _initial_board = [
        BLACK, BLACK, BLACK,
        EMPTY, EMPTY, EMPTY,
        WHITE, WHITE, WHITE
    ]

    def __init__(self):
        self.wins = WinLoose['Wins']
        self.losses = WinLoose['Losses']
        self.winner = None
        self.message = None
        self.board = deepcopy(self._initial_board)
        self.moves = deepcopy(self._initial_moves)
        self.x = self.y = 0
        self.configs = ConfigMoveSet

    #Show state of board after every move
    def reset(self):
        self.board = deepcopy(self._initial_board)
        self.winner = None
        self.message = None

    #Uses Machine Learning to remove losing strategies
    def game_over(self, winner, message=None):
        
        # If the player won
        if winner is WHITE:
            self.wins += 1
            update("Win")

            if message:
                self.message = message
            else:
                self.message = 'You win.'

            # Remove losing strategy from moves list
            self.moves[self.x][self.y] = 0

        # If machine won
        elif winner is BLACK:

            self.losses += 1
            update("Loose")

            if message:
                self.message += '\n' + message
            else:
                self.message += '\nI win.'


        # Winner should only ever be player or machine
        else:
            raise HexpawnException

        self.winner = winner

    def overview(self):
        return 'Games lost = {}, Games won = {}, Total Games = {}.'.format(
            self.losses, self.wins, self.losses + self.wins
        )


#Printing Gameboard
def fnr(x):

    rval = {
        1: 3, 3: 1,
        4: 6, 6: 4,
        7: 9, 9: 7
    }
    return rval.get(x, x)

# Player Move
def white_move(m1, m2, game):
    
    assert game.winner is None
    game.message = None

    # Ensure move is on the board
    if m1 not in range(1, 10) or m2 not in range(1, 10):
        raise IllegalCoordinate

    # Ensure player is moving their own piece
    if game.board[m1 - 1] is not WHITE:
        raise IllegalCoordinate

    # Ensure player isn't moving onto their own piece
    if game.board[m2 - 1] is WHITE:
        raise IllegalMove

    # Ensure if moving diagonally its onto an opponents piece
    if m2 - m1 != -3 and game.board[m2 - 1] is not BLACK:
        raise IllegalMove

    # Ensure the user is not trying to move left, right, or down
    if m2 > m1:
        raise IllegalMove

    # Make sure if moving forward, destination is unoccupied
    if m2 - m1 == -3 and game.board[m2 - 1] is not EMPTY:
        raise IllegalMove

    # Enusre if the player is moving forward it is within allowable range
    if m2 - m1 < -4:
        raise IllegalMove

    # Ensure user isn't moving from bottom left of board to top right
    if m1 == 7 and m2 == 3:
        raise IllegalMove

    # Perform move
    game.board[m1 - 1] = EMPTY
    game.board[m2 - 1] = WHITE

    # Check if any player pieces have reached the far row
    if WHITE in (game.board[0], game.board[1], game.board[2]):
        game.game_over(WHITE)
        return

    # Check if all of machine's pieces have been captured
    if BLACK not in game.board:
        game.game_over(WHITE)
        return

    # Check if machine can move forward
    for i in range(6):
        if game.board[i] is BLACK:
            if game.board[i + 3] is EMPTY:
                return

    # Check if machine can capture a piece
    for i in (0, 1, 3, 4):
        if game.board[i] is BLACK and game.board[i + 4] is WHITE:
            return

    for i in (1, 2, 4, 5):
        if game.board[i] is BLACK and game.board[i + 2] is WHITE:
            return

    # If machine has no valid moves player wins
    game.game_over(WHITE)

#Machine Move
def black_move(game):

    assert game.winner is None
    game.message = None
    strategies = list()
    r = None

    for game.x in range(19):
        current_config = list(game.configs[game.x])
        mirrored_config = list(current_config)
        mirrored_config[0] = current_config[2]
        mirrored_config[3] = current_config[5]
        mirrored_config[6] = current_config[8]
        mirrored_config[2] = current_config[0]
        mirrored_config[5] = current_config[3]
        mirrored_config[8] = current_config[6]

        if game.board == current_config:
            r = False
            break
        elif game.board == mirrored_config:
            r = True
            break

    assert r is not None

    # Uses previously played data to implement move
    for i in range(4):
        if game.moves[game.x][i] != 0:
            strategies.append(i)

    # If a move cannot be found, machine loses
    if not strategies:
        game.game_over(WHITE, message='I lose.')
        return

    # Get machine's move
    game.y = random.choice(strategies)
    move = divmod(game.moves[game.x][game.y], 10)
    if r:
        move = (fnr(move[0]), fnr(move[1]))

    # Perform move
    game.board[move[0] - 1] = EMPTY
    game.board[move[1] - 1] = BLACK
    game.message = 'I move from {} to {}'.format(move[0], move[1])

    # Check if any machine pieces have reached end of board
    if BLACK in (game.board[6], game.board[7], game.board[8]):
        game.game_over(BLACK)
        return

    # Check if all of player's pieces have been captured
    if WHITE not in game.board:
        game.game_over(BLACK)
        return

    # Check if player can move forward
    for i in range(3, 9):
        if game.board[i] is WHITE:
            if game.board[i - 3] is EMPTY:
                return

    # Check if player can capture a piece
    for i in (4, 5, 7, 8):
        if game.board[i] is WHITE and game.board[i - 4] is BLACK:
            return

    for i in (3, 4, 6, 7):
        if game.board[i] is WHITE and game.board[i - 2] is BLACK:
            return
    game.game_over(BLACK, message='Human Loses, Machine Wins.')

from tkinter import *

COLOUR1 = 'black',
COLOUR2 = 'white',
TILE_SIZE = 6

#Start Game
def main():
    game = Game()
    gui = GUI(game)
    gui.mainloop()

class GUI(Tk):
    def __init__(self, game):

        self.game = game
        self.m1 = None

        # Set up Tkinter
        Tk.__init__(self)
        self.title("Hexapawn")
        self.resizable(0, 0)
        self.wpawn = PhotoImage(file='white.gif')
        self.bpawn = PhotoImage(file='black.gif')
        self.empty = PhotoImage(file='empty.gif')
        self.tk.call('wm', 'iconphoto', self._w, self.wpawn)

        self.notice = StringVar()
        Label(
            self, textvariable=self.notice, width=45, height=2,
            font="Sans 12 bold"
        ).pack(pady=10)

        # Create game board
        self.tiles = list()
        self.tile_frame = Frame()
        self.tile_frame.pack(padx=60, pady=(0, 60))
        self.new_game_button = Button(
            self, text='NEW GAME', command=self.enable
        )
        self.new_game_button.pack_forget()

        # Create game board tiles
        color = COLOUR1
        i = 0
        for row in range(3):
            for col in range(3):
                tile = Button(self.tile_frame)
                tile.config(
                    relief=FLAT,
                    bg=color,
                    activebackground=color,
                    command=lambda i=i: self.player_selected(i)
                )
                tile.grid(column=col, row=row)
                self.tiles.append(tile)
                color = COLOUR1 if color == COLOUR2 else COLOUR2
                i += 1
        self.set_pieces()

    #Movement of Pawns
    def set_pieces(self):
        for i in range(9):
            piece = self.game.board[i]
            if piece is BLACK:
                self.tiles[i].config(image=self.bpawn)
                self.tiles[i].image = self.wpawn

            elif piece is WHITE:
                self.tiles[i].config(image=self.wpawn)
                self.tiles[i].image = self.bpawn

            else:
                self.tiles[i].config(image=self.empty)
                self.tiles[i].image = self.empty

    #Determines tile clicked on
    def player_selected(self, position):
        if self.m1 is not None:
            self.move(self.m1, position)
            self.m1 = None
        else:
            if self.game.board[position] is WHITE:
                self.m1 = position

    #Calculates Moves (Whether Illegeal or Not)
    def move(self, m1, m2):
        try:
            white_move(m1 + 1, m2 + 1, self.game)
        except IllegalMove:
            self.notice.set('Illegal move.')
            return
        except IllegalCoordinate:
            self.notice.set('Illegal coordinates.')
            return

        self.set_pieces()
        if self.game.winner:
            self.notice.set(self.game.message.replace('\n', '-- '))
            self.notice.set(
                '{}\n{}'.format(self.notice.get(), self.game.overview()))
            self.disable()
            return

        black_move(self.game)
        self.set_pieces()
        self.notice.set(self.game.message.replace('\n', '-- '))

        if self.game.winner:
            self.notice.set(
                '{}\n{}'.format(self.notice.get(), self.game.overview()))
            self.disable()
            return

    #Disables gameboard interaction
    def disable(self):
        for tile in self.tiles:
            tile.config(state='disabled')
        self.new_game_button.pack(pady=16)
        self.tile_frame.pack(padx=60, pady=0)

    #Disables gameboard interaction
    def enable(self):
        for tile in self.tiles:
            tile.config(state='normal')
        self.game.reset()
        self.set_pieces()
        self.new_game_button.pack_forget()
        self.tile_frame.pack(padx=60, pady=(0, 60))

#Start game
if __name__ == "__main__":
    main()
