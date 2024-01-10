input_file="$1"
pcm_file="${input_file%.*}.pcm"
silk_file="${input_file%.*}.silk"

cur_dir=$(dirname "$0")
echo "Current working directory: $cur_dir"

# echo "input_file: $input_file"
# echo "pcm_file: $pcm_file"
# echo  "silk_file: $silk_file"

ffmpeg -y -i "$input_file" -f s16le -acodec pcm_s16le "$pcm_file"

$cur_dir/silk_encoder "$pcm_file" "$silk_file"
rm "$pcm_file"
