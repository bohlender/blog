from itertools import product, permutations
from dataclasses import dataclass
from random import randint
from z3 import *
from timeit import default_timer

# Configures the complexity of the secret
NUM_POSITIONS = 16
NUM_SYMBOLS = 6


@dataclass
class Feedback:
    """Structure for tracking the numbers of full matches and partial/symbol matches"""
    full_matches: int
    symbol_matches: int


def eval_guess(secret, guess):
    """Given the secret, computes the feedback/matches for a guess"""
    # Count full matches (position & symbol)
    guess_rest = [a for (a, b) in zip(guess, secret) if a != b]
    secret_rest = [b for (a, b) in zip(guess, secret) if a != b]
    full_match_count = len(guess) - len(guess_rest)

    # Count partial matches (symbol only)
    symbol_match_count = 0
    for symbol in guess_rest:
        try:
            secret_rest.remove(symbol)
            symbol_match_count += 1
        except ValueError:
            pass
    return Feedback(full_match_count, symbol_match_count)


def is_consistent(secret, guess, feedback):
    """Returns whether the feedback for a guess is consistent with the provided secret"""
    return feedback == eval_guess(secret, guess)


def is_consistent_with_history(secret, guesses, feedbacks):
    """Returns whether the list of feedback for a list of guesses is consistent with the provided secret"""
    for guess, feedback in zip(guesses, feedbacks):
        if not is_consistent(secret, guess, feedback):
            return False
    return True


class Game:
    """Runs the Mastermind game loop for a given secret and player implementation"""

    def __init__(self, secret, player):
        self.secret = secret
        self.player = player

    def run(self):
        guess = self.player.initial_guess()
        num_guesses = 1

        # Guess-Feedback loop until exact match is guessed
        while True:
            feedback = eval_guess(self.secret, guess)
            print("{} --> {}".format(guess, feedback))
            if feedback.full_matches == NUM_POSITIONS:
                break
            guess = self.player.make_guess(feedback)
            num_guesses += 1
        return guess, num_guesses


class Player:
    """Abstract interface for a client/player/code-breaker"""

    def initial_guess(self):
        raise NotImplementedError()

    def make_guess(self, feedback):
        raise NotImplementedError()


class ExplicitConsistentAi(Player):
    """Explicitly tracks and refines the set of secrets that are consistent with the received feedback"""

    def __init__(self):
        self.last_guess = None
        self.candidates = list(product(range(NUM_SYMBOLS), repeat=NUM_POSITIONS))

    def initial_guess(self):
        self.last_guess = self.candidates[0]
        return self.last_guess

    def make_guess(self, feedback):
        self.candidates = [c for c in self.candidates if
                           is_consistent(c, self.last_guess, feedback) and c != self.last_guess]
        return self.initial_guess()


class LazyExplicitConsistentAi(Player):
    """Lazily enumerates the secrets that are consistent with the received feedback"""

    def __init__(self):
        self.guesses = list()
        self.feedbacks = list()
        self.candidates = (c for c in product(range(NUM_SYMBOLS), repeat=NUM_POSITIONS) if
                           is_consistent_with_history(c, self.guesses, self.feedbacks))

    def initial_guess(self):
        self.guesses.append(next(self.candidates))
        return self.guesses[-1]

    def make_guess(self, feedback):
        self.feedbacks.append(feedback)
        return self.initial_guess()


class SymbolicConsistentAi(Player):
    """Builds and solves a logical characterisation of the secrets that are consistent with the received feedback"""

    def __init__(self):
        self.last_guess = None
        self.solver = SolverFor("QF_FD")

        # Possible values at secret positions, i.e. s_0_2 denotes position 0 of secret having symbol 2
        self.secret_vars = [[Bool("s_{}_{}".format(pos, sym)) for sym in range(NUM_SYMBOLS)]
                            for pos in range(NUM_POSITIONS)]

        # Exactly one symbol on each position
        for pos in range(NUM_POSITIONS):
            coeffs = [(sym, 1) for sym in self.secret_vars[pos]]
            self.solver.add(PbEq(coeffs, 1))

    def initial_guess(self):
        status = self.solver.check()

        # Extract guess from solution to constraints
        m = self.solver.model()
        guess = list()
        for pos in range(NUM_POSITIONS):
            for sym in range(NUM_SYMBOLS):
                if is_true(m.eval(self.secret_vars[pos][sym])):
                    guess.append(sym)
                    continue
        assert (len(guess) == NUM_POSITIONS)

        self.last_guess = tuple(guess)
        return self.last_guess

    def make_guess(self, feedback):
        # Full match and symbol match variables for each position
        fm = [FreshBool("fm_{0}".format(pos)) for pos in range(NUM_POSITIONS)]
        sm = [[FreshBool("sm_{0}_{1}".format(src_pos, dst_pos)) for dst_pos in range(NUM_POSITIONS)]
              for src_pos in range(NUM_POSITIONS)]

        # Possible full matches
        for pos in range(NUM_POSITIONS):
            self.solver.add(self.secret_vars[pos][self.last_guess[pos]] == fm[pos])

        # Full matches must be consistent with feedback
        fm_coeffs = [(fm_pos, 1) for fm_pos in fm]
        self.solver.add(PbEq(fm_coeffs, feedback.full_matches))

        # Possible symbol matches
        for guess_pos in range(NUM_POSITIONS):
            match_exprs = list()
            for secret_pos in range(NUM_POSITIONS):
                if guess_pos == secret_pos:
                    continue
                lhs = list()
                lhs.append(Not(fm[guess_pos]))
                lhs.append(self.secret_vars[secret_pos][self.last_guess[guess_pos]])
                lhs.append(Not(fm[secret_pos]))

                # No previous position in the guess has a symbol match with the current secret_pos
                lhs.extend([Not(sm[prev_pos][secret_pos]) for prev_pos in range(guess_pos) if secret_pos != prev_pos])
                # guess_pos has no symbol match with a previous secret_pos
                lhs.extend([Not(sm[guess_pos][prev_pos]) for prev_pos in range(secret_pos) if guess_pos != prev_pos])

                rhs = sm[guess_pos][secret_pos]
                match_exprs.append(And(lhs) == rhs)
            self.solver.add(And(match_exprs))

        # Symbol matches must be consistent with feedback
        sm_coeffs = [(sm[guess_pos][secret_pos], 1) for (guess_pos, secret_pos) in
                     permutations(range(NUM_POSITIONS), 2)]
        self.solver.add(PbEq(sm_coeffs, feedback.symbol_matches))

        return self.initial_guess()


def main(player):
    """Plays a game of Mastermind with the provided player implementation and a random secret"""
    secret = tuple(randint(0, NUM_SYMBOLS - 1) for _ in range(NUM_POSITIONS))
    game = Game(secret, player)

    print("Using {}\n{} <-- Secret".format(game.player.__class__.__name__, secret))
    start_time = default_timer()
    guess, num_guesses = game.run()
    print("Took {} guesses ({:.3}s)".format(num_guesses, default_timer() - start_time))


if __name__ == "__main__":
    # main(ExplicitConsistentAi())
    # main(LazyExplicitConsistentAi())
    main(SymbolicConsistentAi())
