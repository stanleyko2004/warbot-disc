from itertools import accumulate, chain
from functools import reduce
import operator
from typing import TYPE_CHECKING
import pycuda.driver as cuda
import pycuda.autoinit  # noqa
from pycuda.compiler import SourceModule

from warbot.cogs.teamgen.combos import num_team_lists, nth_team_list

import math
import numpy as np

if TYPE_CHECKING:
    from team_gen import Configuration

TEAMSIZE = 3
MAXOWNED = 10
NUMBRAWLERS = 55 # brawler ids skip from 32 to 34 for some reason so highest id is 1 bigger

mod = SourceModule(f"""
#define TEAMSIZE {TEAMSIZE}
#define MAXOWNED {MAXOWNED}
#define NUMBRAWLERS {NUMBRAWLERS}

__constant__ unsigned int numowned[TEAMSIZE];
__constant__ unsigned long long permutations[MAXOWNED];
__constant__ unsigned long long prefix[MAXOWNED];
__constant__ unsigned long long factorial_lu[MAXOWNED];

texture<int, 3, cudaReadModeElementType> owners;

__device__
unsigned long long factorial(int n) {{
    return factorial_lu[n-1];
}}

__device__
void set_ith_combination(int pool_size, int r, int index, int *result) {{
    int n = pool_size;
    int c = 1;
    int k;
    if (r < n-r) k = r;
    else k = n-r;
    for (int i = 1; i < k+1; i++) {{
        c = c * (n - k + i) / i;
    }}
    
    int i = 0;
    while (r) {{
        c = c*r/n;
        n--;
        r--;
        while (index >= c) {{
            index -= c;
            c = c*(n-r)/n;
            n--;
        }}
        result[i] = pool_size-1-n;
        i++;
    }}
}}

__device__
void set_ith_permutation(int pool_size, int r, int index, int *result) {{
    int n = pool_size;

    unsigned long long c, q;
    if (r == n)
        c = factorial(n);
    else
        c = factorial(n) / factorial(n-r);
    
    if (r<n)
        q = index * factorial(n) / c;
    else
        q = index;
    
    int i;
    int res[MAXOWNED] = {{0}};
    for (int d = 1; d < n+1; d++) {{
        i = q % d;
        q = q / d;
        if (0 <= n - d && n - d < r)
            res[n-d] = i;
        if (q==0)
            break;
    }}

    int pool[MAXOWNED];
    for (i = 0; i < MAXOWNED; i++) {{
        pool[i] = i;
    }}

    for (i = 0; i < r; i++) {{
        result[i] = pool[res[i]];
        for (int j = res[i]; j < MAXOWNED - 1; j++) {{
            pool[j] = pool[j+1];
        }}
    }}

}}

__device__
void set_config(int num_teams, unsigned long long index, int (*results)[MAXOWNED]) {{
    set_ith_combination(numowned[0], num_teams, index/prefix[0], results[0]);
    for (int i = 1; i < TEAMSIZE; i++) {{
        set_ith_permutation(numowned[i], num_teams, (index/prefix[i]) % permutations[i], results[i]);
    }}
}}

__device__
int config_score(int num_teams, int (*indices)[MAXOWNED]) {{
    int score = 0;
    for (int i = 0; i < num_teams; i++) {{
        int brawlers[NUMBRAWLERS] = {{0}};
        for (int j = 0; j < TEAMSIZE; j++) {{
            for (int k = 0; k < NUMBRAWLERS; k++) {{
                int b = tex3D(owners, k, indices[j][i], j);
                if (b > brawlers[k])
                    brawlers[k] = b;
            }}
        }}
        for (int j = 0; j < NUMBRAWLERS; j++){{
            score += brawlers[j];
        }}
    }}
    return score;
}}

__global__
void calc_score_kernel(int num_teams, unsigned long long n, unsigned int *result, int *bscores) {{
//void calc_score_kernel(int num_teams, unsigned long long n, unsigned int *result, int *scores, int *bscores) {{
    //printf("[[%d,%d,%d],[%d,%d,%d],[%d,%d,%d]]\\n[[%d,%d,%d],[%d,%d,%d],[%d,%d,%d]]\\n[[%d,%d,%d],[%d,%d,%d],[%d,%d,%d]]\\n\\n",
    //        tex3D(owners, 0, 0, 0), tex3D(owners, 1, 0, 0), tex3D(owners, 2, 0, 0), tex3D(owners, 0, 1, 0), tex3D(owners, 1, 1, 0), tex3D(owners, 2, 1, 0), tex3D(owners, 0, 2, 0), tex3D(owners, 1, 2, 0), tex3D(owners, 2, 2, 0),
    //        tex3D(owners, 0, 0, 1), tex3D(owners, 1, 0, 1), tex3D(owners, 2, 0, 1), tex3D(owners, 0, 1, 1), tex3D(owners, 1, 1, 1), tex3D(owners, 2, 1, 1), tex3D(owners, 0, 2, 1), tex3D(owners, 1, 2, 1), tex3D(owners, 2, 2, 1),
    //        tex3D(owners, 0, 0, 2), tex3D(owners, 1, 0, 2), tex3D(owners, 2, 0, 2), tex3D(owners, 0, 1, 2), tex3D(owners, 1, 1, 2), tex3D(owners, 2, 1, 2), tex3D(owners, 0, 2, 2), tex3D(owners, 1, 2, 2), tex3D(owners, 2, 2, 2)
    //        
    //        );
    int id = threadIdx.x + blockIdx.x * blockDim.x;
    int stride = blockDim.x * gridDim.x;
    
    unsigned int score;
    unsigned int max = 0;
    unsigned int best_team;
    int indices[TEAMSIZE][MAXOWNED];
    for (unsigned long long i = id; i < n; i += stride) {{
        set_config(num_teams, i, indices);
        
        score = config_score(num_teams, indices);
        //scores[i] = score;
        if (score > max) {{
            max = score;
            best_team = i;
        }}
    }}
    
    result[id] = best_team;
    bscores[id] = max;
}}
""")

