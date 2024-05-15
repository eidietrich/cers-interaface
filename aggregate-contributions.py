import pandas as pd

paths = [
    'cleaned/2024/committees/contributions.csv',
    'cleaned/2024/ag/contributions.csv',
    'cleaned/2024/auditor/contributions.csv',
    'cleaned/2024/gov/contributions.csv',
    'cleaned/2024/leg/contributions.csv',
    'cleaned/2024/opi/contributions.csv',
    'cleaned/2024/psc2/contributions.csv',
    'cleaned/2024/psc3/contributions.csv',
    'cleaned/2024/sos/contributions.csv',
    'cleaned/2024/supco3/contributions.csv',
    'cleaned/2024/supcoChief/contributions.csv',
    'cleaned/2024/supcoClerk/contributions.csv'
]

dtype = {
    'Committee': 'string',
    'Candidate': 'string',
    'Zip': 'string',
    'Entity Name': 'string',
    'First Name': 'string',
    'Last Name': 'string',
}

df = pd.DataFrame()
for path in paths:
    dfi = pd.read_csv(path, dtype=dtype)
    df = pd.concat([df, dfi])

df.fillna("",inplace=True)
df['Recipient'] = df['Committee'] + df['Candidate']
df['Entity Name']
df['Contributor'] = df[['Entity Name', 'First Name', 'Last Name']].apply(lambda x : '{}{} {}'.format(x[0],x[1],x[2]), axis=1)
df['Address'] = df[['Addr Line1', 'City', 'State', 'Zip']].apply(lambda x : '{} {}, {} {}'.format(x[0],x[1],x[2],x[3]), axis=1)

df.to_csv('cleaned/2024/all-contributions.csv', index=False)
