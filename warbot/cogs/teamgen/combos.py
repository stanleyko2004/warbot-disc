import math
from functools import reduce
from itertools import repeat, accumulate, chain
from more_itertools import nth_combination, nth_permutation
import operator

def nth_team_list(index: int, *owners: list):
    '''Return the nth team assignment with the ordering as team_lists'''
    num_teams = min(map(len,owners))
    perms = tuple(map(math.perm, map(len,owners), repeat(num_teams)))
    
    # (a,b,c,d) -> (bcd, cd, d)
    prefix = accumulate( # (bcd, bcd/b, bcd/bc)
        chain( # (bcd, b, c, d)
            (reduce(operator.mul, perms[1:]),), # singleton of bcd
            perms[1:]
        ),
        operator.floordiv
    )
    
    first = nth_combination(owners[0], num_teams, index // next(prefix))
    group = [first]
    for i, owner in enumerate(owners[1:], 1):
        group.append(nth_permutation(owner, num_teams, (index // next(prefix)) % perms[i])) # number of repeats is product of all #s of permutations after, cycle is # of permutations for current level
    return zip(*group)

def num_team_lists(*owners: list):
    num_teams = min(map(len, owners))
    return reduce(operator.mul, map(lambda o, r: math.perm(len(o), r), owners[1:], repeat(num_teams))) * math.comb(len(owners[0]), num_teams)
