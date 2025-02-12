var x{A,K} >=0,<=1;

minimize Objfunct1:
		sum{(i,j) in A,k in K} x[i,j,k]*f[i,j]*d[k];
		
subject to demand{k in K}:#per demand
	sum{(i,j) in A}x[i,j,k]*delta[i,j]<=Delta_Max;
	
subject to Capacity{(i,j) in A}:#capacity
	sum{k in K}x[i,j,k]*d[k]<=u*alfa;
	
subject to balancing{i in N,k in K}:
	sum {(i,j) in A} x[i,j,k] - sum {(j,i) in A} x[j,i,k] =
			(if (i == s[k])
				then (1)
				else (if (i == t[k]) then -1
				else 0));