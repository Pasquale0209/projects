#param nb_r;

#param Nr;
#param Ap {Nr,Nr};


var y{Ap} binary;
#var t integer;


#param tu{Ap} default 0;

minimize pathz:
		sum{(i,j) in Ap}y[i,j];
		
subject to p1{(i,j) in Ap}:
	#u*alfa>=demand*x[i,j];
	tu[i,j]>=demand*y[i,j];
	
subject to p2:#per demand
	sum{(i,j) in Ap}y[i,j]*deltan[i,j]<=0;#here we forced to select the paths to the new node
	
subject to balancing{i in N}:
	sum {(i,j) in Ap} y[i,j] - sum {(j,i) in Ap} y[j,i] =
			(if (i == source)
				then (1)
				else (if (i == target) then -1
				else 0));