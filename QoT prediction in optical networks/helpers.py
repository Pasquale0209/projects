"""
In this file are present some the functions that are used 
in the jupyter notebook, in order to make the notebook more 
compact.

"""
import numpy as np
from sklearn.model_selection import train_test_split 


def read_dataset(filename):


    span_length_matrix = [] #F: list for span lengths (in km) along the path

    link_occupancy_matrix = [] #F: list for the number of channels in the links of the lightpath

    SNR_vect = [] #F: list for SNR values (dB) at the receiver

    with open(filename) as data_file:

        for line in data_file: #F: line will scan through each lightpath

            elements = line.split(';') #F: in the dataset the various characteristics are separated by a ; for each lightpath
            # 4 is the maximum number of splits to do
            #F: obtain list where each element is the list of span length for a lightpath
            span_lengths_vect = [int(i) for i in elements[0].split(",")]

            span_length_matrix.append(span_lengths_vect)

            link_occupancy_vect = [int(i) for i in elements[1].split(",")]
            link_occupancy_matrix.append(link_occupancy_vect)

            snr = elements[2] #F: SNR at the receiver for the considered lightpath
            SNR_vect.append(float(snr))


    return span_length_matrix, link_occupancy_matrix, SNR_vect




def calculate_m_v_s(spans,link_occ,snr_values):

	numspans = []
	lightpathlength = []
	for i in range(len(spans)):
		numspans.append(len(spans[i]))
		lightpathlength.append(sum(spans[i]))

	numocc = []
	for i in range(len(link_occ)):
		numocc.append(sum(link_occ[i]))

	#Let's see what we have in numspans and lightpathlength:
	#print(numspans)
	#print(lightpathlength)
	
	#F: numspans
	mean_numspans = round(sum(numspans)/len(numspans),2)
	var_numspans = round(sum([((x - mean_numspans) ** 2) for x in numspans])/len(numspans),2)
	std_numspans = round(var_numspans**0.5,2)

	#F: lightpathlength
	mean_lightpathlength = round(sum(lightpathlength)/len(lightpathlength),2)
	var_lightpathlength = round(sum([((x - mean_lightpathlength) ** 2) for x in lightpathlength])/len(lightpathlength),2)
	std_lightpathlength = round(var_lightpathlength**0.5,2)

	# Link occupacy
	mean_occ = round(sum(numocc)/len(numocc),2)
	var_occ = round(sum([((x - mean_occ) ** 2) for x in numocc])/len(numocc),2)
	std_occ = round(var_occ**0.5,2)

	#F: snr
	mean_snr = round(sum(snr_values)/len(snr_values),2)
	var_snr = round(sum([((x - mean_snr) ** 2) for x in snr_values])/len(snr_values),2)
	std_snr = round(var_snr**0.5,2)

	print('**********')
	print('Number of spans: mean={}, var={}, std={}'.format(mean_numspans,var_numspans,std_numspans))
	print('Lightpath length: mean={}, var={}, std={}'.format(mean_lightpathlength,var_lightpathlength,std_lightpathlength))
	print('Number of channels in links: mean={}, var={}, std={}'.format(mean_occ,var_occ,std_occ))
	print('SNR: mean={}, var={}, std={}'.format(mean_snr,var_snr,std_snr))
	print('**********')


def extract_features(span_matrix, link_occupancy_matrix):

    X_matrix = [] #F: name of the numpy array to return

    # take one lightpath (vector of span length and information on the interferers)
    for span_len_vect, link_occupancy_vect in zip(span_matrix, link_occupancy_matrix):

        feature_vect = []

        feature_vect.append(len(span_len_vect))
        feature_vect.append(sum(span_len_vect))
        feature_vect.append(max(span_len_vect))

        feature_vect.append(len(link_occupancy_vect))
        feature_vect.append(sum(link_occupancy_vect))
        feature_vect.append(max(link_occupancy_vect))
        X_matrix.append(feature_vect)
        
    return np.array(X_matrix)
    
def split_dataset(X,y, verbose = False):

  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

  if verbose: 
    print(X.shape)
    print(y.shape)
    print(X_train.shape)
    print(y_train.shape)
    print(X_test.shape)
    print(y_test.shape)

  return X_train, X_test, y_train, y_test
  
  
#THIS IS MODIFIED FOR NEW VALUES SHOWN ON THE SLIDES OF THE PROject

def SNR_to_MF(SNR):
	# Input:    - SNR: SNR value (predicted or ground truth) used to decide modulation format
	# Output:   - order of the highest configurable MF; return a number corresponding to the MF	
	#             4 (QPSK), 8 (8QAM), 16 (16QAM), 32 (32QAM), 64 (64QAM)	

	# < and > instead of <= and >=, as SNR is a float and floats cannot be compared with equality
	if SNR < 8.7:
		return 0

	elif SNR > 8.7 and SNR < 12.8:
		return 4

	elif SNR > 12.8 and SNR < 15.2:
		return 8

	elif SNR > 15.2 and SNR < 18.2:
		return 16

	elif SNR > 18.2 and SNR < 21:
		return 32

	else:
		
		return 64
