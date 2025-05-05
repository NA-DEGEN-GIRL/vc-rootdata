import requests
import sys
import re
from thefuzz import fuzz
from api_key import API_KEY_ROOTDATA, telegram_bot_token, admin_id, allowed_chat_id
from telegram.ext import Application, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes


PROJECT_FUZZY_THRESHOLD = 100
TIER2_FUZZY_THRESHOLD = 85

search_url = 'https://api.rootdata.com/open/ser_inv'
search_headers = {
    'apikey': API_KEY_ROOTDATA,
    'Content-Type': 'application/json'
}

tier1 = {
    name.lower() for name in [
        'Raj Gokal', 'VanEck', 'Balaji Srinivasan', 'a16z CSX', 'Santiago Roel Santos',
        'DragonFly', 'Coinbase Ventures', 'YZi Labs', 'The Spartan Group',
        'Blockchain Capital', 'Galaxy', 'Anatoly Yakovenko', 'Andreessen Horowitz',
        'Sandeep Nailwal', 'Paradigm', 'Delphi Digital', 'Pantera Capital',
        'Stani Kulechov', 'Multicoin Capital', 'Circle Ventures', 'Bryan Pellegrino',
        'HashKey Capital', 'Polychain', 'Sequoia Capital', 'ConsenSys', 'BlackRock',
        'Paul Veradittakit', 'Vitalik Buterin', 'Alex Svanevik', 'Y Combinator', 'Arthur Hayes'
    ]
}


tier2_list = [
  "Alliance DAO", "Hack VC", "Avalanche Foundation", "Solana Ventures", "MH Ventures", "Mirana Ventures", "1kx", "MEXC Ventures", "OKX Ventures", "P2 Ventures (Polygon Ventures)",
  "Framework Ventures", "Electric Capital", "Distributed Global", "Robot Ventures", "Mechanism Capital", "Amber Group", "Maven 11 Capital", "MEXC", "DWF Labs", "Stellar Development Foundation",
  "GSR", "Draper Associates", "Wintermute", "Ryze Labs (Sino Global Capital)", "Arrington XRP Capital", "Nascent", "CMS Holdings", "CMT Digital", "Mapleblock Capital", "Alchemy",
  "Triton Capital (Kraken Ventures)", "Tether", "Variant", "Fenbushi Capital", "Union Square Ventures (USV)", "Ripple", "Draper Dragon", "RockawayX", "Paul Taylor", "Franklin Bi",
  "Republic", "Quantstamp", "Jump Crypto", "Greenfield Capital", "IVC", "6th Man Ventures", "Immutable", "Hypersphere Ventures", "Lightspeed Venture Partners", "Standard Crypto",
  "CoinFund", "Ribbit Capital", "Digital Currency Group (DCG)", "Sfermion", "KuCoin Labs", "Kenetic Capital", "Accel", "HongShan (Sequoia China)", "Jane Street Capital", "MGX",
  "Slow Ventures", "C² Ventures", "Boost VC", "Mask Network", "KuCoin Ventures", "IOSG Ventures", "Blockchain.com", "a16z speedrun", "Ethereum Foundation", "BNB Chain", "Web3 Foundation",
  "ParaFi Capital", "Highland Capital Partners", "Shima Capital", "SamsungNext", "GV Google Ventures", "eGirl Capital", "Fabric Ventures", "Bitscale Capital", "Hashed Fund", "The LAO",
  "Bain Capital Crypto", "SoftBank", "The Sandbox", "SwissBorg Ventures", "Yield Guild Games (YGG)", "1confirmation", "Tribe Capital", "Redpoint", "Double Peak", "SafePal",
  "Impossible Finance", "FBG Capital", "Tiger Global Management", "Cardano Foundation", "Visa", "GBV Capital", "TRON Foundation", "Merit Circle", "Jump Capital", "Genblock Capital",
  "Peak XV Partners(Sequoia India)", "Ava Labs", "Genesis", "Eden Block", "IDEO CoLab Ventures", "The a16z Cultural Leadership Fund", "Polygon Studios", "Jump Trading", "J.P. Morgan",
  "Temasek", "Alibaba Group", "QCP Capital", "DHVC", "LG Technology Ventures", "Robinhood", "DeFiance Capital", "Ascensive Assets", "Galxe", "1inch", "PetRock Capital", "Goldman Sachs",
  "Greenoaks Capital", "Susquehanna International Group", "Icetea Labs", "GoldenTree Asset Management", "Epic Games", "Seven Seven Six", "Dapper Labs", "Greylock Partners", "S&P Global",
  "Ericsson Ventures", "Horizons Ventures", "Overstock", "Samsung", "Kabbage", "Nuri", "Ubisoft Entertainment SA", "Take-Two Interactive Software", "Marshall Wace", "McKinsey & Company",
  "Bitstamp", "NBA", "Osaka Gas", "Lightspeed China Partners", "Divergence Ventures", "HTC", "Bandai Namco Entertainment", "Kohlberg Kravis Roberts (KKR)", "Revolution’s Rise of the Rest Seed Fund",
  "Future Art", "Infinity Force", "RTP Global", "Twitter", "Institutional Venture Partners (IVP)", "Canaccord Genuity", "Stifel Financial Corp", "Binance.US", "Morgan Stanley",
  "Silicon Valley Bank", "Fifth Era", "Meta", "Saigon TradeCoin", "Sequoia Heritage", "Polaroid", "Google for Startups", "Hacken", "SeedInvest", "Japan Finance", "AMD",
  "Invest Nebraska", "Samsung Venture Investment", "Idinvest Partners"
]

