var x{A,K} <=1 >=0;
var y{N} <=1 >=0;
var z{A}  >=0;

# Current total number of cover inequalities
param nc default 0;
# Set of indices for the cover inequalities
set C := 1..nc;
# Set of items composing each cover
set CI_i{C} ;
set CI_j{C} ;
set CI_k{C} ;
param CI_c{C} >=0;
param chi2{C,K,N} default 0;


minimize flow:
		sum{(i,j) in A} f[i,j] * z[i,j] + sum{i in N}y[i]*g;

 s.t. DemandRouting {i in N, k in K}: 
     sum {(i,j) in A} x[i,j,k] - sum {(j,i) in A} x[j,i,k] = 
     			demand_balance[i,k];

subject to capacity{(i,j) in A}:
		sum{k in K}d[k]*x[i,j,k] <= z[i,j]*u;
		
subject to amp{(i,j) in A,k in K}:
	x[i,j,k]*lenght[i,j]<=delta*(1-y[i])+maxd*y[i];
	
subject to capa{i in N}:
	sum{k in K, j in N: (i,j) in A and lenght[i,j]>delta}x[i,j,k]*d[k]<=y[i]*gamma;

# Constraints for each cover inequality
s.t. Cover{c in C}:
	sum {i in CI_i[c],j in CI_j[c],k in CI_k[c]:chi2[c,k,j]==1 } x[i,j,k] <= CI_c[c]-1;

#--------------------------------------------------
#                 Separation problem
#--------------------------------------------------

# The separation problem looks for a cover inequality
# violated by the current LP solution

# Fractional solution of current LP
param x_star{A,K} >= 0, <= 1;
 
# Binary variable for item in the cover
var chi{K,N} binary;

# Objective function: Find the most violated cover inequality
minimize Violation: 
	#sum {j in N,k in K:(param_i, j) in A and lenght[param_i,j]>delta} (1 - x_star[param_i,j,k])*chi[k,j];
	sum {(i,j) in A,k in K:param_i==i and lenght[param_i,j]>delta} (1 - x_star[param_i,j,k])*chi[k,j];

# Cover condition constraint
subject to CoverCondition:
	sum {(i,j) in A,k in K:param_i==i and lenght[param_i,j]>delta} d[k]*chi[k,j] >= y[param_i]*gamma+1;

#These two following constraints were added to enforce some conditions that should have been forced with the previous
#constraint and obj function, but AMPL somehow didn't force them.

s.t. NOOOOO:#enforce that there can't be a chi between the same two nodes, there is no arc between ii
	sum {k in K,j in N:j==param_i}chi[k,j]==0; #(i,i)=0
	
s.t. Ni:#enforce that, if there is no arc then chi has to be 0
	sum{k in K, j in N: (param_i, j) not in A}chi[k,j]==0;