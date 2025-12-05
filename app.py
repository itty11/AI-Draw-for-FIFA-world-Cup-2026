import streamlit as st
from pathlib import Path
import time
import json
import random
import copy
import base64
import streamlit.components.v1 as components
from io import BytesIO
from PIL import Image
from pathlib import Path
from fpdf import FPDF
import os


# ---------------------------
# Paths & Files
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
POTS_FILE = DATA_DIR / "pots.json"
GROUPS_FILE = DATA_DIR / "groups.json"
CONF_RULES_FILE = DATA_DIR / "confederation_rules.json"
CONFIRMED_FILE = DATA_DIR / "confirmed_teams.json"
OUT_FILE = DATA_DIR / "groups_out.json"
FLAGS_FILE = DATA_DIR / "flags.json"
QUALIFIERS_FILE = DATA_DIR / "qualifiers.json"
LOGO_FILE = BASE_DIR / "assets" / "2026_FIFA_World_Cup_emblem.jpg"
FONTS_DIR = Path(r"D:\AI Projects\AI-Powered Draw System (Exclusively for FIFA 2026)\dejavu-fonts-ttf-2.37\ttf")
DEJAVU_PATH = FONTS_DIR / "fonts" / "DejaVuSans.ttf"
DATA_DIR = Path(__file__).resolve().parent / "data"
NAMES_FILE = DATA_DIR / "names.json"

with open(NAMES_FILE, "r", encoding="utf-8") as f:
    TEAM_FULL_NAMES = json.load(f)

# ---------------------------
# Utilities
# ---------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Safe loader for optional files
def safe_load(path):
    p = Path(path)
    if p.exists():
        try:
            return load_json(p)
        except Exception:
            return None
    return None

def generate_pdf(groups_result, logo_path=None):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.add_font("DejaVu", "", str(FONTS_DIR / "fonts" / "DejaVuSans.ttf"), uni=True)
    pdf.add_font("DejaVu", "B", str(FONTS_DIR / "fonts" / "DejaVuSans-Bold.ttf"), uni=True)
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 12, "FIFA World Cup 2026 - Official Draw Results", ln=True, align="C")
    pdf.ln(10)

    # Logo
    if logo_path and Path(logo_path).exists():
        logo_w = 35   
        logo_h = 35   
        page_width = 210  

        # Center horizontally
        logo_x = (page_width - logo_w) / 2  
        logo_y = 28  

        pdf.image(str(LOGO_FILE), x=logo_x, y=logo_y, w=logo_w, h=logo_h)
        pdf.ln(40)

    # Table Header
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(35, 10, "Group", border=1, align="C", fill=True)
    pdf.cell(80, 10, "Team", border=1, align="C", fill=True)
    pdf.cell(35, 10, "Flag", border=1, align="C", fill=True)
    pdf.ln()

    # Table content
    pdf.set_font("DejaVu", "", 12)

    for group, slots in groups_result.items():
        for pos in ["1", "2", "3", "4"]:
            short = slots.get(pos, "")
            full = TEAM_FULL_NAMES.get(short, short)

            # Group name (only printed on first row of group)
            pdf.cell(35, 10, group if pos == "1" else "", border=1)
            pdf.cell(120, 10, full, border=1)
            pdf.ln()

    # Return bytes
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()

# ---------------------------
# Flag helpers
# ---------------------------
flags_map = safe_load(FLAGS_FILE) or {}

def normalize_team(name: str) -> str:
    if not name:
        return ""
    s = str(name).strip()
    # accept already 2-4 char codes
    if len(s) <= 4 and s.isalpha():
        return s.upper()
    # simple mapping for known long names
    aliases = {
        "NEW CALEDONIA": "NCL",
        "DR CONGO": "COD",
        "DRCONGO": "COD",
        "N. MACEDONIA": "MKD",
        "NORTHERN IRELAND": "NIR",
    }
    return aliases.get(s.upper(), s.upper())

