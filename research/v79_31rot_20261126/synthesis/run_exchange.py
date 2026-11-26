import search_tree
from quotient_exchange import quotient_plan,COUNTERS
import sys
search_tree.quotient_plan=quotient_plan
search_tree.run(36,sys.argv[1],0,7,2,True,True)
print('EXCHANGE',dict(COUNTERS),flush=True)
