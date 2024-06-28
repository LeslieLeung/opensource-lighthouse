import jinja2
import pandas as pd

from github import Github
from github import Auth
from github.GithubException import UnknownObjectException
import argparse
import datetime

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
time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
cutoff_date = datetime.datetime.now() - datetime.timedelta(days=180)

# load teams from csv
data_teams = pd.read_csv(path_to_teams)
data_repos = pd.read_csv(
    path_to_repos, dtype={"id": str, "created_at": str, "last_updated_at": str}
)

teams = data_teams["name"].values
team_to_company = data_teams.set_index("name")["company"].to_dict()

total_teams = len(teams)
i = 0

# for each team, fetch repos
if args.auth_token is not None:
    auth = Auth.Token(args.auth_token)
    g = Github(auth=auth)
else:
    g = Github()
if not args.skip_fetch:
    for team in teams:
        i += 1
        print(f"Fetching {i}/{total_teams}: {team}")
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
                "description": repo.description,
                "stars": repo.stargazers_count,
                "license": repo.license.name if repo.license is not None else "-",
                "language": repo.language,
                "created_at": repo.created_at.date().strftime("%Y-%m-%d"),
                "last_updated_at": repo.updated_at.date().strftime("%Y-%m-%d"),
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
readme_template = env.get_template("readme_zh.tmpl")
company_template = env.get_template("company_zh.tmpl")
teams = data_teams.to_dict(orient="records")
# read from dataframe
companies = []
for company, group in data_repos.groupby("company"):
    projects = group.to_dict(orient="records")
    # company wise stats
    total_projects = len(projects)
    total_teams = len(group["owner"].unique())
    total_stars = group["stars"].sum()
    top_3_languages = ", ".join(group["language"].value_counts().head(3).index.tolist())
    # count projects updated within 180 days
    active_projects = len(
        [
            project
            for project in projects
            if datetime.datetime.strptime(project["last_updated_at"], "%Y-%m-%d")
            > cutoff_date
        ]
    )
    company_stats = {
        "total_projects": total_projects,
        "total_teams": total_teams,
        "total_stars": total_stars,
        "top_3_languages": top_3_languages,
        "active_projects": active_projects,
    }

    o = company_template.render(
        company_name=company,
        stat=company_stats,
        projects=projects,
        time=time,
    )
    with open(f"page/{company}.md", "w") as f:
        f.write(o)
    companies.append(
        {"name": company, "projects": projects, "stats": company_stats},
    )

# stats
total_repos = data_repos.shape[0]
total_companies = len(companies)
total_teams = len(teams)

output = readme_template.render(
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
