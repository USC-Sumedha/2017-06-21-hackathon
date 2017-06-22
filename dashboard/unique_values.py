import pandas
import pprint
import json

df = pandas.read_csv("./test_30day.csv")
##print(df["test_name"].unique().shape, df["test_name"].shape)
##print(df["job_name"].unique().shape)
##df_testRuns = df.groupby(["job_name", "pass"])["test_name"].nunique()
##df_testRuns.reset_index(name='test_name_counts').to_string(index=False)
##passed = list()
##failed = list()
### job _name, test_counts dictionary
##df_dict = df_testRuns.to_dict()
##for key in df_dict:
##    print(key)
##    if key[1] == 1:
##        passed.append({key[0]: int(df_dict[key])})
##    elif key[1] == 0:
##        failed.append({key[0]: int(df_dict[key])})
##data = dict()
##data['pass'] = passed
##data['fail'] = failed
##print(json.dumps(data))
df["runtime"] = df["end_time"] - df["start_time"]
df2 = df.groupby(["start_time","test_name","ncpu","runtime"]).count()
print(df2.shape)
df2.apply(reset_index(name='test_name_counts')).to_string(index=False)
print(df2)
