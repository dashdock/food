import os
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from oauth2client.service_account import ServiceAccountCredentials


GOOGLE_AUTH_JSON = os.environ["GOOGLE_AUTH_JSON"]
KEYWORD = os.environ.get("DASHBOARD_KEYWORD", "음식물")
OUTPUT_DIR = os.environ.get("DASHBOARD_OUTPUT_DIR", "docs/data")
LEGACY_OUTPUT_PATH = os.environ.get(
    "DASHBOARD_OUTPUT_PATH",
    "docs/data.json",
)

SEOUL = ZoneInfo("Asia/Seoul")


SOURCE_TARGETS = [
    {
        "market": "군수품",
        "source": "발주계획",
        "name": "군수품조달_국내_발주계획",
    },
    {
        "market": "군수품",
        "source": "공고",
        "name": "군수품조달_국내_입찰공고",
    },
    {
        "market": "군수품",
        "source": "계약정보",
        "name": "군수품조달_국내_계약정보",
    },
    {
        "market": "나라장터",
        "source": "공고",
        "kind": "공사",
        "id": os.environ.get(
            "GOV_BID_SHEET_ID_CONSTRUCTION",
            "1gaErGoHJzMrk_tD6PEYAqGg8OC3IxxDHO4KqysJeoh4",
        ),
    },
    {
        "market": "나라장터",
        "source": "공고",
        "kind": "물품",
        "id": os.environ.get(
            "GOV_BID_SHEET_ID_GOODS",
            "1LZOCzbL4juIxmhY015hgokOsUbyewiLcLmHkzLiIqJk",
        ),
    },
    {
        "market": "나라장터",
        "source": "공고",
        "kind": "용역",
        "id": os.environ.get(
            "GOV_BID_SHEET_ID_SERVICE",
            "13RdFWDXDt0S7V2mYrkKYzVFdX01MZd8AIxyvLyU9qmE",
        ),
    },
    {
        "market": "나라장터",
        "source": "계약정보",
        "kind": "통합",
        "id": os.environ.get(
            "GOV_CONTRACT_SPREADSHEET_ID",
            "1ojPuMy9IHPRh7E0_MroTSCv-YsyADbBicmhtr8IEsCg",
        ),
    },
]


EXCLUDE_TABS = {
    "백필_진행상황",
}


TITLE_COLUMNS = [
    "bidNtceNm",
    "대표품목명",
    "공고명",
    "입찰공고명",
    "입찰명",
    "사업명",
    "품명",
    "계약명",
    "수요품명",
    "구매품명",
    "용역명",
    "건명",
    "bidNm",
    "itemNm",
    "cntrctNm",
    "prcurePlanNm",
]


AGENCY_COLUMNS = [
    "수요기관명",
    "dminsttNm",
    "dmndInsttNm",
    "발주기관",
    "수요기관",
    "수요부대",
    "기관명",
    "ornt",
    "orderInsttNm",
]


COMPANY_COLUMNS = [
    "업체명",
    "계약업체명",
    "계약상대자",
    "계약상대자명",
    "계약업체",
    "낙찰업체명",
    "낙찰자명",
    "업체상호",
    "상호",
    "업체",
    "cntrctEntrpsNm",
    "cntrctCorpNm",
    "cntrctCompanyNm",
    "sucsfbidEntrpsNm",
    "corpNm",
    "companyNm",
]


STATUS_COLUMNS = [
    "진행상태",
    "계약상태",
    "공고구분",
    "bidNtceTypeNm",
    "pblancSe",
    "bidNtceSttusNm",
    "ntceKindNm",
]


DATE_COLUMNS = [
    "공고일자",
    "공고일",
    "입찰공고일",
    "입찰공고일자",
    "입찰공고일시",
    "공고게시일",
    "공고게시일자",
    "공고게시일시",
    "게시일자",
    "게시일시",
    "ntceDt",
    "계약체결일",
    "계약체결일자",
    "계약일자",
    "계약일",
    "발주예정월",
    "등록일자",
    "작성일자",
    "bidNtceDt",
    "pblancDate",
    "cntrctDate",
    "cntrctCnclsDate",
    "orderPrearngeMt",
    "rgstDt",
]


PLAN_MONTH_COLUMNS = [
    "공고예정월",
    "발주예정월",
    "orderPrearngeMt",
    "bidNtcePlanMt",
    "pblancPrearngeMt",
]


