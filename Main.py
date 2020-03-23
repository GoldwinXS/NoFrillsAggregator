from ProjectUtils import ensure_dir,get_webarchive_file_names,parse_file_as_df,prepare_csv

# ensure that there is a data dir
ensure_dir('data/')

# grab files
files = get_webarchive_file_names()

# assign a dict to keep track of some vars
data = {'person':[],'data':[],'taxes':[]}

# iterate over file names and extract info
for file in files:
    df,taxes = parse_file_as_df('data/' + file)
    data['data'].append(df)
    data['person'].append(file.rstrip('.webarchive.htm'))
    data['taxes'].append(taxes)

# prepare and save the csv
prepare_csv(data)