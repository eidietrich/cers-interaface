import pandas as pd
import json
import os
import glob

YEAR = '2022'
RACES = [
    'psc',
    'supco'
]


def open_json(path):
    with open(path) as f:
        return json.load(f)


def clean_race(race):
    summary_paths = glob.glob(os.path.join(
        'raw', YEAR, f'{race}*/*-summary.json'))
    contribution_paths = glob.glob(os.path.join(
        'raw', YEAR, f'{race}*/*-contributions-itemized.json'))
    expenditure_paths = glob.glob(os.path.join(
        'raw', YEAR, f'{race}*/*-expenditures-itemized.json'))

    summaries = []
    for file in summary_paths:
        summary = open_json(file)
        summary['candidateName'] = summary['candidateName'].strip()
        summaries.append(dict(summary))

    contributions = pd.DataFrame()
    for file in contribution_paths:
        dfi = pd.read_json(file, orient='records')
        contributions = contributions.append(dfi)

    contributions['Candidate'] = contributions['Candidate'].str.strip()
    contribution_type = {
        1: 'Personal contributions',
        2: 'Unitemized contributions',
        3: 'Loans',
        4: 'Fundraisers & misc',
        5: 'PAC contributions',
        6: 'Political party contributions',
        7: 'Incidental committee contributions',
        8: 'Other political committee contributions',
        9: 'Individual contributions',
    }
    contributions['type'] = contributions['Contribution Type'].replace(
        contribution_type)

    expenditures = pd.DataFrame()
    for file in expenditure_paths:
        dfi = pd.read_json(file, orient='records')
        expenditures = expenditures.append(dfi)

    expenditures['Candidate'] = expenditures['Candidate'].str.strip()

    # Write to /cleaned
    out_path = os.path.join('cleaned', race)
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    contributions.to_csv(os.path.join(
        out_path, 'contributions.csv'), index=False)
    expenditures.to_csv(os.path.join(
        out_path, 'expenditures.csv'), index=False)
    with open(os.path.join(out_path, 'summary.json'), 'w') as f:
        f.write(json.dumps(summaries))
        print(f'Cleaned data written to {out_path}')


for race in RACES:
    clean_race(race)
