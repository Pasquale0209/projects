



		#####################
		#	MASTER PROBLEM	#
		#####################
param cp{P} default 0;
param del{P} default 0;

var x {P} >= 0;

minimize PathCost:
	sum {p in P} cp[p]*x[p];

s.t. PathBalance {k in K}: 
	sum {p in P: orig[p] = s[k] and dest[p] = t[k]} x[p] = d[k];
	
s.t. PathCapacity {(i,j) in Ap}: 
     sum {p in P: (i,j) in Path[p]} x[p] <= u*alfa;
     
#subject to delay{k in K}:#per demand
	#sum {p in P: orig[p] = s[k] and dest[p] = t[k]}(x[p]*sum{(i,j) in A:(i,j) in Path[p]}(delta[i,j]))<=Delta_Max;
#	sum {p in P: orig[p] = s[k] and dest[p] = t[k]}x[p]*del[p]<=Delta_Max;
	#sum{(i,j) in A}x[i,j,k]*delta[i,j]<=Delta_Max;
     


		#####################
		#  PRICING PROBLEM	#
		#####################	
		
#param source symbolic in N;
#param target symbolic in N;
		
param b {i in Nr} := if i = target then 1 else ( if i = source then - 1 else 0 );

# Pricing subproblem cost vector
param g {Ap} default 1;
param sigma {K} default 0;

var z {Ap} binary;

minimize ShortestPath: 
	 sum {(i,j) in Ap} g[i,j] * z[i,j];

s.t. NodeBalance {i in Nr}: 
     sum {(j,i) in Ap} z[j,i] - sum {(i,j) in Ap} z[i,j] = b[i];
     
s.t. delay {k in K}:#the delay constraint is added here on the pricing and not the master
	sum {(i,j) in Ap} z[i,j]*deltan[i,j]<=Delta_Max;




#PROBLEM DEFINITION

problem master: x, PathCost, PathBalance, PathCapacity; 

problem pricing: z, ShortestPath, NodeBalance, delay;
