from Problem import Problem
import numpy as np
import networkx as nx

def solution(p:Problem):
    #Policy: search for the farthest city, reach it without stealing and get back stealing at each city. If near the base there are other cities nextHop to the base go there too. While backtracking if there are multiple paths not nextHop to
    # the base don't steal and go back 

    """Step 1: calculate the navigation structure. The structures to calculate are: 
        -Table, ordered by the number of hops which contains:
            -target, target node
            -nextHop, nextHop hop needed to get to the base node
            -numHops, number of hops needed to get there
            -distance, actual distance to get to a specific city
        -robbedCities, resetted every time the base is reached. Needed for updating the table. Contains all nodes robbed per run
        -state, which is the tuple containing:
            -current: current position
            -gold: gold stolen
    """
    cost = 0
    path = []
    table = createNavTable(p.graph)
    robbedCities = set()
    state = {"current": 0, "gold": 0}
    graph = p.graph.copy()

    while len(table) != 0:
        """
        Step 2: Loop started (ends when all nodes are visited, ergo table is empty), starting policy from base:
            -"deposit" gold owned at the base
            -check the table and look for the city with the highest ammount of hops needed (basically take the last of the table)
            -reach the city without stealing any gold, 
            -steal target gold
        """
        
        state["gold"] = 0

        state["current"] = table[len(table)-1][0]
        
        returnPath = updatePath(table, state["current"], path)
        cost+= table[len(table)-1][3]
        state["gold"] += graph.nodes[state["current"]]['gold']
        graph.nodes[state["current"]]['gold'] = 0

        state["current"] = table[len(table)-1][1]

        while state["current"] != 0:
            robbedCities.add(state["current"])
            """
            Step 3: Return started, returning policy:
                -backtrack with following policy at each nodes:
                    -if pathes - robbedNearbyCities (cities with 0 gold and not the base) == 1 steal and backtrack (only backtrack is "possible")
                    -else if base is near and a nearby node is near to the base (so both linked to base and with each other) steal and go to that city
                    -else don't steal and backtrack (another future path is present, will steal in the future)
            """
            robbedNearbyCities = [x for x in graph.neighbors(state["current"]) if x != 0 and graph.nodes[x]['gold'] == 0].__len__()
            possiblePaths = len(graph.neighbors(state["current"])) - robbedNearbyCities


            nextHop = returnPath[len(returnPath)-1][0]
            returnPath.pop()
            
            
            if possiblePaths == 1:
                state["gold"] += graph.nodes[state["current"]]['gold']
                path.append((state["current"], graph.nodes[state["current"]]['gold']))
                graph.nodes[state["current"]]['gold'] = 0
                robbedCities.add(state["current"])
                cost = p.cost([state["current"], nextHop], cost)
                state["current"] = nextHop
                continue
            if nextHop == 0 and possiblePaths > 1:
                for x in graph.neighbors(state["current"]):
                    if 0 in graph.neighbors(x):
                        state["gold"] += graph.nodes[state["current"]]['gold']
                        path.append((state["current"], graph.nodes[state["current"]]['gold']))
                        graph.nodes[state["current"]]['gold'] = 0
                        robbedCities.add(state["current"])
                        cost = p.cost([state["current"], nextHop], cost)
                        state["current"] = nextHop
                        continue
            
            path.append((state["current"], 0))
            cost = p.cost([state["current"], nextHop], cost)
            state["current"] = nextHop
            
        """
        Step 4: Return, update NavTable:
            -scroll through the table, if the target is in the path of the stolen cities remove them
            example: in this run 2, 3 and 4 have been robbed -> remove the rows which have cities 2, 3 and 4 as target from the NavTable
        """
        
        table = updateNavTable(table, robbedCities)
        robbedCities.clear()

    return path, cost


def createNavTable(g: nx.Graph):
    table = []
    usedNodes = np.zeros(g.number_of_nodes)

    """
    Step 1.1: Table init. From the base node get the list of nodes linked to it. For each node add it to the table with hops of the node equal to 1 and the distance from the base
    """
    usedNodes[0] = 1
    for x in g.neighbors(0):
        table.append((x, 0, 1, nx.path_weight(g, [0, x], weight='dist')))
        usedNodes[x] = 1 

    """
    Step 1.2: Loop start. The following steps are:
        -from a node get the list of nodes linked to it. For each node:
            -if it is already used just skip it (for now, might be a point to optimize distance)
            -if the node is not used add it to the table with hops of the node (hops of the current row + 1)
    """
    
    #value that indicates the last row used
    rowEval = 0
    while(sum(usedNodes) != g.number_of_nodes):
        (node, _, numHops, distance) = table[rowEval]
        rowEval += 1
        for x in g.neighbors(node):
            if usedNodes[x]:
                continue
            table.append((x, node, numHops+1, distance + nx.path_weight(g, [node, x], weight='dist')))
            usedNodes[x] = 1 

    return table


    """
    Updates the table removing all Navigation routes to cities already robbed
    """
def updateNavTable(table: list[tuple[int, int, int]], robbedCities: set[int]):
    return [row for row in table if row[0] not in robbedCities]

        
def updatePath(table: list[tuple[int, int, int]], current, path: list[tuple[int, int]]):
    c = current
    revPath = []
    for i in range (len(table)-1, -1, -1):
        if table[i][0] == c:
            revPath.append((c, 0))
            c = table[i][1]
            if c == 0:
                break
    path.append(list(reversed(revPath)))
    return revPath
    