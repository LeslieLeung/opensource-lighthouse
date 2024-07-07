import jinja2
import os

env = jinja2.Environment(loader=jinja2.FileSystemLoader("./template"))


def render_readme(
    language, total_repos, total_companies, total_teams, time, teams, companies
):
    template = env.get_template(f"readme_{language}.tmpl")
    output = template.render(
        total_repos=total_repos,
        total_companies=total_companies,
        total_teams=total_teams,
        time=time,
        teams=teams,
        companies=companies,
    )
    file_name = f"README_{language}.md"
    if language == "zh":
        file_name = "README.md"
    with open(file_name, "w") as f:
        f.write(output)


def render_company(language, company, company_stats, projects, time):
    template = env.get_template(f"company_{language}.tmpl")
    output = template.render(
        company_name=company,
        stat=company_stats,
        projects=projects,
        time=time,
    )
    file_name = f"page/{language}/{company}.md"
    # create dir if not exists
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    if language == "zh":
        file_name = f"page/{company}.md"
    with open(file_name, "w") as f:
        f.write(output)
