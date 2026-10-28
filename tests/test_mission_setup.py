import json
import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills" / "mission"
AGENTS_DIR = SKILL / "opencode" / "agents"
PROFILE = SKILL / "opencode" / "mission-default.json"

AGENT_NAMES = {
    "mission", "mission-research", "mission-implement",
    "mission-judge", "mission-review", "mission-merger",
}


def backtick(cell):
    match = re.search(r"`([^`]+)`", cell)
    return match.group(1) if match else None


def defaults_table():
    """Agent -> (model, route) rows from MODEL_DEFAULTS.md."""
    rows = {}
    for line in (SKILL / "MODEL_DEFAULTS.md").read_text().splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 4:
            continue
        agent, route = backtick(cells[1]), backtick(cells[3])
        if agent is None or route is None:
            continue  # header or separator row
        rows[agent] = (cells[2], route)
    return rows


def is_route(value):
    parts = value.split("/")
    return len(parts) >= 2 and all(re.fullmatch(r"[A-Za-z0-9._:+-]+", part) for part in parts)


class MissionSetupTests(unittest.TestCase):
    def test_defaults_table_maps_every_agent(self):
        rows = defaults_table()
        self.assertEqual(set(rows), AGENT_NAMES)
        for agent, (model, route) in rows.items():
            self.assertTrue(model, f"missing model for {agent}")
            self.assertTrue(is_route(route), f"bad route for {agent}: {route}")

    def test_agents_exist_with_valid_frontmatter(self):
        for agent in sorted(AGENT_NAMES):
            file = AGENTS_DIR / f"{agent}.md"
            self.assertTrue(file.is_file(), file)
            lines = file.read_text().splitlines()
            self.assertEqual(lines[0], "---", file)
            end = lines[1:].index("---") + 1
            frontmatter = json.loads("\n".join(lines[1:end]))
            self.assertIn("description", frontmatter, agent)
            self.assertIn("mode", frontmatter, agent)

    def test_profile_json_matches_defaults_table(self):
        rows = defaults_table()
        profile = json.loads(PROFILE.read_text())
        self.assertEqual(profile["default_agent"], "mission")
        self.assertEqual(profile["subagent_depth"], 1)
        self.assertEqual(set(profile["agent"]), AGENT_NAMES)
        for agent, (_, route) in rows.items():
            self.assertEqual(profile["agent"][agent]["model"], route, agent)
        self.assertEqual(profile["model"], rows["mission"][1])

    def test_judge_route_differs_from_proposer_routes(self):
        rows = defaults_table()
        judge = rows["mission-judge"][1]
        proposers = {rows["mission"][1], rows["mission-implement"][1], rows["mission-merger"][1]}
        self.assertNotIn(judge, proposers)

    def test_setup_guide_names_real_files(self):
        setup = (SKILL / "SETUP.md").read_text()
        for name in ("MODEL_DEFAULTS.md", "opencode/mission-default.json", "opencode/agents/", "opencode/oc-mission"):
            self.assertIn(name, setup)
            self.assertTrue((SKILL / name.rstrip("/")).exists(), name)

    def test_markdown_links_resolve(self):
        for doc in SKILL.glob("*.md"):
            for target in re.findall(r"\]\(([^)#]+)\)", doc.read_text()):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                self.assertTrue((doc.parent / target).exists(), f"{doc.name}: {target}")


if __name__ == "__main__":
    unittest.main()