def normalize(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())

def generate_tier2_variants(names):
    variants = set()
    for name in names:
        norm = normalize(name)
        variants.add(norm)
        match = re.search(r'^(.*?)(\s*\(.*?\))$', name)
        if match:
            base = match.group(1).strip()
            paren = match.group(2).strip("()")
            variants.add(normalize(base))
            variants.add(normalize(paren))
    return variants

tier2_set = generate_tier2_variants(tier2_list)

def get_project_ids(data):
    return [item.get('id') for item in data.get('data', []) if item.get('type') == 1]

def fetch_project_detail(project_id):
    detail_url = 'https://api.rootdata.com/open/get_item'
    detail_payload = {
        'project_id': project_id,
        'include_team': True,
        'include_investors': True
    }
    detail_headers = {
        'apikey': API_KEY_ROOTDATA,
        'Content-Type': 'application/json'
    }
    resp = requests.post(detail_url, json=detail_payload, headers=detail_headers)
    return resp.json().get('data', {})


def is_tier2(name):
    norm_name = normalize(name)
    if norm_name in tier2_set:
        return True
    for t2 in tier2_list:
        t2_variants = [t2]
        match = re.search(r'^(.*?)(\s*\(.*?\))$', t2)
        if match:
            t2_variants.append(match.group(1).strip())
            t2_variants.append(match.group(2).strip("()"))
        for variant in t2_variants:
            if not variant:
                continue
            variant_norm = normalize(variant)
            if not variant_norm:
                continue
            score = fuzz.ratio(norm_name, variant_norm)
            if score >= TIER2_FUZZY_THRESHOLD:
                return True
    return False


def print_filtered_investors(investors):
    t1_set, t2_set, other_set = set(), set(), set()
    for inv in investors:
        name = inv.get("name", "").strip()
        name_lc = name.lower()
        if name_lc in tier1:
            t1_set.add(name)
        elif is_tier2(name):
            t2_set.add(name)
        else:
            other_set.add(name)

    if t1_set:
        print("\U0001F451 Tier 1 투자자:")
        for name in sorted(t1_set):
            print(f"  - {name}")
        print()
    if t2_set:
        print("🥂 Tier 2 투자자:")
        for name in sorted(t2_set):
            print(f"  - {name}")
        print()
    if other_set:
        print("🔹 기타 투자자:")
        for name in sorted(other_set):
            print(f"  - {name}")
        print()

