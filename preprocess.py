import pandas as pd
query = pd.read_csv(r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\At the margins\queries.csv")
query['French']=query['French'].str.split(';')
query = query.explode(column='French')

        
query['French'] = query['French'].str.replace('(', r'\(', regex=False)
query['French'] = query['French'].str.replace(')', r'\)\s', regex=False)
query.to_csv(r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\At the margins\queries_simple.csv")


