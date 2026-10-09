#!/bin/sh
set -eu
node support/evals/tessl/fixture.mjs edited
rm support/evals/planning-fixture.mjs support/evals/tessl/fixture.mjs
node support/bin/daily-tasks.mjs --help > runtime-smoke.json
