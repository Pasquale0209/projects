#--------------------------------------------------
# Sets and parameters
#--------------------------------------------------

# Set of potential locations
param I;
set Iset := 1..I;

# Set of customers
param J;
set Jset := 1..J;

#demand for treatments
param t{Iset};
#physiotherapy service equipment and staff cost
param c{Jset};

# physiotherapy service capacity
param Gamma;

param d{Iset, Jset};



