import os, json, re
from datetime import datetime
from zoneinfo import ZoneInfo
import gspread
from oauth2client.service_account import ServiceAccountCredentials

GOOGLE_AUTH_JSON = os.environ['GOOGLE_AUTH_JSON']
KEYWORD = os.environ.get('DASHBOARD_KEYWORD', '음식물')
OUTPUT_DIR = os.environ.get('DASHBOARD_OUTPUT_DIR', 'docs/data')
LEGACY_OUTPUT_PATH = os.environ.get('DASHBOARD_OUTPUT_PATH', 'docs/data.json')
SEOUL = ZoneInfo('Asia/Seoul')

SOURCE_TARGETS = [
    {'market':'군수품','source':'발주계획','name':'군수품조달_국내_발주계획'},
    {'market':'군수품','source':'공고','name':'군수품조달_국내_입찰공고'},
    {'market':'군수품','source':'계약정보','name':'군수품조달_국내_계약정보'},
    {'market':'나라장터','source':'공고','kind':'공사','id':os.environ.get('GOV_BID_SHEET_ID_CONSTRUCTION','1gaErGoHJzMrk_tD6PEYAqGg8OC3IxxDHO4KqysJeoh4')},
    {'market':'나라장터','source':'공고','kind':'물품','id':os.environ.get('GOV_BID_SHEET_ID_GOODS','1LZOCzbL4juIxmhY015hgokOsUbyewiLcLmHkzLiIqJk')},
    {'market':'나라장터','source':'공고','kind':'용역','id':os.environ.get('GOV_BID_SHEET_ID_SERVICE','13RdFWDXDt0S7V2mYrkKYzVFdX01MZd8AIxyvLyU9qmE')},
    {'market':'나라장터','source':'계약정보','kind':'통합','id':os.environ.get('GOV_CONTRACT_SPREADSHEET_ID','1ojPuMy9IHPRh7E0_MroTSCv-YsyADbBicmhtr8IEsCg')},
]
EXCLUDE_TABS = {'백필_진행상황'}

TITLE_COLUMNS = ['bidNtceNm','cntrctNm','prcurePlanNm','대표품목명','입찰공고명','입찰공고명칭','공고명','입찰명','계약명','사업명','품명','수요품명','구매품명','용역명','건명','공고건명','bidNm','itemNm']
AGENCY_COLUMNS = ['수요기관명','dminsttNm','dmndInsttNm','수요기관','발주기관명','발주기관','계약기관명','기관명','수요부대','공고기관명','공고게시기관명','ornt','orderInsttNm','ntceInsttNm']
COMPANY_COLUMNS = ['업체명','계약업체명','계약상대자','계약상대자명','계약업체','낙찰업체명','낙찰자명','업체상호','상호','업체','cntrctEntrpsNm','cntrctCorpNm','cntrctCompanyNm','sucsfbidEntrpsNm','corpNm','companyNm']
STATUS_COLUMNS = ['진행상태','계약상태','공고구분','pblancSe','bidNtceSttusNm','ntceKindNm']
DATE_COLUMNS = ['공고일자','입찰공고일자','공고게시일자','공고일시','계약체결일','계약일자','계약일','발주예정월','등록일자','작성일자','bidNtceDt','bidNtceDate','pblancDate','cntrctDate','cntrctCnclsDate','orderPrearngeMt','rgstDt']
PLAN_MONTH_COLUMNS = ['공고예정월','발주예정월','orderPrearngeMt','bidNtcePlanMt','pblancPrearngeMt']
DEADLINE_COLUMNS = ['입찰서제출마감일시','입찰서마감일시','입찰마감일시','입찰참가등록마감일시','개찰일시','bidClseDt','bidClseDate','biddocPresentnClosDt','bidPartcptRegistClosDt','opengDt']
END_DATE_COLUMNS = ['계약종료일','계약종료일자','계약만료일','완료예정일','종료예정일','cntrctEndDate','cntrctEndDt','completionPrearngeDate','finishDate']
METHOD_COLUMNS = ['계약방법','계약체결방법','계약방식','cntrctMth','cntrctMthdNm','cntrctCnclsMthdNm','bidMethdNm']
URL_COLUMNS = ['바로가기','상세URL','계약상세URL','공고상세URL','bidNtceDtlUrl','cntrctDtlInfoUrl','detailUrl','url']
IDENTIFIER_COLUMNS = ['G2B공고번호','공고번호','공고차수','계약번호','통합계약번호','판단번호','사업번호','g2bPblancNo','pblancNo','pblancOdr','cntrctNo','untyCntrctNo','dcsNo','bidNtceNo']
AMOUNT_COLUMNS = {
    '발주계획':['예산금액','추정금액','사업금액','예정금액','budgetAmount','orderPlanAmount','asignBdgtAmt'],
    '공고':['기초예비가격','기초예가','추정가격','배정예산','예정가격','예산금액','bdgtAmt','bsicExpt','bsisPrdprc','presmptPrce','asignBdgtAmt'],
    # 표출 기준: thtmCntrctAmt(금차계약금액) 우선, 0/공백이면 totCntrctAmt(총계약금액)
    '계약정보':['금차계약금액','금차계약금액(원)','thtmCntrctAmt','총계약금액','총계약금액(원)','totCntrctAmt','totalCntrctAmt','계약금액','계약금액(원)','계약총액','계약액','최종계약금액','낙찰금액','cntrctAmnt','cntrctAmt','cntrctAmount','sucsfbidAmt'],
}

