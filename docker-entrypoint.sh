#!/bin/bash

set -e

# Run migrations if DISABLE_MIGRATIONS is not set
if [ -z "$DISABLE_MIGRATIONS" ]; then
    echo "Run migrations"
    $CMD_PREFIX aerich upgrade
fi

$CMD_PREFIX "$@"
