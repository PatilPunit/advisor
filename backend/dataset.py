import pandas as pd

carreer_data = pd.read_csv('/home/punit/Downloads/Mint/AI_career_advisor/dataset/career_paths.csv')
project_data=pd.read_csv('/home/punit/Downloads/Mint/AI_career_advisor/dataset/project_bank.csv')
skill_data=pd.read_csv("/home/punit/Downloads/Mint/AI_career_advisor/dataset/skill_roadmap.csv")
print(carreer_data.head())
print(project_data.head())
print(skill_data.head())