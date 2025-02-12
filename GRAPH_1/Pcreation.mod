var y{A} binary;
#var t integer;

param demand default 0;
param target default 0;
param source default 0;
param tu{A} default 0;

minimize pathz:
		sum{(i,j) in A}y[i,j];
		
subject to p1{(i,j) in A}:
	#u*alfa>=demand*x[i,j];
	tu[i,j]>=demand*y[i,j];
	
subject to p2:#per demand
	sum{(i,j) in A}y[i,j]*delta[i,j]<=Delta_Max;
	
subject to balancing{i in N}:
	sum {(i,j) in A} y[i,j] - sum {(j,i) in A} y[j,i] =
			(if (i == source)
				then (1)
				else (if (i == target) then -1
				else 0));