from recommender import recommend_career
from roadmap import print_roadmap
career_name = "cybersecurity analyst"
print_roadmap(career_name)
skills = ["Python", "Pandas"]
interest = career_name

result = recommend_career(skills, career_name,top_n=10)[0]

print(f"Career: {result['career']}")
print(f"Match Score: {result['match_percent']}%")
print("Missing Skills:")
for skill in result['missing_skills']:
    print(f"  - {skill}")