import pandas as pd
from ICQData_libraries import *

"""
###############################List of an ICQData object's variables#################################
rawdata :  The raw data,
filename:  Filename of initial input data,
columnated_data : Data split into N x 24 array. N is number of observations, 24 is 
				  each column in original ICQ 80 column format.,
general_sorted_data : The data sorted and filtered by normal means,
helio_shifted_data : Original data with extra column containing the heliocentric corrected magnitude.
"""

class ICQData:

	def __init__(self, filename, perihelion_date, general_sorting=True, plots=True, McMc=True): #put any future initial tags needed here
		
		with open(filename) as f:
			cat = f.readlines()
		f.close()
				
		self.rawdata=cat
		self.filename=filename
		self.columnated_data = split_columns(self.rawdata)
		
		self.general_sorted_data, self.removed_data_metalist = do_general_sorting(self.columnated_data, perihelion_date, general_sorting)

	def shift_data(self, helio=True, phase=True, stats=True):
		
		self.helio_shifted_data = do_helio_correction(self.general_sorted_data, helio)
		
		return self.helio_shifted_data