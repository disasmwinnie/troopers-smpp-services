import time


EXIT_WIN_DELAY = 5 # [EXIT_WIN_DELAY] = s


class TicTacToe(object):

    def __init__(self):
        self.fields = []
        self.reset()

    def reset(self):
        self.fields = [['' for _ in range(3)] for _ in range(3)]

    def set_field(self, x, y, player):
        self.fields[y][x] = player

    def check_win(self, player):
        result = False
        for row in self.fields:
            if row[0] == row[1] and row[1] == row[2] and row[0] == player:
                result = True

        transposedfields = [[self.fields[0][0], self.fields[1][0],\
                self.fields[2][0]], [self.fields[0][1], self.fields[1][1],\
                self.fields[2][1]], [self.fields[0][2], self.fields[1][2],\
                self.fields[2][2]]]
        for row in transposedfields:
            if row[0] == row[1] and row[1] == row[2] and row[0] == player:
                result = True

        if self.fields[0][0] == self.fields[1][1] and self.fields[1][1] == self.fields[2][2] and self.fields[0][0] == player:
            result = True

        if self.fields[0][2] == self.fields[1][1] and self.fields[1][1] == self.fields[2][0] and self.fields[0][2] == player:
            result = True
        return result


class _LoginPlayerX(object):

    def __init__(self, gamedata):
        self._gamedata = gamedata
        self._gamedata.output_callback('Login "Player X", send "join".',  self._gamedata.tictactoe.fields)

    def next_move(self, input):
        if input.command == 'join':
            self._gamedata.playerx_nr = input.player_nr
            self._gamedata.player_nr_callback('"Player X" is number {}.'.format(self._gamedata.playerx_nr))
            self._gamedata.state = _LoginPlayerO(self._gamedata)


class _LoginPlayerO(object):

    def __init__(self, gamedata):
        self._gamedata = gamedata
        self._gamedata.output_callback('Login "Player O", send "join" or "exit".',  self._gamedata.tictactoe.fields)

    def next_move(self, input):
        if input.command == 'join':
            if input.player_nr == self._gamedata.playerx_nr:
                self._gamedata.output_callback('The number {} has already joined the game!'.format(input.player_nr), self._gamedata.tictactoe.fields)
                self._gamedata.state = _LoginPlayerO(self._gamedata)
            else:
                self._gamedata.playero_nr = input.player_nr
                self._gamedata.player_nr_callback('"Player X" is number {}, "Player O" is number {}.'.format(self._gamedata.playerx_nr, self._gamedata.playero_nr))
                self._gamedata.state = _MovePlayerX(self._gamedata)
        elif input.command == 'exit':
            self._gamedata.state = _Exit(self._gamedata)


class _MovePlayerX(object):

    def __init__(self, gamedata):
        self._gamedata = gamedata
        self._player = 'X'
        self._gamedata.output_callback('"Player {}" set field, send "x y" or "exit".'.format(self._player),  self._gamedata.tictactoe.fields)

    def next_move(self, input):
        if input.player_nr != self._gamedata.playerx_nr:
            self._gamedata.output_callback('The next move have to be done by "Player {}".'.format(self._player), self._gamedata.tictactoe.fields)
            self._gamedata.state = _MovePlayerX(self._gamedata)
        elif input.command == 'set':
            try:
                self._gamedata.tictactoe.set_field(input.x, input.y, self._player)
            except IndexError:
                self._gamedata.output_callback('Wrong input from "Player {}", "x y" value could only range between [0,2].'.format(self._player), self._gamedata.tictactoe.fields)
                self._gamedata.state = _MovePlayerX(self._gamedata)
            else:
                if self._gamedata.tictactoe.check_win(self._player):
                    self._gamedata.state = _ShowWinner(self._gamedata, self._player)
                else:
                    self._gamedata.state = _MovePlayerO(self._gamedata)
        elif input.command == 'exit':
            self._gamedata.state = _Exit(self._gamedata)


class _MovePlayerO(object):

    def __init__(self, gamedata):
        self._gamedata = gamedata
        self._player = 'O'
        self._gamedata.output_callback('"Player {}" set field, send "x y" or "exit".'.format(self._player),  self._gamedata.tictactoe.fields)

    def next_move(self, input):
        if input.player_nr != self._gamedata.playero_nr:
            self._gamedata.output_callback('The next move have to be done by "Player {}".'.format(self._player), self._gamedata.tictactoe.fields)
            self._gamedata.state = _MovePlayerO(self._gamedata)
        elif input.command == 'set':
            try:
                self._gamedata.tictactoe.set_field(input.x, input.y, self._player)
            except IndexError:
                self._gamedata.output_callback('Wrong input from "Player {}", "x y" value could only range between [0,2].'.format(self._player), self._gamedata.tictactoe.fields)
                self._gamedata.state = _MovePlayerO(self._gamedata)
            else:
                if self._gamedata.tictactoe.check_win(self._player):
                    self._gamedata.state = _ShowWinner(self._gamedata, self._player)
                else:
                    self._gamedata.state = _MovePlayerX(self._gamedata)
        elif input.command == 'exit':
            self._gamedata.state = _Exit(self._gamedata)


class _Exit(object):

    def __init__(self, gamedata):
        self._gamedata = gamedata
        self._gamedata.output_callback('Game exits.',  self._gamedata.tictactoe.fields)
        time.sleep(EXIT_WIN_DELAY)
        self._next_move()

    def _next_move(self):
        self._gamedata.prepare_new_round()
        self._gamedata.state = _LoginPlayerX(self._gamedata)


class _ShowWinner(object):

    def __init__(self, gamedata, player):
        self._gamedata = gamedata
        self._gamedata.output_callback('Congratulation, "Player {}" won the game!'.format(player),  self._gamedata.tictactoe.fields)
        time.sleep(EXIT_WIN_DELAY)
        self._next_move()

    def _next_move(self):
        self._gamedata.prepare_new_round()
        self._gamedata.state = _LoginPlayerX(self._gamedata)


class Input(object):

    def __init__(self, player_nr, command, x=0, y=0):
        self.player_nr = player_nr
        self.command = command
        self.x = x
        self.y = y


class _GameData(object):

    def __init__(self, output_callback, player_nr_callback):
        self.output_callback = output_callback
        self.player_nr_callback = player_nr_callback
        self.tictactoe = TicTacToe()
        self.playerx_nr = 0
        self.playero_nr = 0
        self.state = None

    def prepare_new_round(self):
        self.tictactoe.reset()
        self.playerx_nr = 0
        self.playero_nr = 0


class GameFlow(object):

    def __init__(self):
        self._gamedata = None

    def start_game(self, output_callback, player_nr_callback):
        self._gamedata = _GameData(output_callback, player_nr_callback)
        self._gamedata.state = _LoginPlayerX(self._gamedata)

    def next_move(self, input):
        self._gamedata.state.next_move(input)

