#!/usr/bin/env bash

set -e
set -x

cd /app/gramine-dummy-attester/dummyattester

python testonce.py | tee /data/testquote
