import pandas as pd
import json
import glob
import os

CONTRIBUTION_TYPE = {
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

def open_json(path):
    with open(path) as f:
        return json.load(f)

class CommitteeCleaner:
    def __init__(self):
        return
        
    def clean(self,
               out_path=os.path.join('clean', 'committees'), 
               raw_directory=os.path.join('raw', 'committees')
            ):
        summary_paths = glob.glob(os.path.join(
            raw_directory, '*-summary.json'))
        contribution_paths = glob.glob(os.path.join(
            raw_directory, '*-contributions-itemized.json'))
        expenditure_paths = glob.glob(os.path.join(
            raw_directory, '*-expenditures-itemized.json'))
        
        summaries = []
        for file in summary_paths:
            summary = open_json(file)
            summary['committeeName'] = summary['committeeName'].strip()
            summaries.append(dict(summary))

        contributions = pd.DataFrame()
        for file in contribution_paths:
            dfi = pd.read_json(file, orient='records')
            contributions = pd.concat([contributions, dfi])

        contributions['Committee'] = contributions['Committee'].str.strip()
        contributions['type'] = contributions['Contribution Type'].replace(
            CONTRIBUTION_TYPE)

        expenditures = pd.DataFrame()
        for file in expenditure_paths:
            dfi = pd.read_json(file, orient='records')
            expenditures = pd.concat([expenditures, dfi])

        expenditures['Committee'] = expenditures['Committee'].str.strip()

        # Write out
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        contributions.to_csv(os.path.join(
            out_path, 'contributions.csv'), index=False)
        expenditures.to_csv(os.path.join(
            out_path, 'expenditures.csv'), index=False)
        with open(os.path.join(out_path, 'summary.json'), 'w') as f:
            f.write(json.dumps(summaries))
            print(f'Cleaned data written to {out_path}')

class CandidateCleaner:
    def __init__(self):
        return
        
    def clean(self,
               out_path=os.path.join('clean', 'committees'), 
               raw_directory=os.path.join('raw', 'committees')
            ):
        summary_paths = glob.glob(os.path.join(
            raw_directory, '*-summary.json'))
        contribution_paths = glob.glob(os.path.join(
            raw_directory, '*-contributions-itemized.json'))
        expenditure_paths = glob.glob(os.path.join(
            raw_directory, '*-expenditures-itemized.json'))
        
        summaries = []
        for file in summary_paths:
            summary = open_json(file)
            summary['candidateName'] = summary['candidateName'].strip()
            summaries.append(dict(summary))

        contributions = pd.DataFrame()
        for file in contribution_paths:
            dfi = pd.read_json(file, orient='records')
            contributions = pd.concat([contributions, dfi])

        if len(contributions) > 0:
            contributions['Candidate'] = contributions['Candidate'].str.strip()
            contributions['type'] = contributions['Contribution Type'].replace(
                CONTRIBUTION_TYPE)

        expenditures = pd.DataFrame()
        for file in expenditure_paths:
            dfi = pd.read_json(file, orient='records')
            expenditures = pd.concat([expenditures, dfi])

        if len(expenditures) > 0:
           expenditures['Candidate'] = expenditures['Candidate'].str.strip()

        # Write out
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        contributions.to_csv(os.path.join(
            out_path, 'contributions.csv'), index=False)
        expenditures.to_csv(os.path.join(
            out_path, 'expenditures.csv'), index=False)
        with open(os.path.join(out_path, 'summary.json'), 'w') as f:
            f.write(json.dumps(summaries))
            print(f'Cleaned data written to {out_path}')
        

