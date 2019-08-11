import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from ICQData import *

def remove_no_mags(data):
	with_mag   = data[data['mag']!='']
	nomag = data[data['mag']=='']
	return with_mag, nomag

def sort_by_date_per_observer(data):
	sorted_by_obs_per_date = data.sort_values(by=['obs','yearobs','monthobs','dayobs'])
	return sorted_by_obs_per_date

def remove_row(data, row_index):
	""" 
	removes a row from a pandas dataframe
	"""
	columns = data.columns
	before = np.ndarray.tolist(np.asarray(data[0:row_index]))
	after  = np.ndarray.tolist(np.asarray(data[row_index+1:]))
	for k in range(len(after)):
		before.append(after[k])
	combined = np.array(before)
	data = pd.DataFrame(combined, columns=columns)
	return data

def remove_dupe_dates(data, perihelion_date):
	"""
	Adds date-time column to dataframe.
	Adds daystoperihelion column to dataframe.
	Removes points that occur on the same date by same observer.
	"""
	print("Removing points that are on the same date by the same observer.")
	data['yearobs'] = data['yearobs'].astype('int32')
	data['monthobs']= data['monthobs'].astype('int32')
	data['dayobs']  = data['dayobs'].astype('float64')
	
	these_years = np.asarray(data['yearobs'])
	these_months= np.asarray(data['monthobs'])
	these_days  = np.floor(np.asarray(data['dayobs']))
	dec_hours   = (np.asarray(data['dayobs']) - these_days) * 24
	these_hours = np.floor(dec_hours)
	dec_minutes= (dec_hours - these_hours) * 60.
	these_minutes= np.floor(dec_minutes)
	these_seconds = (dec_minutes - these_minutes) * 60.
			
	date_times = pd.DataFrame({'year': these_years,
							   'month': these_months,
							   'day'  : these_days,
							   'hour': these_hours,
							   'minute':these_minutes,
							   'second':these_seconds})
						
	date_times = pd.to_datetime(date_times)
	data.insert(3, "Date-Times", date_times, True)

	peri_year = int(perihelion_date[0:4])
	peri_month= int(perihelion_date[5:7])
	peri_day  = int(perihelion_date[8:10])
	peri_datetime = datetime(peri_year, peri_month, peri_day)
	timedeltas = (date_times - peri_datetime)
	for k in range(len(timedeltas)):
		timedeltas[k] = timedeltas[k].days
	days_to_peri = pd.DataFrame({'daystoperihelion': timedeltas})
	data.insert(4, 'daystoperihelion', timedeltas, True)
		
	columns=data.columns
	removed_for_duplicated_dates = []
	for k in range(len(data)-1, -1, -1):
		this_row = (data.iloc[k])
		next_row = (data.iloc[k-1])
		if (this_row['obs'] == next_row['obs']) and (this_row['daystoperihelion'] == next_row['daystoperihelion']):
			if (float(this_row['instaperture']) < float(next_row['instaperture'])):
				removed_for_duplicated_dates.append(next_row)
				data = remove_row(data, k-1)
				continue
			elif (this_row['magmethod'] == "S"):
				removed_for_duplicated_dates.append(next_row)
				data = remove_row(data, k-1)
				continue
			elif (next_row['magmethod'] == "S"):
				removed_for_duplicated_dates.append(this_row)
				data = remove_row(data, k)
				continue
			elif (this_row['magmethod'] == "M"):
				removed_for_duplicated_dates.append(next_row)
				data = remove_row(data, k-1)
				continue
			elif (next_row['magmethod'] == "M"):
				removed_for_duplicated_dates.append(this_row)
				data = remove_row(data, k)
				continue
			elif ((this_row['magmethod'] == "B") or (this_row['magmethod'] == "I")):
				removed_for_duplicated_dates.append(next_row)
				data = remove_row(data, k-1)
				continue
			elif ((next_row['magmethod'] == "B") or (next_row['magmethod'] == "I")):
				removed_for_duplicated_dates.append(this_row)
				data = remove_row(data, k)
				continue
			else:
				removed_for_duplicated_dates.append(this_row)
				data = remove_row(data, k)
				continue
	
	if len(removed_for_duplicated_dates)!=0:	
		removed_for_duplicated_dates = pd.DataFrame(np.array(removed_for_duplicated_dates), columns=columns)		
	return data, removed_for_duplicated_dates

