import subprocess

SEG_DIR = "/home/user/videotest/segments"
OUT_DIR = "/home/user/videotest/output"
ASSETS = "/home/user/videotest/assets"

segments = [
    ("seg1_intro_title", 4.5),
    ("seg2_intro_rank", 8.0),
    ("seg3_clipA", 22.0),
    ("seg4_clipB", 14.0),
    ("seg5_outro_rank", 7.0),
    ("seg6_pause", 1.0),
    ("seg7_twitch", 4.5),
]

transitions = [
    ("fade", 0.30),
    ("zoomin", 0.35),
    ("slideleft", 0.30),
    ("circleopen", 0.35),
    ("fadeblack", 0.25),
    ("fade", 0.30),
]

# --- compute new start times in the crossfaded timeline ---
new_start = [0.0]
for i in range(1, len(segments)):
    prev_dur = segments[i - 1][1]
    t_dur = transitions[i - 1][1]
    new_start.append(new_start[i - 1] + prev_dur - t_dur)
total_duration = new_start[-1] + segments[-1][1]
print("new_start:", new_start)
print("total_duration:", total_duration)

# --- build xfade filter chain ---
inputs = []
for name, _ in segments:
    inputs += ["-i", f"{SEG_DIR}/{name}.mp4"]

filter_parts = []
running_label = "0:v"
running_dur = segments[0][1]
for i in range(1, len(segments)):
    ttype, tdur = transitions[i - 1]
    offset = running_dur - tdur
    out_label = f"vx{i}"
    filter_parts.append(
        f"[{running_label}][{i}:v]xfade=transition={ttype}:duration={tdur}:offset={offset:.3f}[{out_label}]"
    )
    running_label = out_label
    running_dur = running_dur - tdur + segments[i][1]

filter_complex = ";".join(filter_parts)

cmd = ["ffmpeg", "-y"] + inputs + [
    "-filter_complex", filter_complex,
    "-map", f"[{running_label}]",
    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
    f"{OUT_DIR}/full_silent_v2.mp4",
]
print(" ".join(cmd[:8]), "...")
subprocess.run(cmd, check=True)

# --- audio cue offsets in the new timeline ---
clipA_start = new_start[2]
seg5_start = new_start[4]
seg7_start = new_start[6]
kill_sfx_t = clipA_start + 18.15
whoosh_into_clipA = new_start[2]
whoosh_into_clipB = new_start[3]
whoosh_into_outro = new_start[4]

print("intro voice at", new_start[0])
print("outro voice at", seg5_start)
print("twitch voice at", seg7_start)
print("kill sfx at", kill_sfx_t)
print("whoosh offsets:", whoosh_into_clipA, whoosh_into_clipB, whoosh_into_outro)

with open(f"{SEG_DIR}/audio_offsets.txt", "w") as f:
    f.write(f"{new_start[0]}\n{seg5_start}\n{seg7_start}\n{kill_sfx_t}\n")
    f.write(f"{whoosh_into_clipA}\n{whoosh_into_clipB}\n{whoosh_into_outro}\n{total_duration}\n")
