import os
from helper_functions import split_and_rename, remove_first_four_chars, contains_all_elements, shift_choices, conditional_lowercase
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import math



# Permanently changes the pandas settings
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
# pd.set_option('display.max_colwidth', -1)



def input_excel(file_path):
    """
    Processes an Excel file to handle merged cells and split questions into separate rows,
    then organizes the data into two categories based on question number.

    Args:
    file_path (str): The file path of the Excel file to be processed.

    Returns:
    df: A dataframe with three columns ('Voter-ID', 'Region 1' and 'Region 2').
    """
    # Load the Excel file without headers
    df = pd.read_excel(file_path, header=None)

    column_names = ['Voter-ID', 'Region 1', 'Region 2']
    # Check if the number of column names matches the number of columns in the DataFrame
    if len(column_names) == df.shape[1]:
        # Assign new column names
        df.columns = column_names

    # Check for merged cells in the first column
    if df.iloc[0::2, 0].isna().any():
        # If found, fill NaNs with the value from the previous row (unmerge cells)
        df.iloc[:, 0] = df.iloc[:, 0].fillna(method='ffill')

    # # Check if questions are combined in the same cell in the second column
    # if df.iloc[:, 1].str.contains('Question No. 1').any() and df.iloc[:, 1].str.contains('Question No. 2').any():
    #     # If found, split the combined questions into separate rows
    #     new_rows = []
    #     for index, row in df.iterrows():
    #         q1, q2 = row[1].split('\n', 1)
    #         new_rows.append([row[0], q1.strip()])
    #         new_rows.append([row[0], q2.strip()])
    #     df = pd.DataFrame(new_rows, columns=df.columns)
    #
    #     # Filter and organize the data by question number
    #     question1 = df[df.iloc[:, 1].str.startswith('Question No. 1')]
    #     question2 = df[df.iloc[:, 1].str.startswith('Question No. 2')]
    # else:
    #     # If the questions are not combined, directly filter the data by question number
    #     question1 = df[df.iloc[:, 1].str.startswith('Question no1')]
    #     question2 = df[df.iloc[:, 1].str.startswith('Question no2')]
    #
    # # Create and return the output dictionary containing the organized data
    # output = {
    #     'Region 1': question1,
    #     'Region 2': question2
    # }
    return df

def clean_up_dataframe(df, consider_invalid=False):
    """
    Cleans up the DataFrame by processing voting data, removing certain entries,
    and optionally considering invalid votes.

    Args:
    df (pd.DataFrame): DataFrame containing the voting data.
    consider_invalid (bool): Flag to determine whether to consider invalid votes.

    Returns:
    tuple: A tuple containing the cleaned DataFrame, total votes, count of 'no good candidate' votes,
           and count of invalid votes.
    """

    # Step 1: Remove everything before the first '[' in column 1
    df['Processed'] = df.iloc[:, 1].str.extract(r'(\[.*$)')
    all_votes = len(df['Processed'])

    # Step 2: Remove empty rows (rows representing 'no good candidates')
    no_good_candidate_count = df['Processed'].isna().sum()
    df = df.dropna(subset=['Processed'])

    # Step 3: Split the column with '>' and rename the columns
    split_df = df['Processed'].apply(split_and_rename)

    # Step 4: Remove the first four characters (the letters) from each cell
    split_df = split_df.apply(remove_first_four_chars)

    # List of strings to convert to lowercase
    strings_to_lowercase = ['no good candidate']

    # Apply the function to each column in the dataframe
    for col in split_df.columns:
        split_df[col] = split_df[col].apply(lambda row: conditional_lowercase(row, strings_to_lowercase))
    # print(split_df)

    # Step 5: Get all candidate names by concatenating values and finding unique ones
    all_values = pd.concat([split_df[col] for col in split_df.columns])
    all_names = all_values.unique().tolist()

    # Filter out 'no good candidate' entries and NaN values
    only_candidate_names = [item for item in all_names if
                            isinstance(item, str) and 'no good candidate' not in item.lower()]

    # Combine the original DataFrame with the processed split DataFrame
    final_df = pd.concat([df.iloc[:, :-1], split_df], axis=1)

    # Step 6: Remove entries with 'no good candidate' in the first choice
    no_good_candidate_count += len(final_df[final_df['choice_1'].str.lower().str.startswith('no good')])
    final_df = final_df.drop(final_df[final_df['choice_1'].str.lower().str.startswith('no good')].index)

    # Step 7 (optional): remove invalid votes
    if consider_invalid == False:
        initial_row_count = len(final_df)

        # Drop rows that do not contain all candidate names
        final_df = final_df[final_df.apply(lambda row: contains_all_elements(row, only_candidate_names), axis=1)]

        # Calculate the number of invalid votes dropped
        invalid_votes = initial_row_count - len(final_df)
    else:
        # final_df.fillna('no good candidate', inplace=True)

        invalid_votes = 0

    # Step 8: streamline use of no good candidate


    return final_df, all_votes, no_good_candidate_count, invalid_votes