def remove_reverse_binocular_method(data):
	print("Removing points that use a reverse binocular method.")
	columns = data.columns
	removed_for_reverse_binoc = []
	for k in range (len(data)-1,-1,-1):
		if (data['specialnotes'].iloc[k] == 'r' ) or (data['specialnotestwo'].iloc[k] == 'r'):
			removed_for_reverse_binoc.append(np.asarray(data.iloc[k]))
			data = remove_row(data, k)
		
	if len(removed_for_reverse_binoc)!=0:
		removed_for_reverse_binoc = pd.DataFrame(np.array(removed_for_reverse_binoc), columns=columns)
	return data, removed_for_reverse_binoc

def remove_bad_extinction(data):
	print("Remvoing points that indicated an inproper extinction correction was performed.")
	columns = data.columns
	removed_for_bad_extinction = []
	for k in range(len(data)-1, -1, -1):
		if (data['specialnotes'].iloc[k]=='&') or (data['specialnotestwo'].iloc[k]=='&'):
			removed_for_bad_extinction.append(np.asarray(data.iloc[k]))
			data = remove_row(data, k)
			
	if len(removed_for_bad_extinction)!=0:
		removed_for_bad_extinction = pd.DataFrame(np.array(removed_for_bad_extinction), columns=columns)
	return data, removed_for_bad_extinction
	
def remove_poor_weather(data):
	print("Removing points that were taken under poor weather conditions.")
	columns = data.columns
	removed_for_poor_weather = []
	for k in range(len(data)-1, -1, -1):
		if (data['poorconditions'].iloc[k]==':'):
			removed_for_poor_weather.append(np.asarray(data.iloc[k]))
			data = remove_row(data, k)
	
	if len(removed_for_poor_weather)!=0:
		removed_for_poor_weather = pd.DataFrame(np.array(removed_for_poor_weather), columns=columns)
	return data, removed_for_poor_weather

def remove_tele_binoc_method(data):
	print("Removing points which used a telescope under a magnitude of 5.4 or binoculars under a magnitude of 1.4.")
	telescopemethod = ['C','R','D','I','J','L','M','q','Q','r','S','T','U','W','Y']
	binocularmethod = ['A','B','N','O']
	columns = data.columns
	removed_for_telescope_mag_under_5_4 = []
	removed_for_binocular_mag_under_1_4 = []
	for k in range(len(data)-1, -1, -1):
		if (data['insttype'].iloc[k] in telescopemethod) and (float(data['mag'].iloc[k])<5.4):
			removed_for_telescope_mag_under_5_4.append(np.asarray(data.iloc[k]))
			data = remove_row(data, k)
		elif (data['insttype'].iloc[k] in binocularmethod) and (float(data['mag'].iloc[k])<1.4):
			removed_for_binocular_mag_under_1_4.append(np.asarray(data.iloc[k]))
			data = remove_row(data, k)
			
	if len(removed_for_telescope_mag_under_5_4)!=0:
		removed_for_telescope_mag_under_5_4 = pd.DataFrame(np.array(removed_for_telescope_mag_under_5_4), columns=columns)
	if len(removed_for_binocular_mag_under_1_4)!=0:
		removed_for_binocular_mag_under_1_4 = pd.DataFrame(np.array(removed_for_binocular_mag_under_1_4), columns=columns)
	return data, removed_for_telescope_mag_under_5_4, removed_for_binocular_mag_under_1_4

def remove_unspecified_method(data):
	print("Removing points that used an unspecified magnitude method.")
	allowedmagnitudemethod = ['S','B','M','I','E']
	columns = data.columns
	removed_for_unspecified_method = []
	for k in range(len(data)-1, -1, -1):
		if (data['magmethod'].iloc[k] not in allowedmagnitudemethod):
			removed_for_unspecified_method.append(np.asarray(data.iloc[k]))
			data = remove_row(data, k)
			
	if len(removed_for_unspecified_method)!=0:
		removed_for_unspecified_method = pd.DataFrame(np.array(removed_for_unspecified_method), columns=columns)
	return data, removed_for_unspecified_method

def remove_outdated_catalog(data):
	print("Removing points which used an outdated reference star catalog.")
	outdated_catalog = ['SC']
	columns = data.columns
	removed_for_outdated_catalog = []
	for k in range(len(data)-1, -1, -1):
		if (data['referencecat'].iloc[k] in outdated_catalog):
			removed_for_outdated_catalog.append(np.asarray(data.iloc[k]))
			data = remove_row(data, k)
			
	if len(removed_for_outdated_catalog)!=0:
		removed_for_outdated_catalog = pd.DataFrame(np.array(removed_for_outdated_catalog), columns=columns)
	return data, removed_for_outdated_catalog

