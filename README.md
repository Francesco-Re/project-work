# project-work Overview

## Repository Summary

The repository contains the following files:
1. Problem.py, containing the python class that generates the problem
2. problem.ipynb, containing the set of test used to benchmark the implementation
3. s343404.py containing the implementation decided to solve the problem
4. base_requirements.txt, containing all dependencies needed to run the solution


## Approach used 

The implementation exploits the Clarke-Wright Savings Algorithm (https://it.scribd.com/document/584775842/Scheduling-of-Vehicles-From-a-Central-Depot-to-a-Number-of-Delivery-Points).
The algorithm has been formulated as a possible solution of the Vehicle Routing Problem (VRP) and it is based on the concept of "Savings".

The VRP is a problem in which a series of trucks has to deliver in serveral points from a depot point. The scope of this problem is to  minize the distance used while delivering.
To do so the Savings algotithm is based on the fact that the saved distance obtained by joining the single routes to points j and i (back and forth from the depot point to i/j point) is equal to the sum of the distances from the depot to each point minus the lenght of the route fro i to j.
From a starting state of having a series of routes from depot to each specific point back and forth (similarly to the baseline implementation of the problem resolution) the routes are joined in order to have the higest amount of savings.

In the context of the traveling thief problem (TTP) an adjustment to the saving calculation is needed, since the cost of route 0 -> i -> j -> 0 might be different from 0 -> j -> i -> 0 due to the cost function depending on the gold carried.
So before joining the routes both orders are evalued and the one with the higher saving cost is used. If no additional saving is found or a certain number of iterations are reached the main loop is ended and each single route is joined into one, given as output.

The general approach of the solution function starts by calculating the distances matrixes using the scipy library. This library was used to increase efficiency in the creation of the paths which is a costly part of the function, especially at higher number of cities, since it is calculating all possible shortests paths from all nodes to all nodes.
From there the algorithm will apply the logic of the Clarke-Wright Algorithm and find an optimal path. Inside it a Tournament based approach is used to retrieve the best saving value in every iteration. The algorithm will continue for at most a max number of iterations (in this implementation being five times the amount of cities with gold) or will terminate early if the savings aren't big enough.

## Main File Contents (s343404.py)

The file contains the following functions:

1. **costCounter**: given a path calculates the cost of such path. Makes one reasonable assumption: each time the base is reached the gold is unloaded.
2. **is_valid**: default path checking function, controls the validity of the path
3. **verify_all_robbed**: custom path checking function, assumes the path is valid and checks if all cities have been robbed, if they have not been robbed multiple times and if there has been any discrepancy in the gold robbed in each city
4. **reconstruct_path**: given the predecessor matrix (which returns the predecessor of a node j when trying to reach it from node i, returning -9999 if no path is available), a start node and an end node recreates the whole shortest path
5. **solution**: receives the problem class variable and optionally a boolean (defaulted to false).
It has an helper function called **evalue_route**. This function receives a set amount of targets which are the nodes that will be joined in a path and its path will be evalued, returning the cost and the resulting path.
The main loop's job is to try to combine different paths until the best saving possible is at least a certain amount or it hasn't done yet enough iterations. 
Additionally to avoid the algorithm to have computational times become unreasonably high a pruning strategy is used. While choosing two targets only the nodes being in a threshold distance are taken. This treshold is the 10% percentile of all the distances calculated between two cities that are not the base.
Inside the while loop all possible combinations of paths are checked and the saving value is calculated in both orders (reaching one first or the other first).
After that the champion saving value among all the one obtained is checked if higher than a minimum threshold. This is to avoid excessive calculations to get marginal improvements.
If the saving is a high enough value the two path are joined, otherwise the main loop ends since there won't be any more savings.
Once the main loop is over all the single routes are joined into one path. 
If the input boolean getCostNotPath is received as true only the cost of the optimal path is returned, if it is false (or nothing is put) the path is returned. 
6. **main**: basic testing function that compares the cost given by the baseline and the solution for a 500 city case with density = 1 and beta = 2. After that the resulting path is validated throught the **is_valid** function

### General results
While the results remain more or less unchanged with marginal decreases in cost compared to the baseline with beta = 1, with any other positive value of beta the result become drammatically better, as shown in the results of the problem jupyter file.

While at smaller number of cities the algorithm is pretty much instantaneus on bigger cities count (tested at 1000 and density = 1 as maximum values) the algorithm takes up to around 6 minutes.
The whole testing suite in the jupyter file took around 30 minutes to compute. The setup used to compute the results has an AMD ryzen 5 7600 processor and a rx 9060 xt GPU.