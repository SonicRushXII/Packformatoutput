import os
import re
import json
import pandas as pd
import html5lib
import shutil

packformatdata = pd.read_html('https://minecraft.fandom.com/wiki/Pack_format')
packformatlist = packformatdata[0].values.tolist()
versions = {}

for idx,releases in enumerate(packformatlist):
	#Change to 5 if you want 1.16 compatiblity aswell
	if releases[2] != '—' and releases[0] >= 7:
		versions[str(releases[0])] = releases[2]

#Changes the Version of the Datapack
def change_version(folder_path , target_version):
	for root, dirs, files in os.walk(folder_path):
		#Renames custom to item
		if 'custom' in dirs:
			custom_folder_path  = os.path.join(root,'custom')
			item_folder_path  = os.path.join(root,'item')
			
			if os.path.exists(item_folder_path):
				for file_name in os.listdir(custom_folder_path):
					file_path = os.path.join(custom_folder_path, file_name)
					new_file_path = os.path.join(item_folder_path, file_name)
					shutil.move(file_path, new_file_path)
			else:	
				os.rename(custom_folder_path,item_folder_path)
			try:
				os.rmdir(custom_folder_path)
			except OSError:
				pass
		
		for filename in files:
				
			#Iterates through every file
			file_path = os.path.join(root,filename)
			
			#Checks if file ends with
			if file_path.endswith('pack.mcmeta'):
				change_pack_format(file_path, target_version)
			
			#Changes json file structure
			if file_path.endswith('.json'):
				change_json(file_path, target_version)
			
		
			
	shutil.make_archive(f'{folder_path} {versions[str(target_version)].replace("1.15","1.16")}', 'zip', folder_path)		
	print("Successfully Modified File")

#Changes the pack format of the file
def change_pack_format(file_path , target_version):
	with open(file_path,'r') as data:
		pack_meta = json.load(data)
		pack_meta["pack"]["pack_format"] = target_version
	with open(file_path,'w') as data:	
		json.dump(pack_meta,data,indent=4,ensure_ascii=False)

def change_json(file_path,target_version):
	with open(file_path,'r') as file:
		data = file.read()
	
	with open(file_path,'w') as file:
		file.write(data.replace('custom/','item/'))

resourcepack = input("Input Resourcepack FileName: ")
for idx,packformat in enumerate(list(versions.keys())):
	change_version(resourcepack,int(packformat))