# 투자자 이름 -> lead인 경우 (Lead) 추가
def split_investors_by_tier(investors):
    """
    같은 투자자가 여러번 등장할 경우:
    - lead_investor 값이 1인 기록이 있으면 (Lead)로, 아니면 일반 이름으로만 한 번 출력
    - 등급별(티어별) 중복 제거
    """
    # Dict: {normalized_name: (최종표시이름, is_lead_존재여부)}
    t1_dict, t2_dict, others_dict = {}, {}, {}

    for inv in investors:
        name = inv.get("name", "").strip()
        name_lc = name.lower()
        norm_name = normalize(name)
        is_lead = inv.get("lead_investor", 0) == 1

        # 어디 티어인지 판별
        if name_lc in tier1:
            group = t1_dict
        elif is_tier2(name):
            group = t2_dict
        else:
            group = others_dict

        # lead 등장여부 갱신 (lead가 한번이라도 등장하면 표시)
        prev_is_lead = group.get(norm_name, (None, False))[1]
        display_name = f"<u>{name}</u>" if is_lead or prev_is_lead else name
        group[norm_name] = (display_name, is_lead or prev_is_lead)

    # Sorted 표시이름만 리스트로 리턴
    t1_list = sorted([v[0] for v in t1_dict.values()])
    t2_list = sorted([v[0] for v in t2_dict.values()])
    others_list = sorted([v[0] for v in others_dict.values()])
    return t1_list, t2_list, others_list


def format_project_info_to_text(project_info):
    lines = []
    lines.append(f"<b>{project_info.get('project_name')}</b>")
    lines.append("")
    lines.append(f"• 한 줄 소개: {project_info.get('one_liner', '')}")
    lines.append(f"• Tag: {', '.join(project_info.get('tags', []))}")
    
    lines.append("")
    social = project_info.get('social_media', {})
    if social.get('website'):
        lines.append(f"• web: {social.get('website')}")
    if social.get('X'):
        lines.append(f"• X: {social.get('X')}")
    lines.append("")
    
    lines.append(f"💰 총 투자액: ${project_info.get('total_funding', 0):,}\n")

    investors = project_info.get('investors', [])
    t1_list, t2_list, others_list = split_investors_by_tier(investors)
    if t1_list:
        lines.append("\U0001F451 Tier 1 투자자:")
        lines.append("  - "+", ".join(t1_list))
        lines.append("")
    if t2_list:
        lines.append("🥂 Tier 2 투자자:")
        lines.append("  - "+", ".join(t2_list))
        lines.append("")
    if others_list:
        lines.append("🔹 기타 투자자:")
        lines.append("  - "+", ".join(others_list))
        lines.append("")

    rootdata_url = project_info.get('rootdataurl')
    if rootdata_url:
        lines.append(f'<a href="{rootdata_url}">Rootdata</a>')
        
    return "\n".join(lines)

async def vc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # user_id가 admin_id이거나, chat_id가 allowed_chat_id일 때만 동작
    if (user_id != admin_id) and (chat_id != allowed_chat_id):
        await update.message.reply_text("권한이 없습니다.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("예시: /vc 프로젝트명")
        return
    
    query_keyword = " ".join(context.args).strip().lower()
    search_payload = {'query': query_keyword}

    # rootdata API 호출, 결과 처리
    res = requests.post(search_url, json=search_payload, headers=search_headers)
    data = res.json()
    project_ids = get_project_ids(data)

    results = []
    if not project_ids:
        await update.message.reply_text("해당 키워드로 검색된 프로젝트가 없습니다.")
        return

    for pid in project_ids:
        detail = fetch_project_detail(pid)
        project_name = (detail.get('project_name') or '').strip().lower()
        if project_name == query_keyword or fuzz.ratio(project_name, query_keyword) >= PROJECT_FUZZY_THRESHOLD:
            msg = format_project_info_to_text(detail)
            print(msg)
            results.append(msg)

    if results:
        # 메시지가 너무 길어질 수 있음. 길면 쪼개서 보냄
        for msg in results:
            if len(msg) < 4000:
                await update.message.reply_text(
                    msg,
                    disable_web_page_preview=True,  # URL 미리보기 비활성화
                    parse_mode='HTML',
                    )
            else:
                # 4096문자 이상이면 쪼개 보내기
                for chunk_start in range(0, len(msg), 4000):
                    await update.message.reply_text(
                        msg[chunk_start:chunk_start+4000],
                        disable_web_page_preview=True,  # URL 미리보기 비활성화
                        parse_mode='HTML',                        
                        )
    else:
        await update.message.reply_text("해당 키워드와 유사한 프로젝트가 없습니다.")


def main():
    # 텔레그램 봇 실행
    application = Application.builder().token(telegram_bot_token).build()
    application.add_handler(CommandHandler("vc", vc_command))
    print("텔레그램 봇이 시작되었습니다.")
    application.run_polling()


# 실행부
if __name__ == "__main__":
    main()