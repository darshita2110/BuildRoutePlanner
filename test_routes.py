from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
EXE = ROOT / "main.exe"


def check_route(start, goal, expected_distance, closed_road=None):
    user_input = f"{start}\n{goal}\n"

    if closed_road is None:
        user_input += "\n"  # Press Enter: no closed road.
    else:
        user_input += f"{closed_road[0]}\n{closed_road[1]}\n"

    run = subprocess.run(
        [str(EXE)],
        input=user_input,
        text=True,
        capture_output=True,
        cwd=ROOT
    )

    assert run.returncode == 0, run.stderr

    match = re.search(
        r"Shortest\s+Distance:\s*(\d+)\s*m",
        run.stdout,
        re.IGNORECASE
    )
    assert match, f"Distance missing from output:\n{run.stdout}"

    actual = int(match.group(1))
    assert actual == expected_distance, (
        f"{start} -> {goal}: expected {expected_distance} m, got {actual} m"
    )

    print(f"PASS: {start} -> {goal} = {actual} m")


check_route("GATE", "CAFE", 200)
check_route("GATE", "CAFE", 250, ("ADMIN", "CAFE"))
check_route("GATE", "LAB", 400)
check_route("GATE", "SPORTS", 315)
check_route("CAFE", "GATE", 200)
check_route("GATE", "GATE", 0)

print("All route checks passed.")