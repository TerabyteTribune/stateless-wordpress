# Stateless Wordpress
Custom Docker container image for deploying our wordpress instance with no local storage.

## Usage
### Configure
Modify `config.json` to include the themes and plugins you'd like to install. In both themes and plugins, `"wordpress.org"` should contain a list of slugs from the appropriate WordPress repo. `"github"` should contain a GitHub repository, in the form `org/repo`, followed by a suffix to determine how to download it. For example, `org/repo.git` will clone the GitHub repository, while `org/repo/filename.zip` will download a build artifact called `filename.zip` from the latest release.

### Local Build
Create a file called `.GITHUB_TOKEN` which contains only a GitHub Personal Access Token with access to repos you have configured to include in your image.

Then, run the following command to build your image.
```
docker buildx build --secret id=GITHUB_TOKEN,src=./.GITHUB_TOKEN .
```

### Auto-build using GitHub Actions
The container is automatically built and pushed to Dockerhub at the 'latest' tag via Github Actions. That workflow requires the following GitHub Actions secrets:
- `DOCKERHUB_USERNAME`: The username of the DockerHub account to push the image to.
- `DOCKERHUB_TOKEN`: An API key for the above DockerHub user.
- `THEME_TOKEN`: A GitHub Personal Access Token with access to repos you have configured to include in your image.

## Deploying
This image is based on [TerabyteTribune/docker-wordpress](https://github.com/TerabyteTribune/docker-wordpress), which is a fork of [TrafeX/docker-wordpress](https://github.com/TrafeX/docker-wordpress). View the documentation in either of those repos for instructions on using environment variables, with the following additional information:

- It is recommended to define the variables from https://api.wordpress.org/secret-key/1.1/salt/ as environment variables to prevent users from being forced to sign in each time the container restarts.

- Do not create a mount to `/var/www/wp-content` as documented in the upstream repos, as this will over-write the stateless plugins and themes fetched at build-time.
    - It is recommended to use a plugin such as Media Cloud (ilab-media-tools) to store uploads in cloud storage for fully stateless operation. Note that some files which do not use Wordpress's media library may not work properly using a plugin like this.
    - Otherwise, persist `/var/www/wp-content/uploads` using a docker volume. Note that some plugins which store files in other locations will not work properly in this configuration.
