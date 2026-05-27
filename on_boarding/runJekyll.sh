#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")/docs"

if [[ ! -d vendor/bundle ]]; then
  bundle config set --local path vendor/bundle
  bundle install
fi

exec bundle exec jekyll serve --livereload