DEADLINE_COLUMNS = [
    "입찰서제출마감일시",
    "입찰참가등록마감일시",
    "개찰일시",
    "bidClseDt",
    "biddocPresentnClosDt",
    "bidPartcptRegistClosDt",
    "opengDt",
]


END_DATE_COLUMNS = [
    "계약종료일",
    "계약종료일자",
    "계약만료일",
    "완료예정일",
    "종료예정일",
    "총완료예정일자",
    "금차완료예정일자",
    "cntrctEndDate",
    "cntrctEndDt",
    "completionPrearngeDate",
    "finishDate",
    "ttalScmpltDate",
    "thtmScmpltDate",
    "cmpltDate",
]


METHOD_COLUMNS = [
    "계약방법",
    "계약체결방법",
    "계약방식",
    "cntrctMth",
    "cntrctMthdNm",
    "cntrctCnclsMthdNm",
    "bidMethdNm",
]


URL_COLUMNS = [
    "바로가기",
    "상세URL",
    "계약상세URL",
    "공고상세URL",
    "bidNtceDtlUrl",
    "cntrctDtlInfoUrl",
    "detailUrl",
    "url",
]


IDENTIFIER_COLUMNS = [
    "G2B공고번호",
    "공고번호",
    "공고차수",
    "계약번호",
    "통합계약번호",
    "판단번호",
    "사업번호",
    "g2bPblancNo",
    "pblancNo",
    "pblancOdr",
    "cntrctNo",
    "untyCntrctNo",
    "dcsNo",
    "bidNtceNo",
]


AMOUNT_COLUMNS = {
    "발주계획": [
        "예산금액",
        "추정금액",
        "사업금액",
        "예정금액",
        "budgetAmount",
        "orderPlanAmount",
        "asignBdgtAmt",
    ],
    "공고": [
        "기초예비가격",
        "기초예가",
        "추정가격",
        "배정예산",
        "예정가격",
        "예산금액",
        "bdgtAmt",
        "bsicExpt",
        "bsisPrdprc",
        "presmptPrce",
        "asignBdgtAmt",
    ],
    "계약정보": [
        # 금차계약금액을 최우선으로 사용한다.
        "thtmCntrctAmt",
        "금차계약금액",
        "금차계약금액(원)",
        # 금차계약금액이 없을 때 총계약금액을 사용한다.
        "totCntrctAmt",
        "총계약금액",
        "총계약금액(원)",
        "totalCntrctAmt",
        # 그 밖의 기존 계약금액 컬럼은 마지막 순위로 사용한다.
        "계약금액",
        "계약금액(원)",
        "계약총액",
        "계약액",
        "최종계약금액",
        "낙찰금액",
        "cntrctAmnt",
        "cntrctAmt",
        "cntrctAmount",
        "sucsfbidAmt",
    ],
}


CANCELLED = {
    "취소공고",
    "유찰",
    "종료",
    "계약종료",
}


SERVICE_TERMS = [
    "처리용역",
    "처리 용역",
    "수거용역",
    "수거 용역",
    "운반용역",
    "운반 용역",
    "수집운반",
    "수집 운반",
    "수집운반용역",
    "수집 운반 용역",
    "수거운반",
    "수거 운반",
    "위탁처리",
    "위탁 처리",
    "위탁용역",
    "위탁 용역",
    "폐기물처리",
    "폐기물 처리",
    "음식물쓰레기처리",
    "음식물쓰레기 처리",
    "음식물류폐기물처리",
    "음식물류폐기물 처리",
    "음식물폐기물처리",
    "음식물폐기물 처리",
    "잔반처리",
    "잔반 처리",
    "폐기물위탁",
    "폐기물 위탁",
    "잔반수거",
    "잔반 수거",
    "음식물수거",
    "음식물 수거",
    "음식물류폐기물수거",
    "음식물류폐기물 수거",
]


EQUIPMENT_LEASE_TERMS = [
    "장비임차",
    "장비 임차",
    "임차장비",
    "임차 장비",
    "장비임대",
    "장비 임대",
    "장비대여",
    "장비 대여",
    "처리기임차",
    "처리기 임차",
    "처리기임대",
    "처리기 임대",
    "처리기대여",
    "처리기 대여",
    "렌탈장비",
    "렌탈 장비",
]


