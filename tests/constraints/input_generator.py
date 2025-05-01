import random
from constraint import Problem

class ConstrainedRandomInput:
    def __init__(self):
        self.problem = Problem()
        self.problem.addVariable("a", [0, 1])
        self.problem.addVariable("b", [0, 1])

    def get_sample(self):
        solution = self.problem.getSolutions()
        return random.choice(solution)
