from evaluation import run_instant_runoff

file_path = 'Elections_2023.xlsx'
store_path = 'Outputs'
run_instant_runoff(file_path,store_path, consider_invalid=False)