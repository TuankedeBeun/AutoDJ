from analysis_functions import data_analysis
from tabulate import tabulate

# Analyse song
csv_known = r"C:\Users\tuank\Programming\Python\AutoDJ\analysis\songtester\data\analysis_testfolder_lead.csv"
csv_computed = r"C:\Users\tuank\Programming\Python\AutoDJ\analysis\analyser\data\analysis_testfolder12Feb2023T1658.csv"
results = data_analysis(csv_known, csv_computed)

table = [
    ['drop start', results['drop_start']['mean'], results['drop_start']['stdev']],
    ['drop end', results['drop_end']['mean'], results['drop_end']['stdev']],
    ['key', results['key']['mean'], results['key']['stdev']]
]
print('')
print(tabulate(table, headers=('property', 'mean', 'st. dev.'), tablefmt='simple_grid'))
print('')
