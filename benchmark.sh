#!/bin/bash

# API Benchmark Script
# Sends multiple curl requests and measures average response time

# Configuration
URL="http://localhost:8000/reviews?user_name=Sarah%20Barker"
NUM_REQUESTS=10
OUTPUT_FILE="/dev/null"  # Set to a filename if you want to save responses

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 API Benchmark Tool${NC}"
echo -e "${BLUE}===================${NC}"
echo -e "URL: ${YELLOW}$URL${NC}"
echo -e "Number of requests: ${YELLOW}$NUM_REQUESTS${NC}"
echo ""

# Array to store response times
times=()
success_count=0
error_count=0

echo -e "${BLUE}Running requests...${NC}"

# Function to draw progress bar
draw_progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((current * width / total))
    local remaining=$((width - completed))

    printf "\r${BLUE}Progress: [${NC}"
    printf "%${completed}s" | tr ' ' '█'
    printf "%${remaining}s" | tr ' ' '░'
    printf "${BLUE}] %d%% (%d/%d)${NC}" $percentage $current $total
}

for i in $(seq 1 $NUM_REQUESTS); do
    # Execute curl and capture time and status
    response=$(curl -s -w "%{http_code},%{time_total}" -o "$OUTPUT_FILE" "$URL" 2>/dev/null)

    # Parse response
    http_code=$(echo "$response" | cut -d',' -f1)
    curl_time=$(echo "$response" | cut -d',' -f2)

    if [ "$http_code" = "200" ]; then
        times+=("$curl_time")
        success_count=$((success_count + 1))
    else
        error_count=$((error_count + 1))
    fi

    # Show progress bar after completing request
    draw_progress_bar $i $NUM_REQUESTS

    # Small delay between requests
    sleep 0.1
done

echo ""  # New line after progress bar

echo ""
echo -e "${BLUE}Results:${NC}"
echo -e "${BLUE}========${NC}"

if [ $success_count -eq 0 ]; then
    echo -e "${RED}❌ All requests failed!${NC}"
    exit 1
fi

# Calculate statistics
total_time=0
min_time=${times[0]}
max_time=${times[0]}

for time in "${times[@]}"; do
    total_time=$(echo "$total_time + $time" | bc -l)

    if (( $(echo "$time < $min_time" | bc -l) )); then
        min_time=$time
    fi

    if (( $(echo "$time > $max_time" | bc -l) )); then
        max_time=$time
    fi
done

avg_time=$(echo "scale=3; $total_time / $success_count" | bc -l)

# Convert to milliseconds for display
avg_time_ms=$(echo "scale=1; $avg_time * 1000" | bc -l)
min_time_ms=$(echo "scale=1; $min_time * 1000" | bc -l)
max_time_ms=$(echo "scale=1; $max_time * 1000" | bc -l)

echo -e "Successful requests: ${GREEN}$success_count${NC} / $NUM_REQUESTS"
echo -e "Failed requests: ${RED}$error_count${NC} / $NUM_REQUESTS"
echo -e "Average response time: ${YELLOW}${avg_time_ms}ms${NC}"
echo -e "Minimum response time: ${GREEN}${min_time_ms}ms${NC}"
echo -e "Maximum response time: ${RED}${max_time_ms}ms${NC}"

# Calculate requests per second
if (( $(echo "$avg_time > 0" | bc -l) )); then
    rps=$(echo "scale=2; 1 / $avg_time" | bc -l)
    echo -e "Requests per second: ${BLUE}${rps}${NC}"
fi

echo ""
echo -e "${BLUE}💡 Tips:${NC}"
echo "- Modify URL variable to test different endpoints"
echo "- Increase NUM_REQUESTS for more accurate averages"
echo "- Set OUTPUT_FILE to save responses for inspection"
