# TODO
# 1. replace requests with aiohttp
# 2. with the limit of 5000 requests per hour, consider use some stateful cache to store the data, e.g. csv file in the repo

from typing import List, Optional
import requests
from typing import List, Tuple, Optional
from tqdm import tqdm


def get_all_repos(user: str, token: Optional[str] = None) -> List[dict]:
    repos = []
    page = 1
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    while True:
        url = f'https://api.github.com/users/{user}/repos'
        params = {
            'per_page': 100,
            'page': page
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repositories: {e}")
            break
    return repos


def get_top_starred_repos(user: str, n: int, token: Optional[str] = None) -> List[Tuple[str, int]]:
    """
    Get the top n repositories with the most stars for a given GitHub user.

    Args:
        user (str): GitHub username.
        n (int): Number of top repositories to fetch.
        token (Optional[str]): GitHub personal access token for authentication.

    Returns:
        List[Tuple[str, int]]: List of tuples containing repository names and their stars.
    """
    repos = get_all_repos(user, token)
    if not repos:
        return []

    # Sort repositories by star count in descending order
    sorted_repos = sorted(
        repos, key=lambda repo: repo['stargazers_count'], reverse=True)

    # Get the top n repositories
    top_repos = sorted_repos[:n]
    return [(repo['name'], repo['stargazers_count']) for repo in top_repos]


def get_all_contributors(user: str, repo: str, token: Optional[str] = None) -> List[Tuple[str, int]]:
    """
    Retrieves all contributors of a given GitHub repository.

    Args:
        user (str): The username or organization name of the repository owner.
        repo (str): The name of the repository.
        token (Optional[str]): GitHub personal access token for authentication.

    Returns:
        List[Tuple[str, int]]: A list of tuples containing the contributor's login name and their number of contributions.
    """
    contributors = []
    page = 1
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    while True:
        url = f'https://api.github.com/repos/{user}/{repo}/contributors'
        params = {
            'per_page': 100,
            'page': page
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            contributors.extend(data)
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching contributors: {e}")
            break
    return [(contributor['login'], contributor['contributions']) for contributor in contributors]


def get_company(user: str, token: Optional[str] = None) -> str:
    """
    Retrieves the uppercase company name of a GitHub user.

    Args:
        user (str): The GitHub username.
        token (Optional[str]): GitHub personal access token for authentication.

    Returns:
        str: The company name of the user, or 'N/A' if not found.
    """
    url = f'https://api.github.com/users/{user}'
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        company = data.get('company')
        if company is None:
            return 'N/A'

        # remove @ and blank spaces
        company = company.replace('@', '').strip()
        return company.upper()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching user data: {e}")
        return 'N/A'


def calculate_contributions_by_company(user: str, repo: str, companies: List[str], n: int, token: Optional[str] = None) -> dict:
    """
    Calculate the contributions made by companies in a GitHub repository.
    Only contributors from the specified companies are considered.

    Args:
        user (str): The username or organization name of the repository owner.
        repo (str): The name of the repository.
        companies (List[str]): A list of company names to filter the contributors by.
        n (int): The maximum number of contributors to consider.
        token (Optional[str]): An optional GitHub personal access token for authentication.

    Returns:
        dict: A dictionary where the keys are the company names and the values are the percentage contributions made by contributors from each company.
        example: {'GOOGLE': 77.99268590004064, 'MICROSOFT': 14.758228362454288, 'INTEL': 7.249085737505078}
    """
    companies = [company.upper() for company in companies]
    contributors = get_all_contributors(user, repo, token)
    company_contributions = {}
    if len(contributors) < n:
        n = len(contributors)
    for contributor, contributions in tqdm(contributors[:n], desc='Fetching contributors'):
        company = get_company(contributor, token)
        count = False
        for target_company in companies:
            if company.find(target_company) != -1:
                company = target_company
                count = True
                break
        if count:
            company_contributions[company] = company_contributions.get(
                company, 0) + contributions

    # convert the number into percentage
    total_contributions = sum(company_contributions.values())
    for company, contributions in company_contributions.items():
        company_contributions[company] = (
            contributions / total_contributions) * 100
    return company_contributions


def calculate_single_company_contributions(user: str, repo: str, company: str, n: int, token: Optional[str] = None) -> float:
    """
    Calculate the percentage contributions made by a single company in a GitHub repository.

    Args:
        user (str): The username or organization name of the repository owner.
        repo (str): The name of the repository.
        company (str): The company name to filter the contributors by.
        n (int): The maximum number of contributors to consider.
        token (Optional[str]): An optional GitHub personal access token for authentication.

    Returns:
        float: The percentage contributions made by contributors from the specified company.
    """
    company = company.upper()
    contributors = get_all_contributors(user, repo, token)
    company_contributions = 0
    if len(contributors) < n:
        n = len(contributors)
    for contributor, contributions in tqdm(contributors[:n], desc='Fetching contributors'):
        contributor_company = get_company(contributor, token)
        if contributor_company.find(company) != -1:
            company_contributions += contributions

    total_contributions = sum(
        contributions for _, contributions in contributors[:n])
    return (company_contributions / total_contributions) * 100


if __name__ == "__main__":
    token = 'ghp_example'
    username = 'kubernetes'
    repo = 'kubernetes'
    companies = ['GOOGLE', 'MICROSOFT', 'INTEL']

    result = calculate_contributions_by_company(
        username, repo, companies, 100, token)
    print(result)