EQUIPMENT_TERMS = [
    "음식물처리기",
    "음식물쓰레기처리기",
    "음식물류폐기물처리기",
    "처리기",
    "음식물감량기",
    "감량기",
    "감량장비",
    "감량 장비",
    "감량화기기",
    "감량화 기기",
    "자원화기기",
    "자원화 기기",
    "미생물처리기",
    "미생물 처리기",
    "건조기",
    "탈수기",
    "분쇄기",
    "발효기",
    "소멸기",
    "처리장비",
    "처리 장비",
    "처리설비",
    "처리 설비",
    "처리기기",
    "처리 기기",
    "계량장비",
    "계량 장비",
    "계량기",
    "장비",
    "기기",
]



def first(row, columns):
    for column in columns:
        value = row.get(column)

        if value not in (None, ""):
            return str(value).strip()

    return ""


def digits(value):
    return "".join(
        character
        for character in str(value or "")
        if character.isdigit()
    )


def number(value):
    if value in (None, ""):
        return 0

    try:
        return int(
            float(
                str(value)
                .replace(",", "")
                .strip()
            )
        )
    except (TypeError, ValueError):
        return 0


def title_of(row):
    value = first(row, TITLE_COLUMNS)

    if value:
        return value

    for value in row.values():
        if value and KEYWORD in str(value):
            return str(value).strip()

    return "(제목 없음)"


def amount_of(row, source):
    for column in AMOUNT_COLUMNS[source]:
        amount = number(row.get(column))

        if amount > 0:
            return amount

    for key, value in row.items():
        normalized_key = (
            str(key)
            .replace(" ", "")
            .lower()
        )

        amount_key = any(
            keyword in normalized_key
            for keyword in (
                "금액",
                "가격",
                "예가",
                "예산",
                "amount",
                "price",
                "amnt",
            )
        )

        if amount_key and "단가" not in normalized_key:
            amount = number(value)

            if amount > 0:
                return amount

    return 0


def date_from(row, columns, min_len=6):
    for column in columns:
        date_value = digits(row.get(column))

        if len(date_value) >= 8:
            return date_value[:8]

        if len(date_value) >= min_len:
            return date_value[:6]

    return ""


def category(row, title):
    # 분류는 다른 컬럼의 "용역" 같은 값에 오염되지 않도록 사업명/공고명/계약명 중심으로 판단한다.
    text = str(title or "").lower().strip()
    compact = re.sub(r"\s+", "", text)

    # 장비 임차·임대·대여·렌탈은 뒤에 "용역"이 붙어도 장비로 분류한다.
    # 예: 음식물쓰레기 처리기기 임차용역, 처리기(건조기)임차용역, 임차장비 용역
    equipment_nouns = [
        "음식물처리기", "음식물쓰레기처리기", "음식물류폐기물처리기",
        "처리기기", "처리기", "건조기", "감량기", "감량장비",
        "처리장비", "처리설비", "장비", "기기",
    ]
    lease_words = ["임차", "임대", "대여", "렌탈"]

    has_equipment_lease = any(
        (noun in compact and lease in compact)
        for noun in equipment_nouns
        for lease in lease_words
    )

    if has_equipment_lease:
        return "장비"

    # 실제 수거·운반·폐기·위탁처리 업무만 처리용역으로 분류한다.
    if any(
        re.sub(r"\s+", "", term.lower()) in compact
        for term in SERVICE_TERMS
    ):
        return "처리용역"

    # 장비 구매·설치·제조·교체 등
    if any(
        re.sub(r"\s+", "", term.lower()) in compact
        for term in EQUIPMENT_TERMS
    ):
        return "장비"

    return "기타음식물"



def is_open(source, deadline, status):
    if source != "공고":
        return False

    if status in CANCELLED:
        return False

    if not deadline:
        return False

    now_value = datetime.now(SEOUL).strftime(
        "%Y%m%d%H%M"
    )

    return deadline >= now_value[:len(deadline)]


def dedupe(
    row,
    source,
    title,
    agency,
    date,
    amount,
):
    identifiers = [
        str(row[column]).strip()
        for column in IDENTIFIER_COLUMNS
        if row.get(column) not in (None, "")
    ]

    if identifiers:
        return (
            source
            + "|"
            + "|".join(identifiers)
        )

    return (
        f"{source}|{title}|{agency}|"
        f"{date}|{amount}"
    )


