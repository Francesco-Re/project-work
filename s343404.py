import networkx as nx
import numpy as np
from Problem import Problem
from scipy.sparse.csgraph import shortest_path

def costCounter(P: Problem, path):
    gold_Kept = 0
    cost = P.cost((0, path[0][0]), 0)
    for i in range(0, len(path)-1):
        gold_Kept += path[i][1]
        cost += P.cost((path[i][0], path[i+1][0]), gold_Kept)
        if(path[i+1][0] == 0):
            gold_Kept = 0
    return cost


def verify_all_robbed(p: Problem, path):
    graph = p.graph
    
    
    expected_gold = {n: graph.nodes[n]['gold'] for n in graph.nodes if n != 0 and graph.nodes[n]['gold'] > 0}
    
    robbed_cities = {}
    
    for step in path:
        node, gold_collected = step
        
        if gold_collected > 0:
            if node in robbed_cities:
                print(f"City {node} has been robbed multiple times!.")
                return False
            robbed_cities[node] = gold_collected
            
    # Verifica città mancanti
    missing_cities = set(expected_gold.keys()) - set(robbed_cities.keys())
    if missing_cities:
        print(f"The following cities have not been robbed: {missing_cities}")
        return False
        
    # Verifica città inesistenti o senza oro
    extra_cities = set(robbed_cities.keys()) - set(expected_gold.keys())
    if extra_cities:
        print(f"ERRORE: Sono state derubate città che non possedevano oro o nodo 0: {extra_cities}")
        return False
        
    
    for node in expected_gold:
        if not np.isclose(expected_gold[node], robbed_cities[node]):
            print(f"Gold discrepancy in node {node}. "
                  f"Expected: {expected_gold[node]}, Got: {robbed_cities[node]}")
            return False
            
    print("Validation passed")
    return True

def reconstruct_path(predecessors, start, end):
    """Reconstructs the minimal path from the predecessor matrix."""
    if start == end:
        return [int(start)]
    
    path = []
    curr = end
    while curr != start:
        path.append(int(curr))
        curr = predecessors[start, curr]
        if curr == -9999:  # No path available
            return []
            
    path.append(int(start))
    return path[::-1]

def solution(p: Problem, getCostNotPath = False):
    graph = p.graph
    
    # Objectives identification
    nodes_gold = {n: graph.nodes[n]['gold'] for n in graph.nodes if n != 0 and graph.nodes[n]['gold'] > 0}
    if not nodes_gold:
        return [(0, 0)]

    gold_nodes = list(nodes_gold.keys())

    # Conversion of the graph into a distance matrix
    adj_matrix = nx.to_scipy_sparse_array(graph, weight='dist')
    

    dist_matrix, predecessors = shortest_path(adj_matrix, method='auto', directed=False, return_predecessors=True)

    all_distances = []
    for i in range(len(gold_nodes)):
        for j in range(i + 1, len(gold_nodes)):
            all_distances.append(dist_matrix[gold_nodes[i], gold_nodes[j]])
    
    # Spatial tollerance treshold
    if all_distances:
        distance_threshold = np.percentile(all_distances, 10) 
    else:
        distance_threshold = float('inf')

    def evaluate_route(targets):
        route = []
        start_node = int(targets[0])
        
        # Reaching the target without taking gold
        path_out = reconstruct_path(predecessors, 0, start_node)
        for step in path_out[1:]:
            if step == start_node:
                route.append((step, nodes_gold[step]))
            else:
                route.append((step, 0))
                
        # Intermediate gold stealing
        curr = start_node
        for nxt in targets[1:]:
            path_between = reconstruct_path(predecessors, curr, nxt)
            for step in path_between[1:]:
                if step == nxt:
                    route.append((step, nodes_gold[step]))
                else:
                    route.append((step, 0))
            curr = nxt
            
        # Unloading
        path_home = reconstruct_path(predecessors, curr, 0)
        for step in path_home[1:]:
            route.append((step, 0))
            
        # Cost calculation
        c = p.cost((0, route[0][0]), 0)
        gold_k = 0
        for i in range(len(route)-1):
            gold_k += route[i][1]
            c += p.cost((route[i][0], route[i+1][0]), gold_k)
            if route[i+1][0] == 0:
                gold_k = 0
                
        return c, route

    targets_list = [[n] for n in gold_nodes]
    routes_info = {tuple(t): evaluate_route(t) for t in targets_list}
    
    max_iterations = len(gold_nodes) * 5 
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        n_routes = len(targets_list)
        
        if n_routes < 2:
            break

        best_saving = 0
        best_merge_idx = None
        best_merge_targets = None
        best_merge_info = None

        for i in range(n_routes):
            for j in range(i + 1, n_routes):
                r1 = targets_list[i]
                r2 = targets_list[j]
                
                
                dist_A = dist_matrix[r1[-1], r2[0]] 
                dist_B = dist_matrix[r2[-1], r1[0]] 
                
                # Pruning
                if dist_A > distance_threshold and dist_B > distance_threshold:
                    continue 
                
                cost_separate = routes_info[tuple(r1)][0] + routes_info[tuple(r2)][0]
                
                saving_A = -1
                if dist_A <= distance_threshold:
                    merged_A = r1 + r2
                    cost_A, route_A = evaluate_route(merged_A)
                    saving_A = cost_separate - cost_A
                
                saving_B = -1
                if dist_B <= distance_threshold:
                    merged_B = r2 + r1
                    cost_B, route_B = evaluate_route(merged_B)
                    saving_B = cost_separate - cost_B
                
                if saving_A > best_saving and saving_A >= saving_B:
                    best_saving = saving_A
                    best_merge_idx = (i, j)
                    best_merge_targets = merged_A
                    best_merge_info = (cost_A, route_A)
                elif saving_B > best_saving and saving_B > saving_A:
                    best_saving = saving_B
                    best_merge_idx = (i, j)
                    best_merge_targets = merged_B
                    best_merge_info = (cost_B, route_B)
                
        if best_saving > 1e-6:
            i, j = best_merge_idx
            idx_max, idx_min = max(i, j), min(i, j)
            
            r_max_tuple = tuple(targets_list.pop(idx_max))
            r_min_tuple = tuple(targets_list.pop(idx_min))
            del routes_info[r_max_tuple]
            del routes_info[r_min_tuple]
            
            targets_list.append(best_merge_targets)
            routes_info[tuple(best_merge_targets)] = best_merge_info
        else:
            break

    # Reconstruction of the final path
    best_overall_path = []
    for t in targets_list:
        best_overall_path.extend(routes_info[tuple(t)][1])
        
    final_optimal_path = []
    for step in best_overall_path:
        if step == (0, 0):
            if not final_optimal_path or final_optimal_path[-1] != (0, 0):
                final_optimal_path.append(step)
        else:
            final_optimal_path.append(step)
            
    if not final_optimal_path or final_optimal_path[-1] != (0, 0):
        final_optimal_path.append((0, 0))
    #for testing in the problem jupyter file.
    if(getCostNotPath):
        return costCounter(p, final_optimal_path)
    print("Optimal cost found: ", costCounter(p, final_optimal_path))
    return final_optimal_path

    

if __name__ == "__main__":
    P = Problem(500, density=0.5, alpha=1, beta=1)
    print("Baseline: ", P.baseline())
    print("Is everything oke?", verify_all_robbed(P, solution(P)))