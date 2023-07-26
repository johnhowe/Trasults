#!/bin/bash

events_file="events.txt"

# Check if events file exists
if [ ! -f "$events_file" ]; then
  echo "Events file '$events_file' not found."
  exit 1
fi

# Function to process each UUID
process_uuid() {
  uuid="$1"
  original_url="https://sporttech.io/events/$uuid/ovs/event/TRA"
  converted_url="${original_url/\/event\/TRA/\/api\/event\/export?type=csv2}"

  # Generate a temporary filename using mktemp
  temp_filename=$(mktemp -p .)

  echo "Original URL: $original_url"
  echo "Converted URL: $converted_url"
  echo "Temp File: $temp_filename"

  # Download the converted URL using curl
  curl -o "$temp_filename" "$converted_url"

  if [ $? -eq 0 ]; then
    echo "Download completed. Temporary file: $temp_filename"

    # Extract the "Title" field from the second row of the CSV
    title=$(awk -F',' 'NR==2 {print $3}' "$temp_filename")

    # Create the final filename based on the "Title" value
    final_filename="${title// /_}.csv"

    # Rename the temporary file to the final filename
    echo mv "$temp_filename" "$final_filename"
    mv "$temp_filename" "$final_filename"

    echo "File renamed to: $final_filename"
  else
    echo "Download failed."
    # Remove the temporary file on download failure
    rm "$temp_filename"
  fi

  echo # Add a blank line between iterations
}

export -f process_uuid

# Process each UUID using GNU parallel
parallel -a "$events_file" process_uuid
