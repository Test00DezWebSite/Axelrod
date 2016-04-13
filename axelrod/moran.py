# -*- coding: utf-8 -*-
from collections import Counter
import random

import numpy as np

from .deterministic_cache import DeterministicCache
from .match import Match
from .player import Player


def fitness_proportionate_selection(scores):
    """Randomly selects an individual proportionally to score."""
    csums = np.cumsum(scores)
    total = csums[-1]
    r = random.random() * total

    for i, x in enumerate(csums):
        if x >= r:
            return i

class MoranProcess(object):
    def __init__(self, players, turns=100, noise=0):
        self.turns = turns
        self.noise = noise
        self.players = list(players) # initial population
        self.winner = None
        self.populations = []
        self.populations.append(self.population_distribution())
        self.score_history = []

    @property
    def _stochastic(self):
        """
        A boolean to show whether a match between two players would be
        stochastic
        """
        if self.noise:
            return True
        else:
            return any(p.classifier['stochastic'] for p in self.players)

    def __next__(self):
        """Iterate the population:
        - play the round's matches
        - chooses a player proportionally to fitness (total score) to reproduce
        - choose a player at random to be replaced
        - update the population
        """
        # Check the exit condition, that all players are of the same type.
        population = self.populations[-1]
        classes = set(p.__class__ for p in self.players)
        if len(classes) == 1:
            self.winner = str(self.players[0])
            raise StopIteration
        scores = self._play_next_round()
        # Update the population
        # Fitness proportionate selection
        j = fitness_proportionate_selection(scores)
        # Randomly remove a strategy
        i = random.randrange(0, len(self.players))
        # Replace player i with clone of player j
        self.players[i] = self.players[j].clone()
        self.populations.append(self.population_distribution())

    def _play_next_round(self):
        """Plays the next round of the process. Every player is paired up
        against every other player and the total scores are recorded."""
        N = len(self.players)
        scores = [0] * N
        for i in range(N):
            for j in range(i + 1, N):
                player1 = self.players[i]
                player2 = self.players[j]
                player1.reset()
                player2.reset()
                match = Match((player1, player2), self.turns, noise=self.noise)
                match.play()
                match_scores = np.sum(match.scores(), axis=0) / float(self.turns)
                scores[i] += match_scores[0]
                scores[j] += match_scores[1]
        self.score_history.append(scores)
        return scores

    def population_distribution(self):
        """Returns the population distribution of the last iteration."""
        player_names = [str(player) for player in self.players]
        counter = Counter(player_names)
        return counter

    next = __next__  # Python 2

    def __iter__(self):
        return self

    def reset(self):
        """Reset the process to replay."""
        self.winner = None
        self.populations = [self.populations[0]]
        self.score_history = []

    def play(self):
        """Play the process out to completion."""
        while True: # O_o
            try:
                self.__next__()
            except StopIteration:
                break

    def __len__(self):
        return len(self.populations)