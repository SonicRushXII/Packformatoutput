import os
import re
import json
import pandas as pd
import html5lib
import shutil

old_pattern = r'replaceitem entity (.*?) (.*?) (.*?)'
replace_old = r'item replace entity \1 \2 \3with '

new_pattern = r'item replace entity (.*?) (.*?) (.*?)with '
replace_new = r'replaceitem entity \1 \2 \3'

packformatdata = pd.read_html('https://minecraft.fandom.com/wiki/Pack_format')
packformatlist = packformatdata[1].values.tolist()
versions = {}

for releases in packformatlist:
	#Change to 5, for 1.16 compatibility aswell. Warning, HIGHLY EXPERIMENTAL
	if releases[2] != '—' and releases[0] >= 5:
		versions[str(releases[0])] = releases[2]

#Changes the Version of the Datapack
def change_version(folder_path , target_version):
	for root, dirs, files in os.walk(folder_path):
		for filename in files:
			#Iterates through every file
			file_path = os.path.join(root,filename)
			
			#Checks if file ends with
			if file_path.endswith('pack.mcmeta'):
				change_pack_format(file_path, target_version)
				
			#Checks for Json Files
			if file_path.endswith('.json'):
				change_json(file_path, target_version)
			
			#Checks for Mcfunction Files
			if file_path.endswith('.mcfunction'):
				change_mcfunction(file_path, target_version)
			
	shutil.make_archive(f'{folder_path} {versions[str(target_version)].replace("1.15","1.16")}', 'zip', folder_path)		
	print("Successfully Modified File")

#Changes the pack format of the file
def change_pack_format(file_path , target_version):
	with open(file_path,'r') as data:
		pack_meta = json.load(data)
		pack_meta["pack"]["pack_format"] = target_version
	with open(file_path,'w') as data:	
		json.dump(pack_meta,data,indent=4)

#Changes the Json File's Structure
def change_mcfunction(file_path, target_version):
	lines = []
	with open(file_path,'r') as mcfunction_file:
		lines = mcfunction_file.readlines()
		for idx,line in enumerate(lines):
			if re.search(old_pattern,line) and target_version > 6:
				lines[idx] = re.sub(old_pattern,replace_old,line)
			elif re.search(new_pattern,line) and target_version <= 6:
				lines[idx] = re.sub(new_pattern,replace_new,line)
			
	with open(file_path,'w') as mcfunction_file:
		mcfunction_file.write("".join(lines))

#Changes the Json File's Structure
def change_json(file_path, target_version):
	# Load the JSON data from the file
	try:
		with open(file_path, 'r') as file:
			data = json.load(file)
	except:
		return None
	
	# Define the functions for upgrading and downgrading player data
	def upgrade_json(playerdata):
		if 'player' in playerdata:
			playerdata['type_specific'] = playerdata.pop('player')
			playerdata['type_specific']['type'] = 'player'
	
	def downgrade_json(playerdata):
		if 'type_specific' in playerdata:
			playerdata['player'] = playerdata.pop('type_specific')
			if 'type' in playerdata['player']:
				del playerdata['player']['type']
	
	def update_json_format(playerdata):
		#print(playerdata)
		if target_version > 9:
			upgrade_json(playerdata)
		else:
			downgrade_json(playerdata)
	
	# Processing Advancement Changes
	try:
		# Process 'criteria' section
		for key in data['criteria']:
			data['criteria'][key]['conditions'].pop('damage', None)
			data['criteria'][key]['conditions'].pop('killing_blow', None)
			
			playerdata = data['criteria'][key]['conditions']['player']
			
			if isinstance(playerdata, list):
				for obj in playerdata:
					if obj['condition'] == 'minecraft:entity_properties':
						update_json_format(obj['predicate'])
						break
			elif isinstance(playerdata, dict):
				update_json_format(playerdata)
				
	except (TypeError, NameError , KeyError):
		pass
		
	# Processing Predicate Changes
	try:
		if isinstance(data,list):
			for key in data:
				update_json_format(key['predicate'])
				update_json_format(key['predicate']['targeted_entity'])
		elif isinstance(data,dict):
			update_json_format(data['predicate'])
			update_json_format(key['predicate']['targeted_entity'])
	except (TypeError, NameError, KeyError):
		pass
		
	# Processing Predicate Alternative Changes
	try:
		if isinstance(data,list):
			condition_type = "minecraft:any_of" if target_version >= 15 else "minecraft:alternative"
			for key in data:
				if key['condition'] in ["minecraft:any_of", "minecraft:alternative"]:
					key['condition'] = condition_type
		elif isinstance(data,dict):
			condition_type = "minecraft:any_of" if target_version >= 15 else "minecraft:alternative"
			if data['condition'] in ["minecraft:any_of", "minecraft:alternative"]:
				data['condition'] = condition_type
	except (TypeError, NameError, KeyError):
		pass		
	
	# Processing The List Changes
	try:
		blockdata = data['values']
		
		for i,val in enumerate(blockdata):
			if target_version <= 9 and val == '#minecraft:wool_carpets':
				blockdata[i] = '#minecraft:carpets'
				break
			elif target_version > 9 and val == '#minecraft:carpets':
				blockdata[i] = '#minecraft:wool_carpets'
				break
		
		if target_version >= 7:
			if file_path.endswith('passable.json') and ('#minecraft:candles' not in blockdata):
				blockdata.append('#minecraft:candles')
			if file_path.endswith('passable.json') and ('minecraft:light' not in blockdata):
				blockdata.append('minecraft:light')
			if file_path.endswith('nalive.json') and ('minecraft:marker' not in blockdata):
				blockdata.append('minecraft:marker')
			
		else:
			new_additions = set(['#minecraft:candles','minecraft:marker','minecraft:light'])
			for i,val in enumerate(blockdata):
				if val in new_additions:
					del blockdata[i]
		
	except (TypeError, NameError , KeyError):
		pass
	
	# Write the modified JSON data back to the file
	with open(file_path, 'w') as file:
		json.dump(data, file, indent=2)

datapack = input("Input Datapack FileName: ")
for packformat in versions.keys():
	change_version(datapack,int(packformat))
