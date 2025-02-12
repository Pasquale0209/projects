#var x{A,K} binary;
#var y{N} binary;

var x{A,K} <=1 >=0;
var y{N} <=1 >=0;
var z{A}  >=0;

minimize flow:
		sum{(i,j) in A} f[i,j] * z[i,j] + sum{i in N}y[i]*g;

 s.t. DemandRouting {i in N, k in K}: 
     sum {(i,j) in A} x[i,j,k] - sum {(j,i) in A} x[j,i,k] = 
     			demand_balance[i,k];

subject to capacity{(i,j) in A}:
		sum{k in K}d[k]*x[i,j,k] <= z[i,j]*u;
		
subject to amp{(i,j) in A,k in K}:
	x[i,j,k]*lenght[i,j]<=delta*(1-y[i])+maxd*y[i];
	
subject to cuts{sv in C}:
	
	sum{(k,j) in A: (k in S[sv] and j not in S[sv])}z[k,j] >=
					ceil(sum{fi in K:s[fi] in S[sv] and t[fi] not in S[sv]}d[fi]/u);