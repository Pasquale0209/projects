#-----------------
# parameters
#-----------------
# Number and set of nodes
param nb_n; 
set N := 1..nb_n;
set A within N cross N;

param f{A};     # transportation/channel installation cost
param delta{A}; # arc delay
param u ;# current arc capacity
param alfa default 2;
param beta default 0.5;
param lambda ;  # channel capacity 
param Delta_Max; #maximum delay





# Number and set of demands 
param nb_d; 
set K := 1..nb_d;

param s {K} within N; # Source
param t {K} within N; # Destination
param d {K}; # Flow demand