from analysis_functions import data_analysis

# Analyse song
csv_known = r"C:\Users\tuank\Programming\Python\AutoDJ\analysis\songtester\data\analysis_testfolder_lead.csv"
csv_computed = r"C:\Users\tuank\Programming\Python\AutoDJ\analysis\analyser\data\analysis_testfolder12Feb2023T1658.csv"
results = data_analysis(csv_known, csv_computed)

print(results)