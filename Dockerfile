###############################################################################
# Build step to gather plugins and themes
###############################################################################
FROM alpine:3.18 as build

# Setup dependencies for download script.
RUN apk add --no-cache git
RUN apk add --no-cache python3-dev

# Run download script.
WORKDIR /var/wp
COPY env_setup.py /var/wp/env_setup.py
COPY config.json /var/wp/config.json
RUN --mount=type=secret,id=GITHUB_TOKEN \
    python3 env_setup.py

###############################################################################
# Build final container
###############################################################################
FROM terabytetribune/wordpress:latest
COPY --from=build /var/wp/themes /var/www/wp-content/themes
COPY --from=build /var/wp/plugins /var/www/wp-content/plugins
