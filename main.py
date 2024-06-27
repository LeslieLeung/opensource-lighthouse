import jinja2
import pandas as pd

from github import Github
from github import Auth
from github.GithubException import UnknownObjectException
import argparse

# create parser
parser = argparse.ArgumentParser(
    description="Fetch data from GitHub and generate README."
)
parser.add_argument(
    "--skip-fetch", action="store_true", help="Skip fetching data from GitHub"
)
parser.add_argument("--auth-token", type=str, help="GitHub personal access token")

# parse arguments
args = parser.parse_args()

path_to_teams = "data/teams.csv"
path_to_repos = "data/repos.csv"

# load teams from csv
data_teams = pd.read_csv(path_to_teams)
data_repos = pd.read_csv(path_to_repos, dtype={"id": str})

teams = data_teams["name"].values
team_to_company = data_teams.set_index("name")["company"].to_dict()

# for each team, fetch repos
if args.auth_token is not None:
    auth = Auth.Token(args.auth_token)
    g = Github(auth=auth)
else:
    g = Github()
if not args.skip_fetch:
    for team in teams:
        try:
            org = g.get_organization(team)
        except UnknownObjectException:
            print(f"Team {team} not found")
            continue

        repos = org.get_repos()
        print(f"Fetched {len(list(repos))} repos for {team}")
        for repo in repos:
            repo_info = {
                "id": str(repo.id),
                "owner": org.login,
                "repo": repo.name,
                "link": repo.html_url,
                "stars": repo.stargazers_count,
                "license": repo.license.name if repo.license is not None else "-",
                "language": repo.language,
                "created_at": repo.created_at,
                "last_updated_at": repo.updated_at,
                "company": team_to_company[team],
            }
            # check if repo id already exists
            if repo.id in data_repos["id"].values:
                # update repo
                for key, value in repo_info.items():
                    data_repos.loc[data_repos["id"] == repo_info["id"], key] = value
            else:
                # add repo
                data_repos = pd.concat(
                    [data_repos, pd.DataFrame([repo_info])], ignore_index=True
                )

# save to csv
data_repos.to_csv(path_to_repos, index=False)

# render readme
env = jinja2.Environment(loader=jinja2.FileSystemLoader("./template"))
template = env.get_template("readme_zh.tmpl")
teams = data_teams.to_dict(orient="records")
# read from dataframe
"""
owner,repo,link,stars,license,language,created_at,last_updated_at,company

{% for company in companies -%}
## {{ company.name }}
| 项目 | 语言 | star | 协议 | 创建时间 | 最后更新时间 |
| --- | --- | --- | --- | --- | --- |
{% for project in company.projects -%}
| [{{ project.name }}]({{ project.url }}) | {{ project.language }} | {{ project.star }} | {{ project.license }} | {{ project.created_at }} | {{ project.updated_at }} |
{% endfor %}
{% endfor %}
"""
companies = []
for company, group in data_repos.groupby("company"):
    projects = group.to_dict(orient="records")
    companies.append({"name": company, "projects": projects})

# stats
total_repos = data_repos.shape[0]
total_companies = len(companies)
total_teams = len(teams)
time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

output = template.render(
    total_repos=total_repos,
    total_companies=total_companies,
    total_teams=total_teams,
    time=time,
    teams=teams,
    companies=companies,
)

# write to file
with open("README.md", "w") as f:
    f.write(output)