def get_flag_url(code_or_name: str):
    if not code_or_name:
        return None
    key = normalize_team(str(code_or_name))
    
    # direct lookup
    if key in flags_map:
        return flags_map[key]
    # case-insensitive keys
    for k, v in flags_map.items():
        if k.upper() == key:
            return v
            
    # --- New, Targeted Placeholder Logic ---
    if key.startswith("WINNER_IC_"):
        # Use the UN flag defined for the Intercontinental winner
        return flags_map.get("IC_WINNER_1") 
    
    if key.startswith("WINNER_D_SF") or key.startswith("WINNER_"):
        # Assume generic WINNER_ placeholders are UEFA for now (like WINNER_D_SF2)
        return flags_map.get("UEFA_PLAYOFF_WINNER") 

    # Handle the main IC/UEFA slot placeholders
    if key == "IC_WINNER_1" or key == "IC_WINNER_2" or key.startswith("IC_"):
        return flags_map.get("IC_WINNER_1")
    
    if key.startswith("UEFA_") or key == "UEFA_PLAYOFF_WINNER":
        return flags_map.get("UEFA_PLAYOFF_WINNER")
        
    return flags_map.get("TBD") # Final fallback

def flag_img_html(code_or_name, width=22, height=14, style_extra=""):
    url = get_flag_url(code_or_name)
    if not url:
        return ""
    return f"<img src='{url}' width='{width}' height='{height}' style='margin-right:8px; vertical-align:middle; {style_extra}'/>"


# ---------------------------
# Optimized Draw Engine
# ---------------------------
class DrawEngine:
    """Optimized backtracking draw engine with heuristic ordering."""
    def __init__(self, pots: dict, groups_template: dict, conf_rules: dict, seed=None):
        # expected pots: {'pot1':[...], 'pot2':[...]}
        # groups_template: {'groups': {'A': {'1': None,...}, ...}}
        self.pots = {k: list(v) for k, v in pots.items()}
        self.groups_template = copy.deepcopy(groups_template.get("groups", {}))
        self.groups = sorted(self.groups_template.keys())
        self.conf_rules = conf_rules or {}
        self.uefa_max = conf_rules.get("confederations", {}).get("UEFA", {}).get("max_per_group", 2)
        self.uefa_min = conf_rules.get("draw_rules", {}).get("uefa_limit", {}).get("min", None)
        if seed is not None:
            random.seed(seed)

    def team_confed(self, team_id: str):
        # small heuristic: map known prefixes
        if not team_id:
            return "UNKNOWN"
        t = str(team_id).upper()
        if t.startswith("UEFA"):
            return "UEFA"
        # interconf placeholders
        if t.startswith("IC_") or t.startswith("INTER"):
            return "MIXED"
        # try conf file via confirmed teams if present
        if CONFIRMED_FILE.exists():
            data = safe_load(CONFIRMED_FILE)
            if data:
                for item in data.get("teams", []) + data.get("slots", []):
                    if item.get("id") == t or item.get("slot_id") == t:
                        return item.get("confederation") or "UNKNOWN"
        # default fallbacks by region codes
        europe_codes = set(["ENG","FRA","ESP","ITA","GER","POR","NED","POL","SCO","WAL","CRO","SUI","BEL","DEN","SWE","NOR","FIN","ISL","IRL","NIR","CZE","SVK","SVN","AUT","HUN","ROU","GEO","KOS","MKD","ALB","BIH","LTU","LVA","EST","LUX","MLT","BLR"])
        if t in europe_codes:
            return "UEFA"
        africa = set(["CMR","SEN","MAR","TUN","NGA","EGY","CIV","GHA"])
        if t in africa:
            return "CAF"
        return "UNKNOWN"

    def violates_pathway(self, team, group, current):
        pairs = [("ESP","ARG"),("FRA","ENG")]
        for a,b in pairs:
            if team==a or team==b:
                # find counterpart
                for g, slots in current.items():
                    if any(sl== (b if team==a else a) for sl in slots.values()):
                        # same half?
                        half = lambda grp: 0 if ord(grp)-ord('A')<6 else 1
                        if half(g) == half(group):
                            return True
        return False

    def count_confed_in_group(self, group_slots, confed):
        cnt=0
        for s in group_slots.values():
            if s and self.team_confed(s)==confed:
                cnt+=1
        return cnt

    def satisfies(self, team, group, current_groups):
        confed = self.team_confed(team)
        # max per confed
        if confed!='UNKNOWN' and confed!='MIXED':
            allowed = self.conf_rules.get("confederations", {}).get(confed, {}).get("max_per_group", 1)
            if confed=="UEFA":
                allowed = self.uefa_max
            if self.count_confed_in_group(current_groups[group], confed) + 1 > allowed:
                return False
        # pathway
        if self.violates_pathway(team, group, current_groups):
            return False
        return True

    def place_pot_greedy(self, pot_list, pot_number, current_groups):
        # order groups by number of teams (fill emptiest first)
        groups_order = sorted(self.groups, key=lambda g: sum(1 for v in current_groups[g].values() if v))
        for team in pot_list:
            placed=False
            random.shuffle(groups_order)
            # try best-fit
            for g in groups_order:
                if current_groups[g][str(pot_number)] is not None:
                    continue
                if not self.satisfies(team,g,current_groups):
                    continue
                current_groups[g][str(pot_number)] = team
                placed=True
                break
            if not placed:
                return False
        return True

    def run_draw(self, max_attempts=50):
        # try multiple attempts with random shuffles & greedy placement
        for attempt in range(max_attempts):
            current = copy.deepcopy(self.groups_template)
            # pot1: place hosts if any then randomize
            pot1 = list(self.pots.get('pot1', []))
            random.shuffle(pot1)
            # fill pot1 into empty '1' slots
            p1_groups = [g for g in self.groups if current[g]['1'] is None]
            for team, grp in zip(pot1, p1_groups):
                current[grp]['1'] = team
            # place pot2..4
            ok = True
            for i, potname in enumerate(['pot2','pot3','pot4'], start=2):
                pot_list = list(self.pots.get(potname, []))
                random.shuffle(pot_list)
                if not self.place_pot_greedy(pot_list, i, current):
                    ok=False
                    break
            if not ok:
                continue
            # final check
            if self.final_check(current):
                return current
        raise RuntimeError('No valid draw found')

    def final_check(self, final_groups):
        # ensure no None and confed rules
        for g in self.groups:
            slots = final_groups[g]
            if any(v is None for v in slots.values()):
                return False
            # count confeds
            confcount={}
            for v in slots.values():
                c=self.team_confed(v)
                confcount[c]=confcount.get(c,0)+1
            if confcount.get('UEFA',0) > self.uefa_max:
                return False
        return True

