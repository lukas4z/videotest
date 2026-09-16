#!/usr/bin/env bash
# Rebuilds the SoloQ Tagebuch Tag 1 draft from the raw VOD clips + assets/.
# Expects clips/fight_3954_raw.mp4 and clips/fight_2213_raw.mp4 to already be
# downloaded (see README notes / yt-dlp --download-sections commands).
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p segments output

# --- crop gameplay clips to vertical 1080x1920 ---
ffmpeg -y -ss 16 -t 22 -i clips/fight_3954_raw.mp4 \
  -vf "crop=608:1080:740:0,scale=1080:1920,fps=30" \
  -c:v libx264 -crf 18 -preset fast -an segments/clipA_raw.mp4

ffmpeg -y -ss 8 -t 14 -i clips/fight_2213_raw.mp4 \
  -vf "crop=608:1080:656:0,scale=1080:1920,fps=30" \
  -c:v libx264 -crf 18 -preset fast -an segments/clipB_raw.mp4

# flash + SFX cue point at the Triple Kill moment (~18.15-18.30s into clipA)
ffmpeg -y -i segments/clipA_raw.mp4 \
  -vf "eq=brightness='if(between(t,18.15,18.30),0.75,0)':enable='between(t,18.15,18.30)'" \
  -c:v libx264 -crf 18 -preset fast -an segments/seg3_clipA.mp4
cp segments/clipB_raw.mp4 segments/seg4_clipB.mp4

# --- title / rank / outro / twitch cards (static image + fade) ---
make_card () {
  local img=$1 dur=$2 out=$3
  ffmpeg -y -loop 1 -i "$img" -t "$dur" \
    -vf "fade=t=in:st=0:d=0.4,fade=t=out:st=$(echo "$dur - 0.4" | bc):d=0.4,format=yuv420p" \
    -r 30 -c:v libx264 -crf 18 -preset fast -an "$out"
}
make_card assets/images/card_intro_title.jpg 4.5 segments/seg1_intro_title.mp4
make_card assets/images/card_intro_rank.jpg 8.0 segments/seg2_intro_rank.mp4
make_card assets/images/card_outro_rank.jpg 7.0 segments/seg5_outro_rank.mp4
make_card assets/images/card_twitch.jpg 4.5 segments/seg7_twitch.mp4

ffmpeg -y -f lavfi -i color=c=black:s=1080x1920:r=30:d=1.0 \
  -c:v libx264 -crf 18 -preset fast -an segments/seg6_pause.mp4

# --- concat silent video ---
cat > segments/concat_list.txt << 'EOF'
file 'seg1_intro_title.mp4'
file 'seg2_intro_rank.mp4'
file 'seg3_clipA.mp4'
file 'seg4_clipB.mp4'
file 'seg5_outro_rank.mp4'
file 'seg6_pause.mp4'
file 'seg7_twitch.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i segments/concat_list.txt -c copy output/full_silent.mp4

# --- audio mix: music bed + 3 voice lines + whoosh cuts + kill-moment sfx ---
# timeline: seg1 0-4.5 | seg2 4.5-12.5 | seg3 12.5-34.5 | seg4 34.5-48.5
#           seg5 48.5-55.5 | seg6 55.5-56.5 | seg7 56.5-61.0
ffmpeg -y \
  -i assets/music/trap_235.mp3 \
  -i assets/voice/intro.mp3 \
  -i assets/voice/outro.mp3 \
  -i assets/voice/twitch_plug.mp3 \
  -i assets/sfx/whoosh1.mp3 \
  -i assets/sfx/whoosh2.mp3 \
  -i assets/sfx/whoosh1.mp3 \
  -i assets/sfx/win1.mp3 \
  -filter_complex "\
[0:a]atrim=0:61,volume=0.15,afade=t=out:st=59:d=2[music]; \
[1:a]adelay=0|0[v1]; \
[2:a]adelay=48500|48500[v2]; \
[3:a]adelay=56500|56500[v3]; \
[4:a]atrim=0:0.8,volume=0.7,adelay=12500|12500[s1]; \
[5:a]atrim=0:0.8,volume=0.7,adelay=34500|34500[s2]; \
[6:a]atrim=0:0.8,volume=0.7,adelay=48500|48500[s3]; \
[7:a]volume=0.85,adelay=30650|30650[s4]; \
[music][v1][v2][v3][s1][s2][s3][s4]amix=inputs=8:duration=first:normalize=0[amixed]; \
[amixed]alimiter=limit=0.9[aout]" \
  -map "[aout]" -c:a aac -b:a 192k output/full_audio.m4a

# --- mux + compress for delivery ---
ffmpeg -y -i output/full_silent.mp4 -i output/full_audio.m4a \
  -map 0:v -map 1:a -c:v copy -c:a copy -shortest \
  output/soloq_tagebuch_tag1_draft.mp4

ffmpeg -y -i output/soloq_tagebuch_tag1_draft.mp4 \
  -c:v libx264 -crf 26 -preset slow -c:a aac -b:a 128k -movflags +faststart \
  output/soloq_tagebuch_tag1_draft_compressed.mp4

echo "done: output/soloq_tagebuch_tag1_draft_compressed.mp4"
