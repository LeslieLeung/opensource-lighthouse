import pandas as pd

from github import Github
from github import Auth
from github.GithubException import UnknownObjectException
import argparse
import datetime
from opensource_lighthouse.render import render_company, render_readme

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
render_languages = ["en", "zh"]  # ISO 639-1 codes
path_to_company_stats = "data/display_data/companies.csv"

time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
cutoff_date = datetime.datetime.now() - datetime.timedelta(days=180)

# Define columns and dtypes
columns = [
    "id",
    "owner",
    "repo",
    "link",
    "stars",
    "license",
    "language",
    "created_at",
    "last_updated_at",
    "last_pushed_at",
    "company",
    "description",
]
dtypes = {
    "id": int,
    "owner": str,
    "repo": str,
    "link": str,
    "stars": int,
    "license": str,
    "language": str,
    "created_at": str,
    "last_updated_at": str,
    "last_pushed_at": str,
    "company": str,
    "description": str,
}

# load teams from csv
data_teams = pd.read_csv(path_to_teams)
data_repos = pd.read_csv(path_to_repos, dtype=dtypes)

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
    # clear all data in repos
    data_repos = pd.DataFrame(columns=columns)
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
                "last_pushed_at": repo.pushed_at.date().strftime("%Y-%m-%d"),
                "company": team_to_company[team],
            }

            # add repo
            data_repos = pd.concat(
                [data_repos, pd.DataFrame([repo_info])], ignore_index=True
            )
    # save to csv
    data_repos.astype(dtypes)
    data_repos.to_csv(path_to_repos, index=False)

# render readme
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
    # count projects pushed within 180 days
    active_projects = len(
        [
            project
            for project in projects
            if datetime.datetime.strptime(project["last_pushed_at"], "%Y-%m-%d")
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

    for l in render_languages:
        render_company(l, company, company_stats, projects, time)

    companies.append(
        {"name": company, "projects": projects, "stats": company_stats},
    )

# order companies by stars descending
companies = sorted(companies, key=lambda x: x["stats"]["total_stars"], reverse=True)

# stats
total_repos = data_repos.shape[0]
total_companies = len(companies)
total_teams = len(teams)

for l in render_languages:
    render_readme(l, total_repos, total_companies, total_teams, time, teams, companies)

# dump company stats to dedicated csv
company_stats_df = pd.DataFrame(
    [
        {
            "company": company["name"],
            "total_projects": company["stats"]["total_projects"],
            "total_teams": company["stats"]["total_teams"],
            "total_stars": company["stats"]["total_stars"],
            "top_3_languages": company["stats"]["top_3_languages"],
            "active_projects": company["stats"]["active_projects"],
        }
        for company in companies
    ]
)
company_stats_df.to_csv(path_to_company_stats, index=False)
