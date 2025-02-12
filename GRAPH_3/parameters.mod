#-----------------
# parameters
#-----------------
# Number and set of nodes
param n; 
set N := 1..n;
set A within N cross N;

param f{A};   # Arc installation cost
param lenght{A};# Arc lenght
param u;  # Arc channel capacity

# Number and set of demands 
param n_d; 
set K := 1..n_d;

param s {K} within N; # Source
param t {K} within N; # Destination
param d {K}; # Flow demand

param demand_balance {i in N,k in K} := if i = t[k] then -1 
			else ( if i = s[k] then  1 else 0 );

param delta; #maximum arc lenght
param g; # node device cost
param gamma; # node device capacity 