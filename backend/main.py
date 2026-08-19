from recommender import recommend_career
from roadmap import print_roadmap

print_roadmap("Data Scientist")
skills = ["Python", "Pandas"]
interest = "Data Science"

result = recommend_career(skills, interest, top_n=1)[0]

print(f"Career: {result['career']}")
print(f"Match Score: {result['match_percent']}%")
print("Missing Skills:")
for skill in result['missing_skills']:
    print(f"  - {skill}")