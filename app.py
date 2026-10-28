"""
Statecraft - a personal development app for aspiring politicians.
Run:  streamlit run app.py
"""
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Statecraft", page_icon="🏛️", layout="wide")

DATA_FILE = Path("statecraft_data.json")

# --------------------------------------------------------------------------
# Custom CSS
# --------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,700&family=Public+Sans:wght@400;500;600&display=swap');
:root{
  --ink:#12203a; --brass:#b9852c; --paper:#f2f4f7; --card:#ffffff;
  --oxblood:#8c2f39; --line:#d5dae3; --muted:#5a6578;
}
.stApp{background:var(--paper); font-family:'Public Sans',sans-serif; color:var(--ink);}
h1,h2,h3,h4{font-family:'Newsreader',serif !important; color:var(--ink); letter-spacing:-0.01em;}
h1{font-size:2.4rem !important;}
[data-testid="stSidebar"]{background:var(--ink);}
[data-testid="stSidebar"] *{color:#e8ecf3 !important;}
[data-testid="stSidebar"] .stDownloadButton button{background:var(--brass); color:#fff !important; border:0;}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section{background:#1c2d4d; border:1px dashed #4a5b7c;}
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button{
  background:var(--ink); color:#fff; border:0; border-radius:6px;
  font-weight:600; padding:.5rem 1.1rem; transition:background .15s;
}
.stButton>button:hover, .stFormSubmitButton>button:hover{background:var(--brass); color:#fff;}
.stButton>button:focus-visible, .stFormSubmitButton>button:focus-visible{outline:3px solid var(--brass); outline-offset:2px;}
[data-testid="stMetric"]{
  background:var(--card); border:1px solid var(--line); border-left:4px solid var(--brass);
  padding:12px 16px; border-radius:6px;
}
.rank{
  background:var(--ink); color:#f4f6fa; padding:26px 30px; border-radius:8px;
  border-bottom:4px solid var(--brass); margin-bottom:18px;
}
.rank h2{color:#fff !important; margin:0 0 4px 0;}
.rank p{color:#b9c3d6; margin:0 0 14px 0;}
.bar{background:#2a3b5e; height:10px; border-radius:5px; overflow:hidden;}
.bar>span{display:block; height:100%; background:var(--brass);}
.panel{
  background:var(--card); border:1px solid var(--line); border-radius:6px;
  padding:16px 20px; margin-bottom:12px;
}
.panel.warn{border-left:4px solid var(--oxblood);}
.panel.good{border-left:4px solid #2f7a55;}
.muted{color:var(--muted); font-size:.92rem;}
.stTabs [data-baseweb="tab"]{font-weight:600;}
.stTabs [aria-selected="true"]{color:var(--oxblood) !important;}
@media (max-width:640px){ h1{font-size:1.8rem !important;} .rank{padding:18px;} }
@media (prefers-reduced-motion:reduce){ *{transition:none !important;} }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------
LEVELS = [
    (0, "Volunteer"), (100, "Ward Worker"), (300, "Local Representative"),
    (700, "Legislator"), (1500, "Minister"), (3000, "Statesperson"),
]

TRAITS = {
    "Public speaking": [
        "Record a 2-minute talk on a local issue and watch it back once.",
        "Rewrite your opening line three ways; pick the one that earns attention fastest.",
        "Practise one pause of two full seconds before your main point.",
    ],
    "Empathy & listening": [
        "In your next conversation, repeat back what the person said before you reply.",
        "Ask three people what their biggest daily frustration is. Do not offer solutions.",
        "Write a 5-line summary of an opponent's view that they would accept as fair.",
    ],
    "Integrity": [
        "List one promise you made this week and confirm you kept it.",
        "Write down a decision where the easy option and the right option differed.",
        "Admit one small mistake openly today, with the fix.",
    ],
    "Resilience": [
        "Read one harsh criticism of a leader you admire and note how they responded.",
        "Do one thing today that risks mild embarrassment (ask a question, volunteer).",
        "After a setback, write: what happened, what I control, my next step.",
    ],
    "Strategic thinking": [
        "Pick a current policy issue. List who gains, who loses, and who decides.",
        "Map a goal you have into 3 milestones over 12 months.",
        "Write the strongest argument against your own position.",
    ],
    "Negotiation": [
        "Before your next negotiation, write your BATNA and theirs.",
        "Find two interests behind a position someone holds, not just the demand.",
        "Practise offering a concession that costs you little and means a lot to them.",
    ],
    "Emotional control": [
        "When irritated today, wait 10 seconds and then answer in one calm sentence.",
        "Name the emotion you feel in a tense moment, in your head, before speaking.",
        "Review a heated exchange and rewrite your side in a neutral tone.",
    ],
    "Media & image": [
        "Prepare three one-sentence messages you want repeated about you.",
        "Practise bridging: answer a hard question in 1 sentence, then pivot to your message.",
        "Audit your public social profile as a journalist would.",
    ],
}

HABITS = {
    "Read news from two differing sources (20 min)": 15,
    "Practise a speech or talk aloud (10 min)": 20,
    "Reach out to one person in my network": 15,
    "Do a 'give' for someone (intro, help, praise)": 20,
    "Write a short evening reflection": 10,
    "Exercise or walk (stamina matters)": 10,
}

QUIZZES = {
    "Governance": [
        ("Separation of powers divides government into which branches?",
         ["Legislature, executive, judiciary", "Army, police, civil service", "Federal, state, local"], 0),
        ("Federalism means:",
         ["All power sits with the capital", "Power is shared between national and regional governments",
          "Regions choose the head of state"], 1),
        ("A coalition government forms when:",
         ["A single party wins every seat", "No single party has a majority and parties agree to govern together",
          "The head of state dissolves the legislature"], 1),
    ],
    "Economics": [
        ("Inflation is:",
         ["A general rise in prices over time", "A fall in unemployment", "A rise in exports"], 0),
        ("Fiscal policy refers to:",
         ["Interest-rate decisions by the central bank", "Government taxation and spending", "Currency exchange rules"], 1),
        ("A budget deficit occurs when:",
         ["Revenue exceeds spending", "Spending exceeds revenue", "Debt is fully repaid"], 1),
    ],
    "Communication": [
        ("Why do speakers often group points in threes?",
         ["Law requires it", "Triads are easy to remember and sound complete", "Audiences dislike pairs"], 1),
        ("A hostile question is best handled by:",
         ["Attacking the questioner", "Ignoring it", "Briefly acknowledging it, then bridging to your message honestly"], 2),
        ("The main job of an opening line is to:",
         ["List your credentials", "Earn attention and connect with the audience", "Summarise the whole talk"], 1),
    ],
    "Ethics & accountability": [
        ("A conflict of interest exists when:",
         ["You disagree with your party", "A private interest could improperly influence a public duty",
          "You are outvoted"], 1),
        ("Accountability means:",
         ["Blaming subordinates", "Being answerable for decisions and outcomes", "Avoiding controversy"], 1),
        ("After a public mistake, the strongest move is to:",
         ["Deny until proven", "Own it, fix it, explain what changes", "Wait for the news cycle to end"], 1),
    ],
    "Diplomacy & negotiation": [
        ("Soft power is influence through:",
         ["Military force", "Attraction: culture, values, credibility", "Trade sanctions"], 1),
        ("BATNA stands for:",
         ["Best alternative to a negotiated agreement", "Basic agreement to national action",
          "Balanced approach to negotiated allies"], 0),
        ("Looking at interests behind positions helps you:",
         ["Find trades that create value for both sides", "Win by exhaustion", "Avoid the other side"], 0),
    ],
}

SCENARIOS = [
    {
        "title": "The hostile town hall",
        "text": "A resident shouts that your party has ignored their neighbourhood for years. Cameras are rolling.",
        "options": [
            ("Defend the record with statistics.", {"Empathy & listening": -1, "Media & image": 0},
             "Facts matter, but leading with them can feel dismissive before the person feels heard."),
            ("Acknowledge the frustration, ask what hurts most, then commit to one concrete follow-up.",
             {"Empathy & listening": 2, "Integrity": 1, "Media & image": 1},
             "Strong. Listening first lowers the temperature and a specific follow-up builds trust."),
            ("Move on to the next question.", {"Resilience": -1, "Integrity": -1},
             "Avoidance looks weak on camera and confirms the resident's complaint."),
        ],
    },
    {
        "title": "The ally who wants too much",
        "text": "A coalition partner threatens to walk unless you give them a ministry you wanted.",
        "options": [
            ("Concede everything to keep peace.", {"Negotiation": -1, "Strategic thinking": -1},
             "Short-term calm, long-term weakness. Others will learn that threats work."),
            ("Ask what they actually need, offer a package that meets that interest, and hold your core point.",
             {"Negotiation": 2, "Strategic thinking": 1},
             "Strong. You are trading on interests rather than positions."),
            ("Call their bluff publicly.", {"Emotional control": -1, "Resilience": 1},
             "Sometimes needed, but doing it publicly first burns the relationship."),
        ],
    },
    {
        "title": "The leaked mistake",
        "text": "A journalist has evidence of an error in a report your office published. It will run tonight.",
        "options": [
            ("Issue a clear statement now: what went wrong, the correction, and the safeguard.",
             {"Integrity": 2, "Media & image": 1, "Resilience": 1},
             "Strong. Getting ahead of the story with ownership usually limits the damage."),
            ("Say nothing and prepare a denial.", {"Integrity": -2},
             "High risk. If the evidence is solid, a denial turns a mistake into a scandal."),
            ("Blame a junior staffer.", {"Integrity": -2, "Emotional control": -1},
             "Leaders absorb responsibility. This also damages team loyalty."),
        ],
    },
]

GIVE_IDEAS = [
    "Introduce two people in your network who should know each other.",
    "Share a useful article or report with a short note on why it matters to them.",
    "Publicly credit someone for their work.",
    "Offer a skill or an hour of help on their project.",
    "Congratulate them on a milestone or remember a personal detail.",
    "Recommend them for a speaking slot, committee, or job.",
]

TIERS = {"A · Inner circle": 14, "B · Key allies": 30, "C · Wider network": 90}

FILLERS = ["um", "uh", "like", "you know", "basically", "actually", "literally", "kind of", "sort of"]

# --------------------------------------------------------------------------
# Data layer
# --------------------------------------------------------------------------
def default_db():
    return {
        "xp": 0,
        "traits": {t: 5.0 for t in TRAITS},
        "habits": {},
        "contacts": [],
        "ledger": [],
        "journal": [],
        "quiz": {},
        "sims": [],
        "drills": {},
    }


def load_db():
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text())
            base = default_db()
            base.update(data)
            for t in TRAITS:
                base["traits"].setdefault(t, 5.0)
            return base
        except (json.JSONDecodeError, OSError):
            pass
    return default_db()


def save_db():
    try:
        DATA_FILE.write_text(json.dumps(st.session_state.db, indent=2))
    except OSError:
        st.warning("Could not save to disk. Use the backup download in the sidebar.")


if "db" not in st.session_state:
    st.session_state.db = load_db()
db = st.session_state.db


def add_xp(n):
    db["xp"] = max(0, db["xp"] + n)


def bump_trait(trait, delta):
    db["traits"][trait] = round(min(10.0, max(1.0, db["traits"][trait] + delta)), 2)


def level_info():
    xp = db["xp"]
    idx = max(i for i, (need, _) in enumerate(LEVELS) if xp >= need)
    name = LEVELS[idx][1]
    if idx + 1 < len(LEVELS):
        nxt_need, nxt_name = LEVELS[idx + 1]
        pct = (xp - LEVELS[idx][0]) / (nxt_need - LEVELS[idx][0])
        return name, nxt_name, nxt_need - xp, pct
    return name, None, 0, 1.0


def streak():
    days, d, count = db["habits"], date.today(), 0
    if len(days.get(d.isoformat(), [])) < 3:
        d -= timedelta(days=1)
    while len(days.get(d.isoformat(), [])) >= 3:
        count += 1
        d -= timedelta(days=1)
    return count


def contact_df():
    rows = []
    for c in db["contacts"]:
        led = [e for e in db["ledger"] if e["contact"] == c["name"]]
        gives = sum(1 for e in led if e["type"] == "Give")
        takes = sum(1 for e in led if e["type"] == "Take")
        last = max([e["date"] for e in led] + [c["added"]])
        due = datetime.fromisoformat(last).date() + timedelta(days=TIERS[c["tier"]])
        if takes > gives:
            status = "Invest first: you have asked more than given"
        elif gives - takes >= 3:
            status = "Goodwill banked: fine to make an ask"
        else:
            status = "Balanced"
        rows.append({"Name": c["name"], "Role": c["role"], "Tier": c["tier"], "Gives": gives,
                     "Asks": takes, "Last contact": last, "Follow up by": due.isoformat(),
                     "Status": status})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def page_dashboard():
    st.title("Statecraft")
    name, nxt, to_go, pct = level_info()
    sub = f"{to_go} XP to {nxt}" if nxt else "Highest rank reached"
    st.markdown(
        f"""<div class="rank"><h2>{name}</h2><p>{db['xp']} XP · {sub}</p>
        <div class="bar"><span style="width:{int(pct*100)}%"></span></div></div>""",
        unsafe_allow_html=True,
    )
    df = contact_df()
    gives = int(df["Gives"].sum()) if not df.empty else 0
    asks = int(df["Asks"].sum()) if not df.empty else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Habit streak", f"{streak()} days")
    c2.metric("Network size", len(db["contacts"]))
    c3.metric("Gives : Asks", f"{gives} : {asks}")
    c4.metric("Simulations played", len(db["sims"]))

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Trait profile")
        labels = list(db["traits"].keys())
        vals = [db["traits"][t] for t in labels]
        fig = go.Figure(go.Scatterpolar(
            r=vals + vals[:1], theta=labels + labels[:1], fill="toself",
            line=dict(color="#b9852c", width=2), fillcolor="rgba(185,133,44,0.25)"))
        fig.update_layout(
            polar=dict(radialaxis=dict(range=[0, 10], tickfont=dict(size=10))),
            showlegend=False, margin=dict(l=40, r=40, t=20, b=20), height=380,
            paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Public Sans", color="#12203a"))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Today's focus")
        weakest = min(db["traits"], key=db["traits"].get)
        st.markdown(
            f"""<div class="panel"><b>Weakest trait: {weakest}</b> ({db['traits'][weakest]}/10)<br>
            <span class="muted">Try this drill: {TRAITS[weakest][0]}</span></div>""",
            unsafe_allow_html=True)
        if asks > gives:
            st.markdown("""<div class="panel warn"><b>Networking check</b><br>
            <span class="muted">You have asked more than you have given. Do a give today.</span></div>""",
                        unsafe_allow_html=True)
        if not df.empty:
            overdue = df[df["Follow up by"] <= date.today().isoformat()]
            if not overdue.empty:
                names = ", ".join(overdue["Name"].head(5))
                st.markdown(f"""<div class="panel warn"><b>Follow-ups due</b><br>
                <span class="muted">{names}</span></div>""", unsafe_allow_html=True)


def page_traits():
    st.title("Trait training")
    st.caption("Rate yourself honestly, then do one drill a day on your weakest trait.")
    with st.expander("Self-assessment (1 to 10)"):
        with st.form("assess"):
            cols = st.columns(2)
            new = {}
            for i, t in enumerate(TRAITS):
                new[t] = cols[i % 2].slider(t, 1.0, 10.0, float(db["traits"][t]), 0.5)
            if st.form_submit_button("Save assessment"):
                db["traits"].update(new)
                add_xp(10)
                save_db()
                st.success("Assessment saved. +10 XP")
    trait = st.selectbox("Choose a trait", list(TRAITS), index=list(TRAITS).index(min(db["traits"], key=db["traits"].get)))
    st.metric("Current score", f"{db['traits'][trait]} / 10")
    today = date.today().isoformat()
    done = db["drills"].setdefault(today, [])
    for i, drill in enumerate(TRAITS[trait]):
        key = f"{trait}:{i}"
        c1, c2 = st.columns([5, 1])
        c1.markdown(f'<div class="panel">{drill}</div>', unsafe_allow_html=True)
        if key in done:
            c2.write("Done today")
        elif c2.button("Done", key=f"drill_{key}"):
            done.append(key)
            bump_trait(trait, 0.2)
            add_xp(15)
            save_db()
            st.rerun()


def page_academy():
    st.title("Knowledge academy")
    st.caption("Short quizzes on core subjects. Add your own country's constitution and laws as you go.")
    module = st.selectbox("Module", list(QUIZZES))
    best = db["quiz"].get(module)
    if best is not None:
        st.write(f"Best score: {best}/{len(QUIZZES[module])}")
    with st.form(f"quiz_{module}"):
        answers = []
        for i, (q, opts, _) in enumerate(QUIZZES[module]):
            answers.append(st.radio(f"{i + 1}. {q}", opts, index=None, key=f"{module}{i}"))
        submitted = st.form_submit_button("Submit answers")
    if submitted:
        if any(a is None for a in answers):
            st.error("Answer every question before submitting.")
            return
        score = 0
        for (q, opts, correct), a in zip(QUIZZES[module], answers):
            if opts.index(a) == correct:
                score += 1
            else:
                st.markdown(f'<div class="panel warn">{q}<br><span class="muted">Correct answer: {opts[correct]}</span></div>',
                            unsafe_allow_html=True)
        gain = max(0, score - (best or 0)) * 10
        if gain:
            add_xp(gain)
        db["quiz"][module] = max(score, best or 0)
        save_db()
        st.success(f"You scored {score}/{len(QUIZZES[module])}. +{gain} XP")


def syllables(word):
    w = word.lower()
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1:
        n -= 1
    return max(n, 1)


def page_speech():
    st.title("Speech lab")
    st.caption("Paste a speech draft. You will get delivery stats and rhetoric feedback.")
    text = st.text_area("Your speech", height=260)
    if st.button("Analyse") and text.strip():
        words = re.findall(r"[A-Za-z']+", text)
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        n_w, n_s = len(words), max(len(sentences), 1)
        syl = sum(syllables(w) for w in words)
        flesch = 206.835 - 1.015 * (n_w / n_s) - 84.6 * (syl / max(n_w, 1))
        lower = text.lower()
        we = len(re.findall(r"\b(we|our|us|together)\b", lower))
        i_ = len(re.findall(r"\b(i|my|me|mine)\b", lower))
        fill = sum(len(re.findall(rf"\b{re.escape(f)}\b", lower)) for f in FILLERS)
        threes = len(re.findall(r"\b\w+,\s+\w+,?\s+and\s+\w+", lower))
        questions = text.count("?")
        starts = [" ".join(s.split()[:2]).lower() for s in sentences if len(s.split()) > 2]
        repeats = sum(1 for a, b in zip(starts, starts[1:]) if a == b)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Words", n_w)
        c2.metric("Speaking time", f"{n_w / 130:.1f} min")
        c3.metric("Readability", f"{flesch:.0f}")
        c4.metric("Avg sentence", f"{n_w / n_s:.0f} words")

        tips = []
        if n_w / n_s > 22:
            tips.append(("warn", "Sentences are long. Aim for about 15 words on average so listeners can follow."))
        if flesch < 60:
            tips.append(("warn", "Readability is low for a general audience. Use shorter words."))
        else:
            tips.append(("good", "Readability suits a general audience."))
        if we >= i_:
            tips.append(("good", f"Inclusive language: {we} 'we/our/us' vs {i_} 'I/my/me'."))
        else:
            tips.append(("warn", f"You say 'I' ({i_}) more than 'we' ({we}). Shift credit and purpose to the audience."))
        if fill:
            tips.append(("warn", f"{fill} filler word(s) found. Cut them or replace with a pause."))
        tips.append(("good" if threes else "warn",
                     f"Rule of three used {threes} time(s). Try one memorable triad." if not threes
                     else f"Rule of three used {threes} time(s). Memorable."))
        tips.append(("good" if questions else "warn",
                     f"{questions} rhetorical question(s)." if questions else "No questions. One well-placed question engages the room."))
        tips.append(("good" if repeats else "warn",
                     "Repetition of sentence openings (anaphora) detected: strong rhythm." if repeats
                     else "Try repeating a phrase at the start of consecutive sentences for rhythm."))
        for kind, msg in tips:
            st.markdown(f'<div class="panel {kind}">{msg}</div>', unsafe_allow_html=True)
        add_xp(10)
        bump_trait("Public speaking", 0.1)
        save_db()


def page_sim():
    st.title("Decision simulator")
    st.caption("Practise leadership calls under pressure. Choices shift your trait scores.")
    sc = st.selectbox("Scenario", SCENARIOS, format_func=lambda s: s["title"])
    st.markdown(f'<div class="panel">{sc["text"]}</div>', unsafe_allow_html=True)
    choice = st.radio("What do you do?", [o[0] for o in sc["options"]], index=None)
    if st.button("Commit decision") and choice:
        for text, effects, feedback in sc["options"]:
            if text == choice:
                for t, d in effects.items():
                    bump_trait(t, d * 0.2)
                gain = 20 if any(v > 0 for v in effects.values()) else 5
                add_xp(gain)
                db["sims"].append({"date": date.today().isoformat(), "scenario": sc["title"], "choice": text})
                save_db()
                kind = "good" if gain == 20 else "warn"
                st.markdown(f'<div class="panel {kind}">{feedback}<br><span class="muted">+{gain} XP</span></div>',
                            unsafe_allow_html=True)


def page_network():
    st.title("Network & reciprocity")
    st.caption("Give first, ask second. Track both sides so goodwill stays balanced.")
    tab1, tab2, tab3 = st.tabs(["People", "Log a give or ask", "Insights"])
    with tab1:
        with st.form("add_contact", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name")
            role = c2.text_input("Role / organisation")
            tier = st.selectbox("Tier", list(TIERS))
            if st.form_submit_button("Add person"):
                if not name.strip():
                    st.error("Enter a name.")
                elif any(c["name"] == name.strip() for c in db["contacts"]):
                    st.error("That person is already in your network.")
                else:
                    db["contacts"].append({"name": name.strip(), "role": role.strip(), "tier": tier,
                                           "added": date.today().isoformat()})
                    add_xp(5)
                    save_db()
                    st.success(f"Added {name.strip()}.")
        df = contact_df()
        if df.empty:
            st.info("Add your first contact to start tracking.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
    with tab2:
        if not db["contacts"]:
            st.info("Add a person first.")
        else:
            with st.form("ledger", clear_on_submit=True):
                who = st.selectbox("Person", [c["name"] for c in db["contacts"]])
                kind = st.radio("Type", ["Give", "Take"], horizontal=True,
                                help="Give = you helped them. Take = you asked something of them.")
                what = st.text_input("What was it?")
                if st.form_submit_button("Log it"):
                    db["ledger"].append({"date": date.today().isoformat(), "contact": who,
                                         "type": kind, "what": what.strip()})
                    add_xp(20 if kind == "Give" else 5)
                    save_db()
                    st.success("Logged." + (" +20 XP for giving." if kind == "Give" else ""))
            st.markdown("**Ideas for a give**")
            for idea in GIVE_IDEAS:
                st.markdown(f"- {idea}")
    with tab3:
        df = contact_df()
        if df.empty:
            st.info("Insights appear once you have contacts.")
        else:
            for _, r in df.iterrows():
                kind = "warn" if r["Status"].startswith("Invest") else "good"
                st.markdown(
                    f'<div class="panel {kind}"><b>{r["Name"]}</b> ({r["Tier"]}) · {r["Gives"]} gives, {r["Asks"]} asks<br>'
                    f'<span class="muted">{r["Status"]}. Follow up by {r["Follow up by"]}.</span></div>',
                    unsafe_allow_html=True)


def page_habits():
    st.title("Daily habits")
    today = date.today().isoformat()
    done = db["habits"].setdefault(today, [])
    st.write(f"Complete 3 or more habits a day to keep your streak. Current streak: **{streak()} days**.")
    for habit, xp in HABITS.items():
        checked = habit in done
        new = st.checkbox(f"{habit}  (+{xp} XP)", value=checked, key=f"h_{habit}")
        if new and not checked:
            done.append(habit)
            add_xp(xp)
            save_db()
            st.rerun()
        elif not new and checked:
            done.remove(habit)
            add_xp(-xp)
            save_db()
            st.rerun()

    st.subheader("Evening reflection")
    prompt = st.selectbox("Prompt", [
        "What did I do today that a leader would be proud of?",
        "Where did I listen less than I should have?",
        "Whom did I help, and whom should I thank?",
        "What decision am I avoiding, and why?",
    ])
    entry = st.text_area("Your reflection", height=120)
    if st.button("Save reflection") and entry.strip():
        db["journal"].append({"date": today, "prompt": prompt, "text": entry.strip()})
        add_xp(10)
        save_db()
        st.success("Saved. +10 XP")
    for j in reversed(db["journal"][-5:]):
        st.markdown(f'<div class="panel"><span class="muted">{j["date"]} · {j["prompt"]}</span><br>{j["text"]}</div>',
                    unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Navigation & backup
# --------------------------------------------------------------------------
PAGES = {
    "Dashboard": page_dashboard,
    "Trait training": page_traits,
    "Knowledge academy": page_academy,
    "Speech lab": page_speech,
    "Decision simulator": page_sim,
    "Network & reciprocity": page_network,
    "Daily habits": page_habits,
}

with st.sidebar:
    st.markdown("## 🏛️ Statecraft")
    choice = st.radio("Navigate", list(PAGES), label_visibility="collapsed")
    st.divider()
    st.download_button("Download backup", json.dumps(db, indent=2), "statecraft_backup.json", "application/json")
    up = st.file_uploader("Restore backup", type="json")
    if up is not None and st.button("Restore now"):
        try:
            restored = default_db()
            restored.update(json.load(up))
            st.session_state.db = restored
            save_db()
            st.rerun()
        except (json.JSONDecodeError, UnicodeDecodeError):
            st.error("That file is not a valid backup.")

PAGES[choice]()
