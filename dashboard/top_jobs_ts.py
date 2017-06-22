# coding: utf-8

import datetime
import os
import json

import pandas
import numpy as np

try:
    import tzlocal
except Exception as e:
    os.system('pip install tzlocal')
    import tzlocal

try:
    from flask import Flask, request,render_template
    from flask import Response
except Exception as e:
    os.system('pip install flask')
    from flask import Flask,request,render_template
    from flask import Response

try:
    from flask_cors import CORS
except Exception as e:
    os.system('pip install flask_cors')
    from flask_cors import CORS
    
from sklearn.ensemble import ExtraTreesClassifier


app = Flask(__name__)
CORS(app)

global df
df = pandas.read_csv("./test_30day.csv")
print("File loaded.")

"""
This method is used to convert the columns with dtype object
into numerical data types
"""
def categorical(input_):

    transform_cols = list()
    col_dtype_dict = input_.dtypes.to_dict()
    for key in col_dtype_dict:
        if col_dtype_dict[key] == 'object':
            try:
                input_[key] = pandas.to_datetime(input_[key])
                del input_[key]
            except Exception as e:
                print("*********",key)
                input_[key] = input_[key].apply(lambda x : sum(bytearray(str(x).encode('utf-8'))))
    return input_

@app.route('/GetBarGraph', methods=['GET'])
def getBarGraph():
    passed = list()
    failed = list()
    data = dict()

    df_testRuns = df.groupby(["job_name", "pass"])["test_name"].nunique()
    df_testRuns.reset_index(name='test_name_counts').to_string(index=False)
    
    # job _name, test_counts dictionary  
    df_dict = df_testRuns.to_dict()
    for key in df_dict:
        print(key)
        if key[1] == 1:
            passed.append({'x' : key[0], 'y' : int(df_dict[key])})
        elif key[1] == 0:
            failed.append({'x' : key[0], 'y' : int(df_dict[key])})

    data['Passed Tests'] = passed
    data['Failed Tests'] = failed
    
    return Response(json.dumps(data), mimetype='application/json')

def getdate(date_):
    unix_timestamp = float(str(date_))
    local_timezone = tzlocal.get_localzone() # get pytz timezone
    local_time = datetime.datetime.fromtimestamp(unix_timestamp, local_timezone)
    
    return local_time.strftime("%Y-%m-%d")
@app.route('/GetBarGraph1', methods=['GET'])
def getBarGraph1():
    
    passed = list()
    failed = list()
    data = dict()

    start_date = float(request.args.get('start'))
    end_date = float(request.args.get('end'))
##    print(start_date.dtype)
##    df["start_time"] = pandas.to_datetime(df["start_time"])
##    df["end_time"] = pandas.to_datetime(df["end_time"])

    print(df["start_time"].dtype)
    new_df = df[(df["start_time"] >= start_date) & (df["end_time"] <= end_date)]
    
##    df = df.loc[mask]
    print('-----------',new_df.shape)
    df_testRuns = new_df.groupby(["job_name", "pass"])["test_name"].nunique()
    df_testRuns.reset_index(name='test_name_counts').to_string(index=False)
    
    # job _name, test_counts dictionary  
    df_dict = df_testRuns.to_dict()
    for key in df_dict:
        print(key)
        if key[1] == 1:
            passed.append({'x' : key[0], 'y' : int(df_dict[key])})
        elif key[1] == 0:
            failed.append({'x' : key[0], 'y' : int(df_dict[key])})

    data['Passed Tests'] = passed
    data['Failed Tests'] = failed
    
    return Response(json.dumps(data), mimetype='application/json')

@app.route('/GetBarGraph', methods=['POST'])
def getBarGraphWithDates():
    print('***********', df.shape)
    start_date = datetime.datetime.strptime(request.form['dateFrom'], '%Y-%m-%d').timestamp()
    end_date = datetime.datetime.strptime(request.form['dateTo'], '%Y-%m-%d').timestamp()
    print(start_date, '---', end_date)
    return render_template('BarGraph.html', start=start_date, end=end_date)


@app.route('/FeatureSelection', methods=['GET'])
def getRelevantFeatures():
    df["runtime"] = df["end_time"] - df["start_time"]
    print(df["test_name"].unique().shape)
    X = df.copy(deep=True)
    del X["pass"]
    Y = df["pass"]
    del X["git_hash"]
    X = categorical(X)
    # feature extraction - see if a particular setting is really useful for the unit testing for success and failure differentiate
    model = ExtraTreesClassifier()
    model.fit(X, Y)
    print(X.shape, Y.shape, df.shape)
    print(model.feature_importances_)
    print(np.argpartition(model.feature_importances_, -4)[-4:])
    
    
@app.route('/GetData', methods=['GET'])
def GetData():
    df["runtime"] = df["end_time"] - df["start_time"]

    #for success see which combinations are giving fastest run time for a test
    #find run time for each test type and
    # cluster total number of different tests run in last 30 days
    # show total number of successfull passes and failures
    # show different number of pass and failure for each test
    # show which feature is of highest importance for failed once
    # show which feature is of highest relevance for fastest run time
    # for a particular range how did the features change for the test
    # what were the values of the feature during that change
    
    
    means = df.groupby(["git_branch","job_name","ncpu","test_name"])["runtime"].mean()
    std = df.groupby(["git_branch","job_name","ncpu","test_name"])["runtime"].std()
    df2 = df.set_index(["git_branch","job_name","ncpu","test_name"]).join(means,how="inner",rsuffix="_mean").join(std, how="inner",rsuffix="_std")
    df2["zscore"] = (df2["runtime"] - df2["runtime_mean"])/df2["runtime_std"]
    df2 = df2.reset_index()
    df2 = df2.sort_values(["git_branch","job_name","ncpu","test_name","end_time"])
    ends = df2.groupby(["git_branch","job_name","ncpu","test_name"])["zscore"]
    last = ends.last().abs() 
    print('************',last.head(10))
    last.sort_values(ascending=False)
    df3 = df2.set_index(["git_branch","job_name","ncpu","test_name"]).join(last.head(25), rsuffix="top_zscores", how="left")
    final = df3[df3["zscoretop_zscores"].notnull()]
    final = final.reset_index()
    print(final.shape)
    final = final.drop(["zscoretop_zscores","runtime_std"],axis=1)
    #final["end_time"] = pandas.to_datetime(final["end_time"]).apply(lambda x:x.timestamp())
    global count 
    count = 1
    def genJSON(df):
        global count
        df2 = df.set_index(["git_branch","job_name","ncpu","test_name"]) 
        jsonStr = '"' + str(count) + '"' + ':{"key":"' + " ".join([str(x) for x in df2.index[0]]) + '",'
        jsonStr += '"values":' + df2[["end_time","zscore","runtime_mean"]].to_json(orient="records") + '}'
        count += 1
        return jsonStr
    jsonStr = final.groupby(["git_branch","job_name","ncpu","test_name"]).apply(lambda x: genJSON(x)).values
    jsonStrFinal = '{' + ",".join(jsonStr) + "}"
    print(jsonStrFinal)
    return Response(jsonStrFinal, mimetype='application/json')

#GetData()

@app.route('/')
def root():
    return app.send_static_file('index.html'), app.send_static_file('multiBarGraph.html')


if __name__ == "__main__":
    app.run(debug=True)