def instant_runoff_voting(clean_votes):
    """
    Conducts an Instant-Runoff Voting (IRV) process on a DataFrame of ranked voting data.

    Args:
    clean_votes (pd.DataFrame): DataFrame containing ranked voting data.

    Returns:
    tuple: A tuple containing the winner's name, detailed information about each round,
           and the total number of rounds conducted.
    """

    # Extract only the columns with voting choices (assuming first two columns are not choices)
    votes_df = clean_votes.iloc[:, 2:]
    print(votes_df.iloc[:, 0].unique())

    rounds_info = []  # To store information about each round
    round_number = 0  # Initialize round counter

    while True:
        round_number += 1
        # Count the first-choice votes for each candidate
        first_choices = votes_df.iloc[:, 0].value_counts()

        # Record the vote counts for this round
        rounds_info.append({'Round': round_number, 'Votes': first_choices.to_dict(), 'Eliminated': 'None'})

        # Check if a candidate has more than 50% of the votes
        if (first_choices / first_choices.sum()).max() > 0.5:
            winner = first_choices.idxmax()  # Identify the winner
            return winner, rounds_info, round_number

        # If no winner, find the candidate with the least votes
        least_votes_candidate = first_choices.idxmin()

        # Record the candidate's elimination
        rounds_info[-1]['Eliminated'] = least_votes_candidate

        # Update the DataFrame to remove the eliminated candidate and shift choices leftward
        votes_df = votes_df.apply(lambda row: shift_choices(row, least_votes_candidate), axis=1, result_type='expand')

    return "No winner found", rounds_info, round_number


def plot_instant_runoff_results(rounds_info,store_path, region, invalid_specifier):
    """
    Generates visualizations for Instant-Runoff Voting results, including a horizontal stacked bar chart
    and a series of pie charts for each round of voting.

    Args:
    rounds_info (list of dicts): A list containing vote counts and eliminated candidates for each round.
    region (str): The name of the region, used for labeling the output files.
    """

    # Convert rounds_info to a DataFrame for easy plotting
    rounds_df = pd.DataFrame([round['Votes'] for round in rounds_info])
    rounds_df.fillna(0, inplace=True)  # Replace NaN with 0 for plotting

    # Set up the plot parameters
    num_rounds = len(rounds_df)
    candidates = rounds_df.columns
    colors = plt.cm.viridis_r(np.linspace(0, 1, len(candidates)))  # Assign colors to candidates

    # Create a horizontal stacked bar chart
    plt.figure(figsize=(15, 8))

    ax = rounds_df.plot(kind='barh', stacked=True, color=colors, legend=False)
    plt.title(f'Considered Votes per Candidate per Counting Round in {region}')
    plt.ylabel('Counting')
    plt.xlabel('Number of Votes')


    # Draw a dashed line indicating the 50% vote threshold
    '''If accounting for invalid votes, this threhsold might change, because some voters might only have voted for 
    one eliminated candidate and thus have no vote regarding the remaining set of candidates'''

    half_votes = rounds_df.sum(axis=1) * 0.5
    for i in half_votes.index:
        label = '50% (required simple majority)' if i == 0 else None
        plt.plot([half_votes[i],half_votes[i]],[i-0.5,i+0.5],color='grey', linestyle='--', label=label, alpha=0.7)

    # Position the legend outside the plot
    plt.yticks(range(num_rounds), ['Round ' + str(i + 1) for i in range(num_rounds)], rotation=0)

    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)
    plt.tight_layout()
    plt.savefig(f'{store_path}/{region}_Votes_BarChart_{invalid_specifier}.png')

    # # Set up a grid of subplots for pie charts
    # cols = 3  # Max number of columns
    # rows = math.ceil(num_rounds / cols)  # Calculate the number of rows needed
    # fig, axes = plt.subplots(rows, cols, figsize=(15, 6 * rows))
    # axes = axes.flatten()  # Flatten axes for easy iteration
    #
    # # Create a pie chart for each round
    # for i in range(num_rounds):
    #     round_data = rounds_df.iloc[i]
    #     round_data = round_data[round_data > 0]  # Exclude candidates with 0 votes
    #     axes[i].pie(round_data, labels=None, autopct='%1.1f%%', colors=colors, startangle=140)
    #     axes[i].set_title(f'Round {i + 1}')
    #
    # # Hide any unused subplots
    # for j in range(i + 1, len(axes)):
    #     axes[j].axis('off')
    #
    # # Create a legend for the pie charts
    # fig.legend(rounds_df.columns, title='Candidates', loc='center left', bbox_to_anchor=(1, 0.5))
    #
    # plt.suptitle(f'Vote Share per Round in {region}')
    # plt.subplots_adjust(right=0.7)
    # plt.tight_layout()
    # fig.savefig(f'{store_path}/{region}_Votes_PieCharts_{invalid_specifier}.png')