# light wrapper
def run_draw_engine(pots, groups_template, conf_rules, attempts=50, seed=None):
    engine = DrawEngine(pots, groups_template, conf_rules, seed=seed)
    return engine.run_draw(max_attempts=attempts)

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title='AI Draw for FIFA World Cup 2026', layout='wide')

# small CSS for gold theme
if LOGO_FILE.exists():
    logo_base64_main = base64.b64encode(open(LOGO_FILE, 'rb').read()).decode()
    st.markdown(
        f"<div style='display:flex; align-items:center; gap:15px;'><img src='data:image/jpeg;base64,{logo_base64_main}' width='70' style='margin-top:-10px;'/><h1 style='margin:0;'>AI Draw for FIFA World Cup 2026</h1></div>", 
        unsafe_allow_html=True
    )
    # Remove the extra st.title('AI Draw for FIFA World Cup 2026') line if it's duplicated.
else:
    st.title('AI Draw for FIFA World Cup 2026')

st.markdown("---")
st.subheader('📜 Official Draw Rules Summary')
with st.expander("Click to view full draw rules and constraints"):
    wiki_text = """
    > The draw is scheduled for December 5, 2025, at the Kennedy Center in Washington, D.C. (12:00 UTC−5/EST).
    > The 48 teams are divided into **four pots of 12** based on the November 2025 FIFA Men's World Ranking.
    > 
    > **Pot 1** consists of the three hosts and the top nine ranked teams. Pots 2, 3, and 4 contain the remaining teams by ranking.
    > The four **UEFA playoff** and two **inter-confederation playoff** winners (scheduled for March 2026) are automatically allocated to **Pot 4**.
    > 
    > ### Key Constraints:
    > * **Confederation Rule:** No group will have more than **one team** from the same confederation, **except UEFA**.
    > * **UEFA Rule:** Each group must have **either one or two UEFA teams** drawn into it.
    > * **Host Pre-Allocation:** >     * **Mexico** $\\to$ Group **A** (Position 1, opening match).
    >     * **Canada** $\\to$ Group **B** (Position 1).
    >     * **United States** $\\to$ Group **D** (Position 1).
    > * **Competitive Balance/Pathway:** To ensure two separate knockout bracket pathways, the pairs **Spain (1st)** & **Argentina (2nd)** and **France (3rd)** & **England (4th)** are drawn into groups on **opposite sides** of the bracket.
    > * **Inter-Confederation Winners** are subject to the confederation restriction.
    """
    st.markdown(wiki_text)
