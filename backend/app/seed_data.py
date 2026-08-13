"""Curated seed content: several realistic meetings with full transcripts.

Kept as plain data so `seed.py` stays a thin loader. Transcripts use the
"[HH:MM:SS] Speaker: text" format so the parser produces real timestamps and
the click-to-seek sync is meaningful in the demo.
"""
from __future__ import annotations

SAMPLE_AUDIO = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
SAMPLE_AUDIO_2 = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3"

DEFAULT_USER = {
    "name": "Siddharth Singh",
    "email": "tech@miracleai.in",
    "avatar_url": "https://api.dicebear.com/7.x/initials/svg?seed=Siddharth%20Singh",
}

MEETINGS = [
    {
        "title": "Q3 Product Roadmap Planning",
        "days_ago": 2,
        "audio_url": SAMPLE_AUDIO,
        "tags": ["Product", "Planning"],
        "participants": [
            {"name": "Priya Nair", "email": "priya@acme.com"},
            {"name": "Daniel Kim", "email": "daniel@acme.com"},
            {"name": "Siddharth Singh", "email": "tech@miracleai.in"},
        ],
        "transcript": """
[00:00:02] Priya Nair: Alright everyone, thanks for joining. Today we need to lock the Q3 roadmap so engineering can start planning sprints next week.
[00:00:15] Daniel Kim: Sounds good. I think the biggest theme should be onboarding. Our activation numbers dropped to 41 percent last quarter.
[00:00:29] Priya Nair: Agreed, onboarding is priority one. Siddharth, can you own the redesign of the first-run experience?
[00:00:38] Siddharth Singh: Yes, I'll take the first-run experience. I'll have a prototype ready by next Friday for us to review.
[00:00:51] Daniel Kim: Great. The second theme I'd propose is integrations. Customers keep asking for a Slack and a Notion integration.
[00:01:05] Priya Nair: Let's scope the Slack integration for Q3 and push Notion to Q4. Daniel, can you write the technical spec?
[00:01:17] Daniel Kim: I'll draft the Slack integration spec and share it by Wednesday.
[00:01:26] Siddharth Singh: One risk I want to flag: our current auth service can't handle third-party OAuth cleanly. We may need to refactor it first.
[00:01:40] Priya Nair: Good catch. Let's add an auth refactor as a dependency. We should review the effort before committing dates.
[00:01:52] Daniel Kim: I'm a little worried about capacity. If we do onboarding, Slack, and an auth refactor, that's a lot for one quarter.
[00:02:05] Priya Nair: Fair concern. Let's treat onboarding as must-have, Slack as should-have, and the auth refactor as an enabler we do only if it blocks Slack.
[00:02:20] Siddharth Singh: That prioritization works for me. I'll update the roadmap document with these three items and the dependencies.
[00:02:32] Priya Nair: Perfect. Let's reconvene Thursday to review the specs. Thanks everyone, this was productive.
""",
        "summary": {
            "overview": "The team locked the Q3 roadmap around three themes: a first-run onboarding redesign (must-have, prompted by activation dropping to 41%), a Slack integration (should-have), and an auth-service refactor treated as an enabler only if it blocks Slack. Notion integration was deferred to Q4. Capacity concerns were addressed by strict prioritization, and specs will be reviewed Thursday.",
            "keywords": "onboarding, Slack integration, auth refactor, roadmap, activation, Q3",
            "sentiment": "Positive",
        },
        "action_items": [
            {"text": "Build a prototype of the first-run onboarding experience.", "assignee": "Siddharth", "done": False},
            {"text": "Draft and share the Slack integration technical spec by Wednesday.", "assignee": "Daniel", "done": False},
            {"text": "Update the roadmap document with the three items and their dependencies.", "assignee": "Siddharth", "done": True},
            {"text": "Reconvene Thursday to review the specs.", "assignee": "Priya", "done": False},
        ],
        "topics": [
            {"title": "Onboarding as top priority", "start_ms": 15_000},
            {"title": "Integrations: Slack vs Notion", "start_ms": 51_000},
            {"title": "Auth refactor dependency", "start_ms": 86_000},
            {"title": "Capacity and prioritization", "start_ms": 112_000},
        ],
    },
    {
        "title": "Weekly Engineering Standup",
        "days_ago": 1,
        "audio_url": SAMPLE_AUDIO_2,
        "tags": ["Engineering", "Standup"],
        "participants": [
            {"name": "Aisha Rahman", "email": "aisha@acme.com"},
            {"name": "Marco Silva", "email": "marco@acme.com"},
            {"name": "Daniel Kim", "email": "daniel@acme.com"},
        ],
        "transcript": """
[00:00:01] Aisha Rahman: Morning all, let's do a quick round. Marco, you first.
[00:00:08] Marco Silva: Yesterday I finished the caching layer for the search endpoint. Latency dropped from 800 milliseconds to about 120.
[00:00:22] Aisha Rahman: That's a huge win, nice work. Any blockers?
[00:00:28] Marco Silva: No blockers. Today I'll write the integration tests and open the pull request.
[00:00:37] Daniel Kim: I spent yesterday debugging the flaky deployment pipeline. It turned out to be a race condition in the migration step.
[00:00:50] Aisha Rahman: Did you get it fixed?
[00:00:53] Daniel Kim: Mostly. I'll finalize the fix today and I need to review the rollback script with someone before we ship.
[00:01:04] Aisha Rahman: I can review the rollback script with you after standup.
[00:01:10] Marco Silva: Quick flag: the staging database is running low on disk. We should clean it up before it becomes a problem.
[00:01:21] Aisha Rahman: Good catch. Daniel, can you schedule a cleanup of the staging database this week?
[00:01:29] Daniel Kim: Sure, I'll schedule the staging cleanup for Thursday.
[00:01:35] Aisha Rahman: Great. On my side, I'm finishing the API documentation and I'll publish it today. That's everyone, thanks!
""",
        "summary": {
            "overview": "A productive standup: Marco shipped a caching layer that cut search latency from 800ms to ~120ms and will add integration tests. Daniel traced the flaky deploy pipeline to a race condition in the migration step and will finalize the fix after reviewing the rollback script with Aisha. The team flagged low disk on the staging database and scheduled a cleanup. Aisha is publishing the API documentation.",
            "keywords": "caching, latency, deployment pipeline, race condition, staging, rollback",
            "sentiment": "Positive",
        },
        "action_items": [
            {"text": "Write integration tests and open the pull request for the caching layer.", "assignee": "Marco", "done": False},
            {"text": "Finalize the migration race-condition fix and review the rollback script.", "assignee": "Daniel", "done": False},
            {"text": "Schedule a cleanup of the staging database for Thursday.", "assignee": "Daniel", "done": False},
            {"text": "Publish the API documentation.", "assignee": "Aisha", "done": True},
        ],
        "topics": [
            {"title": "Search caching and latency win", "start_ms": 8_000},
            {"title": "Deployment pipeline race condition", "start_ms": 37_000},
            {"title": "Staging database cleanup", "start_ms": 70_000},
        ],
    },
    {
        "title": "Customer Discovery Call — Northwind Logistics",
        "days_ago": 5,
        "audio_url": SAMPLE_AUDIO,
        "tags": ["Sales", "Discovery"],
        "participants": [
            {"name": "Sofia Alvarez", "email": "sofia@acme.com"},
            {"name": "Tom Becker", "email": "tom@northwind.com"},
        ],
        "transcript": """
[00:00:03] Sofia Alvarez: Thanks for taking the time, Tom. I'd love to understand how your team currently handles meeting notes.
[00:00:14] Tom Becker: Honestly it's a mess. Everyone takes their own notes and half the action items get lost after the call.
[00:00:26] Sofia Alvarez: That's a really common pain point. How many meetings would you say your team runs in a week?
[00:00:34] Tom Becker: Between the ops and sales teams, probably forty to fifty client calls a week.
[00:00:43] Sofia Alvarez: And when action items get lost, what's the impact on the business?
[00:00:50] Tom Becker: We've missed follow-ups that cost us deals. One slipped renewal last quarter was worth about ninety thousand dollars.
[00:01:03] Sofia Alvarez: That's significant. If a tool could automatically capture and assign every action item, would that solve the core problem?
[00:01:14] Tom Becker: That would be huge. The other thing we need is search. Finding what a client said three months ago is impossible right now.
[00:01:27] Sofia Alvarez: Search across all your past meetings is exactly what we do. I'll send you a tailored demo focused on action items and search.
[00:01:38] Tom Becker: Perfect. Can you also include pricing for a team of about thirty people?
[00:01:45] Sofia Alvarez: Absolutely, I'll send the demo and a thirty-seat pricing proposal by end of week.
[00:01:53] Tom Becker: Sounds great, looking forward to it.
""",
        "summary": {
            "overview": "Discovery call with Tom Becker at Northwind Logistics revealed a strong fit: their 40-50 weekly client calls suffer from lost action items — one missed renewal cost ~$90k last quarter — and they struggle to search past conversations. Tom confirmed automatic action-item capture and cross-meeting search would address the core pain. Sofia will follow up with a tailored demo and a 30-seat pricing proposal by end of week.",
            "keywords": "discovery, action items, search, renewal, pricing, Northwind",
            "sentiment": "Positive",
        },
        "action_items": [
            {"text": "Send a tailored demo focused on action items and search.", "assignee": "Sofia", "done": False},
            {"text": "Prepare a 30-seat pricing proposal and send by end of week.", "assignee": "Sofia", "done": False},
        ],
        "topics": [
            {"title": "Current note-taking pain", "start_ms": 14_000},
            {"title": "Business impact of lost follow-ups", "start_ms": 50_000},
            {"title": "Demo and pricing next steps", "start_ms": 98_000},
        ],
    },
    {
        "title": "Design Critique — New Dashboard",
        "days_ago": 8,
        "audio_url": SAMPLE_AUDIO_2,
        "tags": ["Design", "Review"],
        "participants": [
            {"name": "Lena Fischer", "email": "lena@acme.com"},
            {"name": "Priya Nair", "email": "priya@acme.com"},
            {"name": "Marco Silva", "email": "marco@acme.com"},
        ],
        "transcript": """
[00:00:02] Lena Fischer: I'll share my screen. This is the new dashboard concept. The goal was to reduce clutter and surface the most important metrics first.
[00:00:16] Priya Nair: I love the cleaner header. But the primary metric card feels a bit lost among the others. Can we make it visually dominant?
[00:00:29] Lena Fischer: Good point. I'll increase the size and add a subtle accent color to the primary card.
[00:00:38] Marco Silva: From an engineering side, the chart library you're using might be heavy. Can we consider a lighter one to keep load times fast?
[00:00:51] Lena Fischer: I'll check the bundle size and evaluate a lighter charting option before we commit.
[00:01:00] Priya Nair: The empty state is really nice, by the way. That illustration does a lot of work.
[00:01:08] Marco Silva: Agreed, the empty state is great. One accessibility note: the contrast on the secondary text looks a little low.
[00:01:19] Lena Fischer: You're right, I'll bump the contrast to meet the accessibility guidelines.
[00:01:26] Priya Nair: Overall this is a strong direction. Let's get a revised version and then hand it to engineering.
[00:01:34] Lena Fischer: I'll revise the primary card, contrast, and charting and share v2 by Monday.
""",
        "summary": {
            "overview": "Design critique of the new dashboard concept was positive overall. The team praised the cleaner header and empty-state illustration, but asked to make the primary metric card visually dominant, improve low-contrast secondary text for accessibility, and evaluate a lighter charting library to protect load times. Lena will deliver a revised v2 by Monday before handing off to engineering.",
            "keywords": "dashboard, design critique, accessibility, contrast, charting, load time",
            "sentiment": "Positive",
        },
        "action_items": [
            {"text": "Make the primary metric card larger with an accent color.", "assignee": "Lena", "done": False},
            {"text": "Evaluate a lighter charting library and check bundle size.", "assignee": "Lena", "done": False},
            {"text": "Increase secondary-text contrast to meet accessibility guidelines.", "assignee": "Lena", "done": False},
            {"text": "Share dashboard v2 by Monday.", "assignee": "Lena", "done": False},
        ],
        "topics": [
            {"title": "Primary metric hierarchy", "start_ms": 16_000},
            {"title": "Charting performance", "start_ms": 38_000},
            {"title": "Accessibility and contrast", "start_ms": 68_000},
        ],
    },
]
