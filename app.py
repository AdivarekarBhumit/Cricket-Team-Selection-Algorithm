import numpy as np
import pandas as pd
import pickle as pb
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

batsman_cols = ['Matches_Played', 'Not_Out', 'Hundreds', 'Fifties', 'Sixes', 'Fours', 'Highest_Score', 'Total_Runs', 'Avg', 'Balls_Faced', 'Strike_Rate']
bowlers_cols = ['MP', 'BB', 'R', 'W', '5WI', '10WM', 'Avg', 'SR', 'Econ']

def get_batsman_score(rfr_batsman, df):
    
    def get_score(df):
        attributes = df[batsman_cols].values
        pred = rfr_batsman.predict(attributes)
        return pred
    
    df['score'] = get_score(df)
    columns = ['Player_Name', 'Matches_Played', 'Not_Out', 'Hundreds', 'Fifties', 'Sixes', 
           'Fours', 'Highest_Score', 'Total_Runs', 'Avg', 'Balls_Faced', 'Strike_Rate', 'score']
    top_class = df.where(df['score'] > df['score'].mean() + 160).dropna()
    middle_class = df.where(df['score'] >= df['score'].mean() + 70).where(df['score'] <= df['score'].mean() + 160).dropna()
    low_class = df.where(df['score'] < df['score'].mean() + 70).dropna()
    
    top_class['Difference_avg_score'] = top_class['score'] - top_class['Avg']
    middle_class['Difference_avg_score'] = middle_class['score'] - middle_class['Avg']
    low_class['Difference_avg_score'] = low_class['score'] - low_class['Avg']
    
    x = top_class.where(top_class['Difference_avg_score'] > 100).where(top_class['Difference_avg_score'] < 300).dropna().sort_values(by='Avg', ascending=False).sample(2)
    y = middle_class.where(middle_class['Difference_avg_score'] > 200).where(middle_class['Difference_avg_score'] < 300).dropna().sort_values(by='Avg', ascending=False).sample(3)
    z = low_class.where(low_class['Difference_avg_score'] > 100).where(low_class['Difference_avg_score'] < 300).dropna().sort_values(by='Avg', ascending=False).sample(1)
    
    return pd.concat([x, y, z])


def get_bowler_score(rfr_bowler, df):
    
    def get_score(df):
        attributes = df[bowlers_cols].values
        pred = rfr_bowler.predict(attributes)
        return pred
    
    df['score'] = get_score(df)

    top_class = df.where(df['score'] > df['score'].mean() + 50).dropna()
    middle_class = df.where(df['score'] > df['score'].mean()).where(df['score'] <= df['score'].mean() + 50).dropna()
    low_class = df.where(df['score'] <= df['score'].mean()).dropna()

    # Players Selection
    a = top_class.sample(2)
    b = middle_class.sample(2)
    c = low_class.sample(1)

    return pd.concat([a,b,c])

def load_models():
    # Random Forest Models for both batsman and bowler
    with open('./models/random_forest_regressor_batsman.pb', 'rb') as f:
        rfr_batsman = pb.load(f)
    
    with open('./models/random_forest_regressor_bowlers.pb', 'rb') as f:
        rfr_bowler = pb.load(f)
    
    return rfr_batsman, rfr_bowler


def filename_validation(filename, batsman = True):
    status = None 
    path = None
    if batsman:
        if 'xlsx' in str(filename):
            path = './temp/batsman.xlsx'
            filename.save(path)
            status = True
        elif 'csv' in str(filename):
            path = './temp/batsman.csv'
            filename.save(path)
            status = True
        else:
            status = False
    else:
        if 'xlsx' in str(filename):
            path = './temp/bowler.xlsx'
            filename.save(path)
            status = True
        elif 'csv' in str(filename):
            path = './temp/bowler.csv'
            filename.save(path)
            status = True
        else:
            status = False

    return status, path


@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html')

@app.route('/results', methods=['POST', 'GET'])
def results():
    batsman_file_path = request.files['batsman']
    bowler_file_path = request.files['bowler']
    bat_status, bat_path = filename_validation(batsman_file_path, batsman=True)
    bowl_status, bowl_path = filename_validation(bowler_file_path, batsman=False)
    # print(bat_path, bowl_path)
    if 'csv' in bat_path:
        batsman = pd.read_csv(bat_path)
    else:
        batsman = pd.read_excel(bat_path)
    if 'csv' in bowl_path:
        bowler = pd.read_csv(bowl_path)
    else:
        bowler = pd.read_excel(bowl_path)

    rfr_batsman, rfr_bowler = load_models()
    new_bat_cols = ['Player_Name', 'Matches_Played', 'Not_Out',
       'Hundreds', 'Fifties', 'Sixes', 'Fours', 'Highest_Score', 'Total_Runs',
       'Avg', 'Balls_Faced', 'Strike_Rate']
    
    new_bowl_cols = ['Player', 'MP', 'BB', 'R', 'W', '5WI', '10WM',
                    'Avg', 'SR', 'Econ']
    # new_bowl_cols = 
    best_batsman = get_batsman_score(rfr_batsman, batsman)
    best_bowler = get_bowler_score(rfr_bowler, bowler)
    best_batsman = best_batsman[new_bat_cols]
    best_bowler = best_bowler[new_bowl_cols]
    # print(best_batsman.values.tolist())
    # print(best_bowler.columns)
    # print(best_batsman.columns)
    # print(best_bowler.values.tolist())

    return render_template('results.html', bat_status=bat_status, bowl_status=bowl_status, best_bat = best_batsman.values.tolist(), best_bowl = best_bowler.values.tolist())

if __name__ == "__main__":
    app.run(debug=True)