st.markdown("---")

# load data
pots_raw = safe_load(POTS_FILE)
if not pots_raw:
    st.error('pots.json missing in data/. Add your pots file and reload.')
    st.stop()

groups_template = safe_load(GROUPS_FILE) or {"groups": {}}
conf_rules = safe_load(CONF_RULES_FILE) or {}
qualifiers = safe_load(QUALIFIERS_FILE) or {}
flags_map = safe_load(FLAGS_FILE) or {}

# normalize pots dictionary
pots = pots_raw.get('pots') if isinstance(pots_raw, dict) and 'pots' in pots_raw else pots_raw

# Pots overview
st.subheader('🏅 Pots Overview')
cols = st.columns(4)
pot_keys = sorted(list(pots.keys()))
for i, key in enumerate(pot_keys):
    with cols[i%4]:
        st.markdown(f"<div class='card'><h4 class='hgold'>{key.capitalize()}</h4>", unsafe_allow_html=True)
        for t in pots[key]:
            url = get_flag_url(t) or ''
            if url:
                st.markdown(f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'><img src='{url}' width='24' height='16' style='border-radius:3px;'/><b style='color:#fff'>{t}</b></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"- {t}")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('---')

# Playoff paths (UEFA + Intercontinental)
st.subheader('⚔️ Playoff Paths (UEFA & Intercontinental)')
if qualifiers:
    uefa = qualifiers.get('uefa_playoffs') or {}
    if uefa:
        eu_html = flag_img_html('UEFA_PLAYOFF_WINNER', width=22, height=14)
        st.markdown(f"### {eu_html} UEFA Playoffs", unsafe_allow_html=True)
        for path, data in uefa.items():
            st.markdown(f"**{path}**")
            semis = data.get('semi_finals') or data.get('semi-finals') or []
            for m in semis:
                t1 = m.get('team1','')
                t2 = m.get('team2','')
                date = m.get('date','')
                st.markdown(f"{flag_img_html(t1)} <b>{t1}</b> vs {flag_img_html(t2)} <b>{t2}</b> <span class='small-muted'>({date})</span>", unsafe_allow_html=True)
            final = data.get('final')
            if final:
                st.markdown(f"Final: {flag_img_html(final.get('team1'))} <b>{final.get('team1')}</b> vs {flag_img_html(final.get('team2'))} <b>{final.get('team2')}</b>", unsafe_allow_html=True)
    ic = qualifiers.get('inter_confed_playoffs') or qualifiers.get('intercontinental_playoffs') or {}
    if ic:
        st.markdown('### 🌍 Intercontinental Playoffs')
        matches = ic.get('matches',{})
        for stage in ('semi_finals','finals'):
            items = matches.get(stage, [])
            if items:
                st.markdown(f"**{stage.replace('_',' ').title()}**")
                for m in items:
                    st.markdown(f"{flag_img_html(m.get('team1'))} <b>{m.get('team1')}</b> vs {flag_img_html(m.get('team2'))} <b>{m.get('team2')}</b> <span class='small-muted'>({m.get('date','')})</span>", unsafe_allow_html=True)
else:
    st.info('No qualifiers.json found — add it to data/ to render playoff paths.')

st.markdown('---')

# Draw controls
st.subheader('🎲 Run Draw')
left, right = st.columns([1,3])
with left:
    seed_checkbox = st.checkbox('Use fixed seed')
    seed = st.number_input('Seed', min_value=0, max_value=10_000_000, value=42)
    attempts = st.number_input('Max attempts', min_value=1, max_value=20000, value=200)
    run_btn = st.button('Run Draw Now 🏆')
with right:
    if 'pdf_trigger' not in st.session_state:
        st.session_state['pdf_trigger'] = False

# Run draw
if run_btn:
    st.session_state['pdf_trigger'] = False
    st.info('Running optimized draw engine — this may take a moment')
    try:
        groups_result = run_draw_engine(pots, groups_template, conf_rules, attempts=int(attempts), seed=(seed if seed_checkbox else None))
    except Exception as e:
        st.error(f'Engine failed: {e}')
        groups_result = None

    if not groups_result:
        st.error('No valid draw found. Try increasing attempts or check confederation rules.')
    else:
        st.success('Draw completed — saving results')
        save_json(OUT_FILE, {'groups': groups_result})
        st.session_state['groups_result'] = groups_result
        # animated reveal
        anim = """
        <div style='display:flex;align-items:center;gap:12px;'>
          <div style='font-size:20px;'>🏁</div>
          <div style='font-weight:700;color:#ffd166;'>Draw complete — revealing groups</div>
        </div>
        """
        st.markdown(anim, unsafe_allow_html=True)

# Show final groups
if 'groups_result' in st.session_state:
    st.subheader('📊 Final Groups')
    groups_result = st.session_state['groups_result']
    group_letters = sorted(groups_result.keys())
    
    # HTML structure for the grid and the print target ID
    results_html = "<div id='draw-results-container'>"
    results_html += "<div style='display:flex; flex-wrap:wrap; gap:16px;'>" # Container for groups
    gi = 0
    
    for g in group_letters:
        block = groups_result[g]
        
        # Build the card HTML
        html = f"""
        <div class='card' style='flex: 1 1 23%; min-width: 250px; background-color: #1a1a1a; padding: 20px;'>
            <h4 class='hgold' style='margin-bottom: 15px;'>Group {g}</h4>
        """
        for pos in ['1','2','3','4']:
            t = block.get(pos,'')
            url = get_flag_url(t) or ''
            html += "<div style='display:flex;align-items:center;margin-bottom:8px;'>"
            if url:
                # Use slightly larger flags for the final groups display
                html += f"<img src='{url}' width='32' height='21' style='margin-right:12px;border-radius:4px;border:1px solid #333;'/>"
            html += f"<span style='color:#fff;font-weight:600;'>{t}</span></div>"
        html += '</div>'
        
        results_html += html
        gi += 1
        
    results_html += "</div>" # Close the groups grid container
    results_html += "</div>" # Close the draw-results-container
    
    # Display the HTML results using Streamlit's markdown
    st.markdown(results_html, unsafe_allow_html=True)
    
    # Add the Print/Download Button (separated from the HTML)
    st.subheader("📄 Export Results")

if st.button("⬇️ Generate PDF"):
    groups_result = st.session_state.get("groups_result")
    if groups_result:
        pdf_bytes = generate_pdf(groups_result, LOGO_FILE)

        st.download_button(
            label="📄 Click to Download PDF",
            data=pdf_bytes,
            file_name="FIFA_2026_Draw.pdf",
            mime="application/pdf"
        )

st.markdown('---')

# Footer
st.markdown(
    """
    <style>
    .block-container {
        padding-bottom: 1.5rem;   /* reduce bottom space */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

footer_html = """
<div style="text-align:center; margin-top:0px;">
    <span style="color:#9aa0a6; font-size:13px;">
        © 2025 AI Draw for 2026 FIFA World Cup by <b>Ittyavira C Abraham</b>
    </span>
    <br>
    <a href="https://www.linkedin.com/in/ittyavira-c-abraham-5435621b7/" target="_blank">
        <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/linkedin.svg"
             width="18" style="margin-right:10px; filter: invert(70%);" />
    </a>
    <a href="https://github.com/itty11" target="_blank">
        <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/github.svg"
             width="18" style="filter: invert(70%);" />
    </a>
</div>
"""

st.markdown(footer_html, unsafe_allow_html=True)

