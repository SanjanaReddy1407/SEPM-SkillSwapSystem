# CrossSkill — Multi-Page Prototype

A real, multi-page front-end for the CrossSkill PRD — actual `.html` files with real links
between them (no client-side router / SPA), CSS split by concern, JS split per page, and
mock data in JSON. State (profile, requests, connections, chats, schedules, feedback) is
kept in `localStorage` so it survives normal page navigation and browser refreshes.

## Folder structure

```
crossskill-mpa/
├── index.html                 Landing page
├── login.html                 Sign in
├── signup.html                Create account
├── profile-setup.html         Add offered/desired skills (onboarding)
├── app/                       Everything behind login
│   ├── discover.html          Search by name / skill
│   ├── recommendations.html   Ranked match engine
│   ├── requests.html          Incoming / Sent / Active tabs
│   ├── chat.html              1-on-1 messaging
│   ├── schedule.html          Book & track sessions
│   ├── feedback.html          Star rating + written review
│   └── profile.html           Reputation + editable skill catalog
├── css/
│   ├── tokens.css             Colors, fonts, reset (used everywhere)
│   ├── components.css         Buttons, fields, chips, badges, toast (used everywhere)
│   ├── landing.css            index.html only
│   ├── auth.css               login.html / signup.html
│   ├── setup.css              profile-setup.html (+ reused on app/profile.html)
│   └── app-shell.css          Sidebar + all /app pages
├── js/
│   ├── store.js                localStorage-backed state + auth guards
│   ├── match.js                Recommendation scoring logic
│   ├── toast.js                Bottom notification helper
│   ├── nav.js                  Renders the left sidebar on every /app page
│   ├── auth.js                 login.html + signup.html
│   ├── setup.js                profile-setup.html
│   ├── discover.js             app/discover.html
│   ├── recommendations.js      app/recommendations.html
│   ├── requests.js             app/requests.html
│   ├── chat.js                 app/chat.html
│   ├── schedule.js             app/schedule.html
│   ├── feedback.js             app/feedback.html
│   └── profile.js              app/profile.html
└── data/
    ├── students.json           Mock candidate pool (6 students)
    └── categories.json         Skill category list
```

## Running it

`discover.js` and `recommendations.js` `fetch()` the JSON files, and browsers block
`fetch()` on `file://` pages for security reasons — so open this with a local server
rather than double-clicking `index.html`:

```bash
cd crossskill-mpa
python3 -m http.server 8000
# then open http://localhost:8000/index.html
```

(Any static server works — `npx serve`, VS Code's Live Server extension, etc.)

## How the flow maps to the PRD

- **US-01–03 (auth)** → `login.html`, `signup.html`, `js/auth.js`
- **US-04–08 (profile/skills)** → `profile-setup.html` (first run) and `app/profile.html`
  (ongoing edits), both backed by `js/store.js`'s `me.offered` / `me.desired`
- **US-09–11 (search)** → `app/discover.html`
- **US-12–16 (recommendation engine)** → `js/match.js` (desired↔offered cross-match,
  skill-level compatibility, rating factor) rendered by `app/recommendations.html`
- **US-17–19 (requests/connections)** → `app/requests.html`, `PENDING → ACTIVE` lifecycle
- **US-20–21 (chat)** → `app/chat.html`
- **US-22–24 (scheduling)** → `app/schedule.html`
- **US-25–27 (feedback/rating)** → `app/feedback.html`, updates `me.avgRating`

## Notes

- This is a front-end prototype only — there's no Flask backend or Neon Postgres here,
  matching the PRD's actual stack. `localStorage` stands in for the database so the UI
  is fully clickable end-to-end.
- To reset the demo (clear all local state), open the browser console on any page and run:
  `localStorage.removeItem('crossskill_state_v1')`, or click **Log out** on the Profile page.
