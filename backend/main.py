from recommender import recommend_career
from roadmap import print_roadmap

career_name = "cybersecurity analyst"
skills = ["Python", "Pandas"]
interest = career_name

results = recommend_career(skills, interest, top_n=3)

for i, result in enumerate(results, start=1):
    print(f"\n#{i} Career: {result['career']}")
    print(f"Match Score: {result['match_percent']}%")
    print(f"Interest Score: {result['interest_score']}%")
    print("Missing Skills:")
    for skill in result['missing_skills']:
        print(f"  - {skill}")

# Roadmap for the top recommended career (not hardcoded)
top_career = results[0]['career']
print(f"\nRoadmap for {top_career}:")
print_roadmap(top_career)