RENTAL = ['임차','렌탈','리스','대여']
SERVICE = ['폐기물','위탁처리','수집운반','수거','운반','처리용역']
MAINT = ['정비','유지보수','수리','보수','위탁관리']
ACCESSORY = ['처리대','처리통','잔반통','쓰레기통','봉투','보관판넬','부수자재']
CORE = ['음식물처리기','음식물 처리기','음식물쓰레기처리기','음식물 쓰레기 처리기','감량기','감량기기','분쇄기','건조기','탈수기','자원화기기']
CANCELLED = {'취소공고','유찰','종료','계약종료'}

def first(row, cols):
    for c in cols:
        v = row.get(c)
        if v not in (None, ''):
            return str(v).strip()
    return ''

def digits(v):
    return ''.join(ch for ch in str(v or '') if ch.isdigit())

def number(v):
    if v in (None, ''): return 0
    try: return int(float(str(v).replace(',','').strip()))
    except: return 0

def title_of(row):
    v = first(row, TITLE_COLUMNS)
    if v: return v
    for v in row.values():
        if v and KEYWORD in str(v): return str(v).strip()
    return '(제목 없음)'

def amount_of(row, source):
    # 계약정보는 금차계약금액을 우선 표출하고, 0/공백일 때만 총계약금액을 사용합니다.
    if source == '계약정보':
        current_amount = 0
        for c in ('금차계약금액', '금차계약금액(원)', 'thtmCntrctAmt', 'currentCntrctAmt'):
            current_amount = number(row.get(c))
            if current_amount > 0:
                return current_amount

        for c in ('총계약금액', '총계약금액(원)', 'totCntrctAmt', 'totalCntrctAmt'):
            total_amount = number(row.get(c))
            if total_amount > 0:
                return total_amount

    for c in AMOUNT_COLUMNS[source]:
        n = number(row.get(c))
        if n > 0:
            return n
    for k, v in row.items():
        key = str(k).replace(' ','').lower()
        if any(x in key for x in ('금액','가격','예가','예산','amount','price','amnt')) and '단가' not in key:
            n = number(v)
            if n > 0:
                return n
    return 0

def date_from(row, columns, min_len=6):
    for c in columns:
        d = digits(row.get(c))
        if len(d) >= 8: return d[:8]
        if len(d) >= min_len: return d[:6]
    return ''

def category(title):
    compact = str(title or '').replace(' ', '')
    if any(k.replace(' ', '') in compact for k in CORE):
        return '장비'
    if any(k.replace(' ', '') in compact for k in SERVICE):
        return '처리용역'
    # 임차/유지보수/부속품도 음식물처리 장비 운영과 직접 관련된 경우 장비로 분류
    if any(k.replace(' ', '') in compact for k in RENTAL + MAINT + ACCESSORY):
        return '장비'
    return '기타음식물'

