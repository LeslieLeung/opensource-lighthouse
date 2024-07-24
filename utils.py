# TODO
# 1. with the limit of 5000 requests per hour, consider use some stateful cache to store the data, e.g. csv file in the repo

from typing import List, Optional
from tqdm import tqdm
from github import Auth, Github, Repository, NamedUser
import requests


def get_all_repos(user: str, token: Optional[str] = None) -> List[Repository]:
    """
    Retrieves all repositories for a given user.

    Args:
        user (str): The username of the user.
        token (str, optional): GitHub personal access token for authentication.

    Returns:
        List[Repository]: A list of Repository objects representing the user's repositories.
    """
    auth = Auth.Token(token)
    g = Github(auth=auth)
    org = g.get_user(user)
    repos = []
    for repo in org.get_repos():
        repos.append(repo)
    return repos


def get_top_starred_repos(user: str, n: int, token: Optional[str] = None) -> List[Repository]:
    """
    Get the top n repositories with the most stars for a given GitHub user.

    Args:
        user (str): GitHub username.
        n (int): Number of top repositories to fetch.
        token (Optional[str]): GitHub personal access token for authentication.

    Returns:
        List[Repository]]: List of Repository containing repository names and their stars.
    """
    repos = get_all_repos(user, token)
    if not repos:
        return []

    # Sort repositories by star count in descending order
    sorted_repos = sorted(
        repos, key=lambda repo: repo.stargazers_count, reverse=True)

    # Get the top n repositories
    top_repos = sorted_repos[:n]
    return top_repos


def calculate_contributions_by_company(repo: Repository, companies: List[str], n: Optional[int] = None) -> dict:
    """
    Calculate the contributions in terms of number of commits made by companies in a GitHub repository.
    Only contributors from the specified companies are considered.

    Args:
        repo (Repository): Repository object.
        companies (List[str]): A list of company names to filter the contributors by.
        n (int): The maximum number of contributors to consider, if not given, it will consider all contributors.

    Returns:
        dict: A dictionary where the keys are the company names and the values are the percentage contributions made by contributors from each company.
        example: {'GOOGLE': 77.99268590004064,
            'MICROSOFT': 14.758228362454288, 'INTEL': 7.249085737505078}
    """
    companies = [company.upper() for company in companies]
    contributors = repo.get_contributors()
    contributors = [contributor for contributor in contributors]
    company_contributions = {}
    if n is None or len(contributors) < n:
        n = len(contributors)
    for contributor in tqdm(contributors[:n], desc='Fetching contributors'):
        company = contributor.company
        if company is None:
            continue
        company = company.upper().replace('@', '').strip()

        count = False
        for target_company in companies:
            if company.find(target_company) != -1:
                company = target_company
                count = True
                break
        if count:
            company_contributions[company] = company_contributions.get(
                company, 0) + contributor.contributions

    # convert the number into percentage
    total_contributions = sum(company_contributions.values())
    for company, contributions in company_contributions.items():
        company_contributions[company] = (
            contributions / total_contributions) * 100
    return company_contributions


def calculate_single_company_contributions(repo: Repository, company: str, n: Optional[int] = None) -> float:
    """
    Calculate the percentage contributions in terms of number of commits made by a single company in a GitHub repository.

    Args:
        repo (Repository): Repository object.
        company (str): The company name to filter the contributors by.
        n (int): The maximum number of contributors to consider, if not given, it will consider all contributors.

    Returns:
        float: The percentage contributions made by contributors from the specified company.
    """
    company = company.upper()
    contributors = repo.get_contributors()
    contributors = [contributor for contributor in contributors]
    company_contributions = 0
    total_contributions = 0
    if n is None or n > len(contributors):
        n = len(contributors)
    for contributor in tqdm(contributors[:n], desc='Fetching contributors'):
        contributor_company = (
            contributor.company or '').upper().replace('@', '').strip()

        if contributor_company.find(company) != -1:
            company_contributions += contributor.contributions
        total_contributions += contributor.contributions

    return (company_contributions / total_contributions) * 100


def list_organizations_of_pr_creators(repo: Repository) -> List:
    """
    Retrieves a list of organizations associated with the creators of pull requests in a given repository.

    Args:
        repo (Repository): The repository object for which to retrieve the organizations.

    Returns:
        List: A list of organizations associated with the creators of pull requests.
        Every element in the list is a dictionary containing 'org_name', 'percentage' and 'pull_request_creators'
    """
    owner = repo.owner.login
    name = repo.name

    url = 'https://api.ossinsight.io/v1/repos/{owner}/{name}/pull_request_creators/organizations/'.format(
        owner=owner, name=name)

    payload = {}
    headers = {
        'Accept': 'application/json'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    response.raise_for_status()

    data = response.json()['data']['rows']

    return data


def is_company_dominant_in_repo(repo: Repository, threshold: float) -> bool:
    """
    Checks if a company is dominant in a repository based on the percentage of pull request creators.

    Args:
        repo (Repository): The repository to check.
        threshold (float): The threshold percentage for dominance. e.g. 0.3 for 30%.

    Returns:
        bool: True if the company is dominant, False otherwise.
    """
    result = list_organizations_of_pr_creators(repo)
    if float(result[0]['percentage']) > threshold:
        return True
    return False


if __name__ == "__main__":
    token = 'ghp_example'
    username = 'kubernetes'
    companies = ['GOOGLE', 'MICROSOFT', 'INTEL',
                 'Red Hat', 'Databricks', 'Amazon Web Services', 'Goldman Sachs']

    repos = get_top_starred_repos(username, 5, token)
    repo = repos[0]

    result1 = calculate_contributions_by_company(repo, companies, 100)
    print(f'Contributions by company: {result1}')
    result2 = calculate_single_company_contributions(repo, companies[0], 100)
    print(f'Contributions by single company {companies[0]}: {result2}')

    result3 = is_company_dominant_in_repo(repo, 0.05)
    print(f'Is company dominant in repo: {result3}')
