import webarchive, bs4
from ProjectUtils import ensure_dir,get_webarchive_file_names,parse_webarchive_as_df,prepare_csv

ensure_dir('data/')

files = get_webarchive_file_names()

data = {'person':[],'data':[],'taxes':[]}

for file in files:
    df,taxes = parse_webarchive_as_df('data/'+file)
    data['data'].append(df)
    data['person'].append(file.rstrip('.webarchive'))
    data['taxes'].append(taxes)

print(data)

prepare_csv(data)