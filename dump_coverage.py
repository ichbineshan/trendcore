import json

out = {
    "coverage_pct": 0.0,
    "lines_total": 0,
    "lines_covered": 0,
    "branch_pct": 0.0,
    "branches_covered": 0,
    "branches_total": 0,
}

with open("coverage/coverage_output.json", "w") as outfile:
    json.dump(out, outfile)
