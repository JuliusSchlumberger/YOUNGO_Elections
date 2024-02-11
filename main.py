from evaluation import run_instant_runoff

file_path = 'YOUNGO_Votes_2024_GN.xlsx'
store_path = '2024_GN'
run_instant_runoff(file_path,store_path, consider_invalid=True)