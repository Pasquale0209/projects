var x{A,K} binary;
var y{A} integer >=0;

minimize Objfunct3:
		sum{(i,j) in A} y[i,j]*f[i,j];#c[i,j]=f[i,j] the cost is not provided

subject to Capacity{(i,j) in A}:#capacity
	sum{k in K}x[i,j,k]*d[k]<=u*beta+y[i,j]*lambda;

subject to demand{k in K}:#per demand
	sum{(i,j) in A}x[i,j,k]*delta[i,j]<=Delta_Max;
	
	
subject to balancing{i in N,k in K}:
	sum {(i,j) in A} x[i,j,k] - sum {(j,i) in A} x[j,i,k] =
			(if (i == s[k])
				then (1)
				else (if (i == t[k]) then -1
				else 0));