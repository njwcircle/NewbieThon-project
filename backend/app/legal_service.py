import os

from sqlalchemy.orm import Session

from . import models, schemas

DISCLAIMER = "이 답변은 일반적인 법률 정보 안내이며, 개별 사건에 대한 법률 자문을 대체하지 않습니다. 중요한 판단 전에는 계약서 원문과 최신 법령을 확인하고 필요하면 전문가에게 상담하세요."


def build_legal_context(db: Session, contract: models.Contract) -> tuple[str, list[str], list[str]]:
    unit = contract.unit
    building = unit.building

    issues = (
        db.query(models.IssueReport)
        .filter(models.IssueReport.contract_id == contract.id)
        .order_by(models.IssueReport.created_at.desc())
        .limit(20)
        .all()
    )
    agreements = (
        db.query(models.PriorAgreement)
        .filter(models.PriorAgreement.contract_id == contract.id)
        .all()
    )

    issue_lines = []
    for i in issues:
        issue_lines.append(
            f"- ID={i.id}, category={i.category.value}, status={i.status.value}, "
            f"responsible={i.responsible.value}, description={i.description or '-'}, "
            f"resolved_detail={i.resolved_detail or '-'}"
        )

    agreement_lines = []
    for a in agreements:
        agreement_lines.append(
            f"- ID={a.id}, category={a.category.value}, responsible={a.responsible.value}, note={a.note or '-'}"
        )

    context = f"""
[현재 계약 정보]
- 계약 ID: {contract.id}
- 건물: {building.name or building.address}
- 주소: {building.address}
- 동/호: {unit.dong}동 {unit.ho}호
- 월세: {contract.rent_amount}원
- 고정 관리비: {contract.maintenance_fee_fixed}원
- 계약기간: {contract.start_date} ~ {contract.end_date}
- 계약상태: {contract.status.value}

[사전합의사항]
{chr(10).join(agreement_lines) if agreement_lines else '- 등록된 사전합의 없음'}

[해당 계약의 최근 문제접수 기록]
{chr(10).join(issue_lines) if issue_lines else '- 문제접수 기록 없음'}
""".strip()

    return context, [i.id for i in issues], [a.id for a in agreements]


def get_legal_advice(
    db: Session,
    contract: models.Contract,
    payload: schemas.LegalAdviceRequest,
) -> schemas.LegalAdviceResponse:
    context, issue_ids, agreement_ids = build_legal_context(db, contract)

    api_key = os.getenv("LEGAL_LLM_API_KEY")
    if not api_key:
        raise RuntimeError("LEGAL_LLM_API_KEY가 설정되지 않았습니다. backend/.env에 API 키를 넣어주세요.")

    model = os.getenv("LEGAL_LLM_MODEL")
    if not model:
        raise RuntimeError(
            "LEGAL_LLM_MODEL이 설정되지 않았습니다. 사용 중인 제공업체의 실제 모델명을 확인해 "
            "backend/.env에 넣어주세요 (예: Gemini는 gemini-3.5-flash)."
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai 패키지가 없습니다. pip install -r requirements.txt 를 다시 실행해주세요.") from exc

    # OpenAI SDK 호환 엔드포인트를 제공하는 곳이면 어디든 api_key/base_url만 바꿔서 그대로 쓸 수 있다
    # (Upstage Solar, Google Gemini, Groq 등). 현재는 base_url 기본값을 Gemini로 둔다.
    base_url = os.getenv("LEGAL_LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    client = OpenAI(api_key=api_key, base_url=base_url)

    instructions = """
당신은 대한민국 임대차 상황에서 사용자가 쟁점을 정리하도록 돕는 법률 정보 안내 에이전트다.
반드시 한국어로 답한다.
현재 계약 정보, 사전합의사항, 문제접수 기록을 우선 참고하되, 기록에 없는 사실을 만들어내지 않는다.
법적 결론을 단정하지 말고 '일반적으로', '확인이 필요하다' 같은 표현을 사용한다.
최신 법 조문이나 판례를 확인하지 않은 상태에서 조문 번호나 판례번호를 만들어내지 않는다.
답변은 1) 상황 요약 2) 일반적인 판단 기준 3) 현재 정보에서 확인할 점 4) 다음 행동 순서로 짧고 명확하게 구성한다.
""".strip()

    user_input = f"""
법률 도움 카테고리: {payload.category.value}
기타 카테고리 직접 입력: {payload.custom_category or '-'}
사용자 질문: {payload.question}

{context}
""".strip()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": user_input},
        ],
    )

    return schemas.LegalAdviceResponse(
        category=payload.category,
        answer=response.choices[0].message.content,
        contract_id=contract.id,
        referenced_issue_ids=issue_ids,
        referenced_agreement_ids=agreement_ids,
        disclaimer=DISCLAIMER,
    )
