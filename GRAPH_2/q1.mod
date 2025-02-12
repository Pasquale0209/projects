var x{Iset,Jset} binary;
var y{Jset} binary;

minimize objfun:
	sum{j in Jset}c[j]*y[j]+sum{i in Iset, j in Jset}x[i,j]*d[i,j]*t[i];

s.t. demand{j in Jset}:
	sum{i in Iset}x[i,j]*t[i]<=Gamma*y[j];

s.t. unique{i in Iset}:
	sum{j in Jset}x[i,j]==1;