def is_open(source, deadline, status):
    if source != '공고' or status in CANCELLED: return False
    now = datetime.now(SEOUL).strftime('%Y%m%d%H%M')
    return bool(deadline and deadline >= now[:len(deadline)])

def dedupe(row, source, title, agency, date, amount):
    ids = [str(row[c]).strip() for c in IDENTIFIER_COLUMNS if row.get(c) not in (None,'')]
    if ids: return source + '|' + '|'.join(ids)
    return f'{source}|{title}|{agency}|{date}|{amount}'

def scan(client, target):
    source = target['source']; market = target['market']
    ss = client.open_by_key(target['id']) if target.get('id') else client.open(target['name'])
    rows=[]; seen=set()
    for ws in ss.worksheets():
        if ws.title in EXCLUDE_TABS: continue
        vals = ws.get_all_values()
        if len(vals) < 2: continue
        known_headers = set(TITLE_COLUMNS + AGENCY_COLUMNS + COMPANY_COLUMNS + DATE_COLUMNS + DEADLINE_COLUMNS + METHOD_COLUMNS + URL_COLUMNS + IDENTIFIER_COLUMNS)
        header_idx = 0
        best_score = -1
        for i, candidate in enumerate(vals[:20]):
            score = sum(1 for cell in candidate if str(cell).strip() in known_headers)
            if score > best_score:
                best_score = score
                header_idx = i
        hdr = [str(v).strip() for v in vals[header_idx]]
        for vr in vals[header_idx + 1:]:
            if not any(vr) or not any(KEYWORD in str(v) for v in vr if v): continue
            raw = dict(zip(hdr, vr))
            title = title_of(raw); agency = first(raw, AGENCY_COLUMNS); amount = amount_of(raw, source)
            date = date_from(raw, DATE_COLUMNS); plan_month = date_from(raw, PLAN_MONTH_COLUMNS)
            deadline = date_from(raw, DEADLINE_COLUMNS, 8)
            end_date = date_from(raw, END_DATE_COLUMNS, 8)
            status = first(raw, STATUS_COLUMNS) or '미상'
            key = dedupe(raw, source, title, agency, date, amount)
            if key in seen: continue
            seen.add(key)
            rows.append({
                'market': market, 'kind': target.get('kind',''), 'source': source,
                'title': title, 'agency': agency, 'company': first(raw, COMPANY_COLUMNS),
                'amount': amount, 'category': category(' '.join(str(v) for v in raw.values() if v)), 'status': status,
                'date': date, 'plan_month': plan_month or date[:6], 'deadline': deadline,
                'end_date': end_date, 'method': first(raw, METHOD_COLUMNS),
                'url': first(raw, URL_COLUMNS), 'open': is_open(source, deadline, status),
                'lookup_keyword': title,
            })
    return rows

def main():
    scope=['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds=ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_AUTH_JSON),scope)
    client=gspread.authorize(creds)
    all_rows=[]
    for target in SOURCE_TARGETS:
        print('스캔:',target['market'],target['source'],target.get('kind',''))
        all_rows.extend(scan(client,target))
    all_rows.sort(key=lambda r:(r.get('date',''),r.get('amount',0)), reverse=True)
    years=sorted({(r.get('date') or r.get('plan_month') or '')[:4] for r in all_rows if len((r.get('date') or r.get('plan_month') or ''))>=4}, reverse=True)
    now=datetime.now(SEOUL)
    payload={'updated_at':now.strftime('%Y-%m-%d %H:%M:%S'),'keyword':KEYWORD,'years':years,'records':all_rows}
    os.makedirs(OUTPUT_DIR,exist_ok=True)
    with open(os.path.join(OUTPUT_DIR,'summary.json'),'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,separators=(',',':'))
    os.makedirs(os.path.dirname(LEGACY_OUTPUT_PATH) or '.',exist_ok=True)
    with open(LEGACY_OUTPUT_PATH,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,separators=(',',':'))
    print('완료:',len(all_rows),'건')

if __name__=='__main__': main()