def plot_test_eligibility(vote_dict,store_path, region, invalid_specifier):
    """
    Generates a pie chart visualization for vote categories in a specified region.

    Args:
    vote_dict (dict): A dictionary with keys as vote categories and values as their counts.
    region (str): The name of the region for which the pie chart is generated.

    The function saves the generated pie chart as a PNG file.
    """

    # Assign different colors for each vote category
    colors = plt.cm.viridis_r(np.linspace(0, 1, len(vote_dict.keys())))

    # Create a DataFrame from the vote dictionary for easy plotting
    chart_df = pd.DataFrame(vote_dict, index=[0])

    # Create a figure for the pie chart
    plt.figure()
    # Generate the pie chart using the flattened values of the DataFrame
    plt.pie(chart_df.values.flatten(), colors=colors, labels=chart_df.columns, autopct='%1.1f%%', startangle=140)
    # Set the title of the pie chart including the total number of votes
    plt.title(f"Vote Validity in {region} ({chart_df.values.flatten().sum()})")
    plt.tight_layout()

    # Save the pie chart as a PNG file
    plt.savefig(f'{store_path}/{region}_Validity_Votes_PieCharts_{invalid_specifier}.png')

def run_instant_runoff(file_path,store_path, consider_invalid=False):
    """
    Executes the Instant-Runoff Voting process for a given Excel file. This includes data processing,
    running the IRV algorithm, plotting results, and saving the data and plots.

    Args:
    file_path (str): Path to the Excel file containing voting data.
    consider_invalid (bool): Flag to determine whether to consider invalid votes.

    The function saves the results as Excel files and plots as images for each region in the dataset.
    """
    if consider_invalid:
        invalid_specifier = 'with_invalid'
    else:
        invalid_specifier = 'without_invalid'
    # Process the Excel file to obtain voting data
    input_df = input_excel(file_path)

    # Iterate through each region in the processed data
    for region in input_df.columns[1:]:
        # Clean up and prepare the DataFrame for IRV
        final_df, all_votes, no_good_candidate_count, invalid_votes = clean_up_dataframe(input_df[['Voter-ID', region]], consider_invalid)

        # Create a dictionary for vote categories and their counts
        vote_dict = {
            f'valid votes ({all_votes - no_good_candidate_count - invalid_votes})': all_votes - no_good_candidate_count - invalid_votes,
            f'no good candidates ({no_good_candidate_count})': no_good_candidate_count,
            f'invalid votes ({invalid_votes})': invalid_votes
        }

        # Plot the eligibility of votes (valid, no good candidates, invalid)
        plot_test_eligibility(vote_dict,store_path, region, invalid_specifier)

        # Run the Instant-Runoff Voting algorithm
        winner, rounds_info, total_rounds = instant_runoff_voting(final_df)

        # Save the vote validity and IRV results to Excel files
        vote_validity = pd.DataFrame(vote_dict, index=[0])
        vote_validity.to_excel(f'{store_path}/{region}_validity_vote.xlsx')

        elim_df = pd.DataFrame([round['Eliminated'] for round in rounds_info])
        rounds_df = pd.DataFrame([round['Votes'] for round in rounds_info])
        rounds_df['Eliminated'] = elim_df
        rounds_df['Elimination Round'] = range(1, len(rounds_df) + 1)
        rounds_df.to_excel(f'{store_path}/{region}_votes{invalid_specifier}.xlsx')

        # Plot the results of each round of Instant-Runoff Voting
        plot_instant_runoff_results(rounds_info,store_path, region, invalid_specifier)


