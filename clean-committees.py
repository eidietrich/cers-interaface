import pandas as pd
import json
import os
import glob

YEAR = '2022'


def open_json(path):
    with open(path) as f:
        return json.load(f)


def clean_committees():
    summary_paths = glob.glob(os.path.join(
        'raw', 'committees/*-summary.json'))
    contribution_paths = glob.glob(os.path.join(
        'raw', 'committees/*-contributions-itemized.json'))
    expenditure_paths = glob.glob(os.path.join(
        'raw', 'committees/*-expenditures-itemized.json'))

    summaries = []
    for file in summary_paths:
        summary = open_json(file)
        summary['committeeName'] = summary['committeeName'].strip()
        summaries.append(dict(summary))

    contributions = pd.DataFrame()
    for file in contribution_paths:
        dfi = pd.read_json(file, orient='records')
        contributions = contributions.append(dfi)

    contributions['Committee'] = contributions['Committee'].str.strip()
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

    expenditures['Committee'] = expenditures['Committee'].str.strip()

    # Write to /cleaned
    out_path = os.path.join('cleaned', 'committees')
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    contributions.to_csv(os.path.join(
        out_path, 'contributions.csv'), index=False)
    expenditures.to_csv(os.path.join(
        out_path, 'expenditures.csv'), index=False)
    with open(os.path.join(out_path, 'summary.json'), 'w') as f:
        f.write(json.dumps(summaries))
        print(f'Cleaned data written to {out_path}')


clean_committees()
