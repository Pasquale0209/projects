
var x{Iset,Jset} binary;
var y{Jset} binary;
var s{Iset}  >= 0;

minimize objfun:
	#sum{j in Jset}c[j]*y[j]+sum{i in Iset}s[i]*t[i];
	sum{j in Jset} c[j]*y[j] + sum{i in Iset, j in Jset} x[i,j]*d[i,j]*t[i];

s.t. demand{j in Jset}:
	sum{i in Iset}x[i,j]*t[i]<=Gamma*y[j];

s.t. unique{i in Iset}:
	sum{j in Jset}x[i,j]==1;
	
s.t. min_distance{i in Iset, j in Jset}:
	#s[i]<=d[i,j]*y[j]+(1-y[j])*10000000000;
	s[i]<=d[i,j]*y[j]+(1-y[j])*maxd;
	
	
s.t. closest_center{i in Iset}:
	sum{j in Jset}x[i,j]*d[i,j]==s[i];
