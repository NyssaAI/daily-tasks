#!/bin/sh
set -eu
node support/evals/tessl/fixture.mjs recovery
node support/bin/daily-tasks.mjs --help > runtime-smoke.json
