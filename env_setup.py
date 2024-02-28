""" This script is run by the Dockerfile to download themes and plugins
specified in config.json. Running it manually is not necessary.
"""
import os
import shutil
import json
import zipfile
from urllib import request

def get_json(url, req_headers=[]):
    opener = request.build_opener()
    if req_headers:
        opener.addheaders = opener.addheaders + req_headers
    request.install_opener(opener)

    with request.urlopen(url) as response:
        json_response = json.loads(response.read())
    return json_response

def download_zip(url, type, req_headers=[]):
    # Download the item as a zipfile to the zips directory (and make sure it exists).
    if not os.path.isdir("zips"):
        os.mkdir("zips")
    os.chdir("zips")

    opener = request.build_opener()
    if req_headers:
        opener.addheaders = opener.addheaders + req_headers
    request.install_opener(opener)

    local_filename, headers = request.urlretrieve(url)
    attachment_name = headers.get("Content-Disposition").split("=")[1]
    shutil.move(local_filename, f"./{attachment_name}")

    os.chdir("..")
    
    # Extract the item to the appropriate directory (and make sure it exists).
    if not os.path.isdir(type):
        os.mkdir(type)

    with zipfile.ZipFile(f"zips/{attachment_name}") as zip_object: 
        zip_object.extractall(path=type)
    
    # Remove the plugin zipfiles.
    shutil.rmtree("zips")

def download_from_wp(type, json_response):
    # Get the download link from the JSON.
    url = json_response["download_link"]
    download_zip(url, type)

def download_wp_plugins(config):
    download_links = []
    for plugin in config.get("plugins").get("wordpress.org"):
        json_response = get_json(f"https://api.wordpress.org/plugins/info/1.0/{plugin}.json")
        download_from_wp("plugins", json_response)

def download_wp_themes(config):
    for theme in config.get("themes").get("wordpress.org"):
        json_response = get_json(f"https://api.wordpress.org/themes/info/1.2/?action=theme_information&request[slug]={theme}")
        download_from_wp("themes", json_response)

def download_from_github(type, config, github_token):
    # Clone each repo from GitHub.
    for repo in config.get(type).get("github"):
        # If it ends in .git, directly clone the default branch of the repo.
        if repo.endswith(".git"):
            # Make sure the correct directory exists and cd into it.
            if not os.path.isdir(type):
                os.mkdir(type)
            os.chdir(type)

            status = os.system(f"git clone https://{github_token}:@github.com/{repo}")
            # Make sure the git clone was successful.
            if os.waitstatus_to_exitcode(status) != 0:
                raise RuntimeError(f"Cloning {repo} exited non-zero.")

            # Chdir back to the project's working directory.
            os.chdir("..")
        # If it ends in .zip, download and extract the zip file instead.
        else:
            repo_parts = repo.split("/")
            repo_name = repo_parts[0] + "/" + repo_parts[1]
            headers = [("Accept", "application/vnd.github+json"), ("Authorization", f"Bearer {github_token}"), ("X-GitHub-Api-Version", "2022-11-28")]

            # Get the latest release.
            release_json = get_json(f"https://api.github.com/repos/{repo_parts[0]}/{repo_parts[1]}/releases/latest", headers)
            
            # Get the list of assets from that release.
            assets_json = get_json(release_json["assets_url"], headers)

            # Get the download URL of the correct asset (by name).
            for asset in assets_json:
                if asset["name"] == repo_parts[-1]:
                    asset_url = asset["url"]
                    break

            # Download the asset.
            headers = [("Accept", "application/octet-stream"), ("Authorization", f"Bearer {github_token}"), ("X-GitHub-Api-Version", "2022-11-28")]

            download_zip(asset_url, type, headers)

    

def main():
    # Load config.
    with open("config.json") as stream:
        config = json.load(stream)
    
    # Get GitHub Token, either from env var or docker secrets file.
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        with open("/run/secrets/GITHUB_TOKEN") as stream:
            github_token = stream.read()
    
    download_wp_plugins(config)
    download_from_github("plugins", config, github_token)
    download_wp_themes(config)
    download_from_github("themes", config, github_token)

if __name__ == "__main__":
    main()
