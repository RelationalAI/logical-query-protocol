#!/bin/bash

for f in lqp_input/*; do
    if [ ! -f "$f" ]; then
        continue
    fi

    echo "Regenerating $f"

    # Get the filename without the path and extension
    filename=$(basename -- "$f")
    filename_no_ext="${filename%.*}"

    # Run the command and save the output to a file
    lqp --bin "bin_output/${filename_no_ext}.bin" "$f"
done
