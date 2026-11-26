from domain.demolitions_api import router as demolitions
from domain.brick_stacks_api import router as brick_stacks
from domain.cluster_rules_api import router as cluster_rules
from domain.rack_candidates_api import router as rack_candidates
from domain.rack_merges_api import router as rack_merges

routers = (demolitions, brick_stacks, cluster_rules, rack_candidates, rack_merges,)
