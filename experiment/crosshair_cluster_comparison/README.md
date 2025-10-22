# Reproduction

Install crosshair

    uvx crosshair-tool
    
Execute `./cluster.py se` to produce clusters using symbolic execution.

Execute `./cluster.py test` to produce clusters using tests.

Execute `./cluster.py diff` to measure average Rand index.

Output: `0.9470435347628331`


# Rand Index (ARI)

- The Rand Index computes a similarity measure between two clusterings by considering all pairs of samples and counting pairs that are assigned in the same or different clusters in the predicted and true clusterings
