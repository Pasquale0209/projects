var x{A,K,1..2} binary;

var l integer;
maximize Objfunct4:
	l;

subject to delay{k in K}:#per demand
	sum{(i,j) in A}x[i,j,k,1]*delta[i,j]<=Delta_Max;
	
subject to Capacity{(i,j) in A}:#capacity
	sum{k in K,p in 1..2}x[i,j,k,p]*d[k]<=2*u*alfa;
	
subject to balancing{i in N,k in K,p in 1..2}:
	sum {(i,j) in A} x[i,j,k,p] - sum {(j,i) in A} x[j,i,k,p] =
			(if (i == s[k])
				then (1)
				else (if (i == t[k]) then -1
				else 0));
				
subject to disjointness{(i,j)in A, k in K}:
	x[i,j,k,1]+x[i,j,k,2]<=1;
	
	
subject to minimum{(i,j)in A}:
	l<=2*alfa*u-sum{k in K, p in 1..2}x[i,j,k,p]*d[k];