def scan(client, target):
    source = target["source"]
    market = target["market"]

    if target.get("id"):
        spreadsheet = client.open_by_key(
            target["id"]
        )
    else:
        spreadsheet = client.open(
            target["name"]
        )

    rows = []
    seen = set()

    for worksheet in spreadsheet.worksheets():
        if worksheet.title in EXCLUDE_TABS:
            continue

        values = worksheet.get_all_values()

        if len(values) < 2:
            continue

        headers = values[0]

        for value_row in values[1:]:
            if not any(value_row):
                continue

            if not any(
                KEYWORD in str(value)
                for value in value_row
                if value
            ):
                continue

            raw = dict(
                zip(headers, value_row)
            )

            title = title_of(raw)
            agency = first(
                raw,
                AGENCY_COLUMNS,
            )
            company = first(
                raw,
                COMPANY_COLUMNS,
            )
            amount = amount_of(
                raw,
                source,
            )

            date = date_from(
                raw,
                DATE_COLUMNS,
            )
            plan_month = date_from(
                raw,
                PLAN_MONTH_COLUMNS,
            )
            deadline = date_from(
                raw,
                DEADLINE_COLUMNS,
                8,
            )

            # 일부 군수품 공고 시트는 공고일이 비어 있거나 컬럼명이 다르다.
            # 이 경우 연도 필터에서 누락되지 않도록 입찰 마감일을 기준일로 보완한다.
            if source == "공고" and not date and deadline:
                date = deadline[:8]

            end_date = date_from(
                raw,
                END_DATE_COLUMNS,
                8,
            )

            status = (
                first(raw, STATUS_COLUMNS)
                or "미상"
            )

            # 공고 목록의 공고구분(V열)에 "취소"가 포함된 행은 제외한다.
            # 컬럼명이 API 필드명으로 들어오는 경우도 함께 처리한다.
            notice_type = str(
                raw.get("공고구분")
                or raw.get("bidNtceTypeNm")
                or status
                or ""
            ).strip()
            if source == "공고" and "취소" in notice_type:
                continue

            key = dedupe(
                raw,
                source,
                title,
                agency,
                date,
                amount,
            )

            if key in seen:
                continue

            seen.add(key)

            rows.append(
                {
                    "market": market,
                    "kind": target.get(
                        "kind",
                        "",
                    ),
                    "source": source,
                    "title": title,
                    "agency": agency,
                    "company": company,
                    "amount": amount,
                    "category": category(
                        raw,
                        title,
                    ),
                    "status": status,
                    "date": date,
                    "plan_month": (
                        plan_month
                        or date[:6]
                    ),
                    "deadline": deadline,
                    "end_date": end_date,
                    "method": first(
                        raw,
                        METHOD_COLUMNS,
                    ),
                    "url": first(
                        raw,
                        URL_COLUMNS,
                    ),
                    "open": is_open(
                        source,
                        deadline,
                        status,
                    ),
                    "lookup_keyword": title,
                }
            )

    return rows


def main():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = (
        ServiceAccountCredentials
        .from_json_keyfile_dict(
            json.loads(GOOGLE_AUTH_JSON),
            scope,
        )
    )

    client = gspread.authorize(
        credentials
    )

    all_rows = []

    for target in SOURCE_TARGETS:
        print(
            "스캔:",
            target["market"],
            target["source"],
            target.get("kind", ""),
        )

        all_rows.extend(
            scan(client, target)
        )

    all_rows.sort(
        key=lambda row: (
            row.get("date", ""),
            row.get("amount", 0),
        ),
        reverse=True,
    )

    years = sorted(
        {
            (
                row.get("date")
                or row.get("plan_month")
                or ""
            )[:4]
            for row in all_rows
            if len(
                row.get("date")
                or row.get("plan_month")
                or ""
            ) >= 4
        },
        reverse=True,
    )

    now = datetime.now(SEOUL)

    payload = {
        "updated_at": now.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "keyword": KEYWORD,
        "years": years,
        "records": all_rows,
    }

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    summary_path = os.path.join(
        OUTPUT_DIR,
        "summary.json",
    )

    with open(
        summary_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    legacy_directory = (
        os.path.dirname(
            LEGACY_OUTPUT_PATH
        )
        or "."
    )

    os.makedirs(
        legacy_directory,
        exist_ok=True,
    )

    with open(
        LEGACY_OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print(
        "완료:",
        len(all_rows),
        "건",
    )


if __name__ == "__main__":
    main()