calc_score_kernel = mod.get_function('calc_score_kernel')

owners_ref = mod.get_texref('owners')
numowned_sym = mod.get_global('numowned')[0]
permutations_sym = mod.get_global('permutations')[0]
prefix_sym = mod.get_global('prefix')[0]
factorial_lu_sym = mod.get_global('factorial_lu')[0]

def find_best_teams_index(config, blockCount: int, threadsPerBlock: int) -> int:
    totalThreads = threadsPerBlock * blockCount
    
    # convert to np
    nparr = np.zeros((TEAMSIZE, MAXOWNED, NUMBRAWLERS), dtype=np.intc)
    for i, owner in enumerate(config):
        for j, player in enumerate(owner):
            for brawler in player.brawlers:
                nparr[i][j][brawler.id] = brawler.score
    
    
    # set owners array
    array = cuda.np_to_array(nparr, 'F')
    owners_ref.set_array(array)
    
    # initialize kernel params
    n = np.ulonglong(num_team_lists(*config))
    num_teams = np.intc(min(map(len, config)))
    results = np.empty(totalThreads, np.intc)
    best_scores = np.empty(totalThreads, np.intc)
    # scores = np.empty(n, np.intc)
    
    
    # precalculate stuff
    numowned = np.array([len(o) for o in config], np.uintc)
    permutations = np.array([math.perm(len(o), num_teams) for o in config], np.ulonglong)
    prefix = np.array(list(accumulate(chain((reduce(operator.mul, permutations[1:]),), permutations[1:]), operator.floordiv)), np.ulonglong)
    factorial_lu = np.array(list(accumulate(range(1,MAXOWNED+1), operator.mul)), np.ulonglong)
    
    # initialize output arrays
    results_gpu = cuda.mem_alloc(results.nbytes)
    best_scores_gpu = cuda.mem_alloc(best_scores.nbytes)
    # scores_gpu = cuda.mem_alloc(scores.nbytes)
    
    # set precalculated values
    cuda.memcpy_htod(numowned_sym, numowned)
    cuda.memcpy_htod(permutations_sym, permutations)
    cuda.memcpy_htod(prefix_sym, prefix)
    cuda.memcpy_htod(factorial_lu_sym, factorial_lu)
    
    # call the thing
    print(f'Checking {n} ways to make {num_teams} teams...')
    calc_score_kernel(num_teams, n, results_gpu, best_scores_gpu, block=(blockCount,1,1), grid=(threadsPerBlock,1))
    # calc_score_kernel(num_teams, n, results_gpu, scores_gpu, best_scores_gpu, block=(blockCount,1,1), grid=(threadsPerBlock,1))
    
    # fetch results
    cuda.memcpy_dtoh(best_scores, best_scores_gpu)
    cuda.memcpy_dtoh(results, results_gpu)
    # cuda.memcpy_dtoh(scores, scores_gpu)
    
    # print(results)
    # print(best_scores)
    # print(scores)
    
    best_id = max(range(len(results)), key=lambda i: best_scores[i])
    
    return results[best_id], best_scores[best_id]
    