def split_columns(data):
	metalist = []
	for k in range(len(data)):
		tmp = []
		tmp.append(data[k][0:3].strip(' '))
		tmp.append(data[k][3:9].strip(' '))
		tmp.append(data[k][9].strip(' '))
		tmp.append(data[k][11:15].strip(' '))
		tmp.append(data[k][16:18].strip(' '))
		tmp.append(data[k][19:24].strip(' '))
		tmp.append(data[k][25].strip(' '))
		tmp.append(data[k][26].strip(' '))
		tmp.append(data[k][28:32].strip(' '))
		tmp.append(data[k][32].strip(' '))
		tmp.append(data[k][33:35].strip(' '))
		tmp.append(data[k][35:40].strip(' '))
		tmp.append(data[k][40].strip(' '))
		tmp.append(data[k][41:43].strip(' '))
		tmp.append(data[k][43:47].strip(' '))
		tmp.append(data[k][48].strip(' '))
		tmp.append(data[k][49:54].strip(' '))
		tmp.append(data[k][54].strip(' '))
		tmp.append(data[k][55:57].strip(' '))
		tmp.append(data[k][58:63].strip(' '))
		tmp.append(data[k][64:67].strip(' '))
		tmp.append(data[k][68:74].strip(' '))
		tmp.append(data[k][74].strip(' '))
		tmp.append(data[k][75:80].strip(' '))
		metalist.append(tmp)
		
	columns = ["shortperapparition","designation","splitnuc","yearobs","monthobs","dayobs","specialnotes","magmethod","mag","poorconditions","referencecat","instaperture","insttype","focalratio","magnification","comadiamestimate","comadiameter","centralcondensation","degreeofcondensation","taillength","positionangleoftail","ICQPublication","specialnotestwo","obs"]
	return pd.DataFrame(np.array(metalist), columns = columns)
	
def do_general_sorting(data, perihelion_date, do_sorting):
	if do_sorting == False:
		print("Skipping general sorting.")
	else:
		sorted_data = sort_by_date_per_observer(data)
		remaining_data, removed_for_no_mag_reported   = remove_no_mags(sorted_data)
		remaining_data, removed_for_reverse_binoc     = remove_reverse_binocular_method(remaining_data)
		remaining_data, removed_for_poor_weather	  = remove_poor_weather(remaining_data)
		remaining_data, removed_for_bad_extinction    = remove_bad_extinction(remaining_data)
		remaining_data, \
		  removed_for_telescope_mag_under_5_4, \
		  removed_for_binocular_mag_under_1_4	      = remove_tele_binoc_method(remaining_data)
		remaining_data, removed_for_unspecified_method= remove_unspecified_method(remaining_data)
		remaining_data, removed_for_outdated_catalog  = remove_outdated_catalog(remaining_data)
		remaining_data, removed_for_duplicated_dates  = remove_dupe_dates(remaining_data, perihelion_date)
	
	print(len(removed_for_poor_weather))
	removed_data_metalist = 		{ 'removedfornomag': removed_for_no_mag_reported,
										   'removedforreverse_binoc': removed_for_reverse_binoc,
										   'removedforpoor_weather': removed_for_poor_weather,
										   'removedforbad_extinction':removed_for_bad_extinction,
										   'removedfortelescope_mag_under_5_4':removed_for_telescope_mag_under_5_4,
										   'removedforbinocular_mag_under_1_4':removed_for_binocular_mag_under_1_4,
										   'removedforunspecified_method':removed_for_unspecified_method,
										   'removedforoutdatedcatalog':removed_for_outdated_catalog,
										   'removedforduplicateddates':removed_for_duplicated_dates}	
	
	final_cat = remaining_data
	print("Done with general sorting!")
	return final_cat, removed_data_metalist

def do_helio_correction(data, helio):
	if helio==False:
		print("Skipping heliocentric correction")
	else:
		mags=(data['mag'].astype('float64'))
		mags=np.asarray(mags)
		
		heliocentriccorrectedmag = mags + 15.
		
		
		data.insert(11, 'heliocentriccorrectedmag', heliocentriccorrectedmag, True)

	return data
	
	
def please_just_do_everything_for_me():
	print("ha, you wish")
	pass