def main():
    threadsPerBlock = 1
    blockCount = 4
    totalThreads = threadsPerBlock * blockCount
    
    owners = np.array([
        [[10,9,8],[7,6,5],[4,3,2]],
        [[1,3,6],[1,2,1],[1,3,5]],
        [[3,0,2],[2,5,1],[2,1,8]],
    ], np.intc)
    
    owners_ref = mod.get_texref('owners')
    
    array = cuda.np_to_array(owners, 'F')
    # print(array.get_descriptor_3d().height)
    owners_ref.set_array(array)
    
    n = np.ulonglong(num_team_lists(*owners))
    num_teams = np.intc(min(map(len, owners)))
    results = np.empty(totalThreads, np.intc)
    scores = np.empty(n, np.intc)
    
    results_gpu = cuda.mem_alloc(results.nbytes)
    scores_gpu = cuda.mem_alloc(scores.nbytes)
    
    # cuda.memcpy_htod(results_gpu, results)
    # cuda.memcpy_htod(scores_gpu, scores)
    
    numowned_sym = mod.get_global('numowned')[0]
    permutations_sym = mod.get_global('permutations')[0]
    prefix_sym = mod.get_global('prefix')[0]
    factorial_lu_sym = mod.get_global('factorial_lu')[0]
    
    numowned = np.array([len(o) for o in owners], np.uintc)
    permutations = np.array([math.perm(len(o), num_teams) for o in owners], np.ulonglong)
    prefix = np.array(list(accumulate(chain((reduce(operator.mul, permutations[1:]),), permutations[1:]), operator.floordiv)), np.ulonglong)
    factorial_lu = np.array(list(accumulate(range(1,MAXOWNED+1), operator.mul)), np.ulonglong)
    
    cuda.memcpy_htod(numowned_sym, numowned)
    cuda.memcpy_htod(permutations_sym, permutations)
    cuda.memcpy_htod(prefix_sym, prefix)
    cuda.memcpy_htod(factorial_lu_sym, factorial_lu)

    
    func = mod.get_function('calc_score_kernel')
    func(num_teams, n, results_gpu, scores_gpu, block=(blockCount,1,1), grid=(threadsPerBlock,1))
    
    output = np.empty_like(results)
    oscores = np.empty_like(scores)
    cuda.memcpy_dtoh(results, results_gpu)
    cuda.memcpy_dtoh(scores, scores_gpu)
    
    print(results)
    print(scores)
    
    print(list(nth_team_list(19, *owners)))

if __name__ == '__main__':
    main()