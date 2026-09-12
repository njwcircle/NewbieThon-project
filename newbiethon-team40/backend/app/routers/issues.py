from datetime import datetime
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..chat_service import post_system_message
from ..deps import get_current_user, get_db, require_landlord

router = APIRouter(prefix="/contracts/{contract_id}/issues", tags=["issues"])
upload_router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"
ISSUE_UPLOAD_DIR = UPLOAD_ROOT / "issues"
RECEIPT_UPLOAD_DIR = UPLOAD_ROOT / "receipts"
ISSUE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RECEIPT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def _get_accessible_contract(contract_id: str, user: models.User, db: Session) -> models.Contract:
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if contract is None:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    if user.id not in (contract.landlord_id, contract.tenant_id):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    return contract


def _get_issue(contract_id: str, issue_id: str, db: Session) -> models.IssueReport:
    issue = (
        db.query(models.IssueReport)
        .filter(models.IssueReport.id == issue_id, models.IssueReport.contract_id == contract_id)
        .first()
    )
    if issue is None:
        raise HTTPException(status_code=404, detail="문제접수 내역을 찾을 수 없습니다.")
    return issue


def _save_image(file: UploadFile, directory: Path, public_prefix: str) -> schemas.UploadResponse:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="jpg, png, webp, gif 이미지만 업로드할 수 있습니다.")

    suffix = Path(file.filename or "image").suffix.lower()
    if not suffix:
        suffix = ".jpg"
    filename = f"{uuid.uuid4().hex}{suffix}"
    dest = directory / filename

    size = 0
    with dest.open("wb") as out:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="이미지는 최대 10MB까지 업로드할 수 있습니다.")
            out.write(chunk)

    return schemas.UploadResponse(url=f"/uploads/{public_prefix}/{filename}")


@upload_router.post("/issues", response_model=schemas.UploadResponse)
def upload_issue_image(file: UploadFile = File(...)):
    return _save_image(file, ISSUE_UPLOAD_DIR, "issues")


@upload_router.post("/receipts", response_model=schemas.UploadResponse)
def upload_receipt_image(file: UploadFile = File(...)):
    return _save_image(file, RECEIPT_UPLOAD_DIR, "receipts")


@router.post("", response_model=schemas.IssueCreateResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    contract_id: str,
    payload: schemas.IssueReportCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    contract = _get_accessible_contract(contract_id, current_user, db)

    # 실제 신고는 임차인이 하는 것이 기본. 임대인도 테스트/대리접수는 허용한다.
    agreement = (
        db.query(models.PriorAgreement)
        .filter(
            models.PriorAgreement.contract_id == contract.id,
            models.PriorAgreement.category == payload.category,
        )
        .order_by(models.PriorAgreement.updated_at.desc())
        .first()
    )

    responsible = agreement.responsible if agreement else models.Responsible.UNDEFINED
    issue_status = models.IssueStatus.RECEIVED if agreement else models.IssueStatus.IN_CHAT

    issue = models.IssueReport(
        contract_id=contract.id,
        category=payload.category,
        description=payload.description,
        photo_url=payload.photo_url,
        status=issue_status,
        responsible=responsible,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)

    category_label = payload.category.value
    if agreement:
        note = agreement.note or "등록된 사전합의 내용을 확인해주세요."
        system_text = f"[{category_label}] 문제가 접수되었습니다. 사전합의가 있어 해당 기준으로 처리합니다."
        next_action = "FOLLOW_AGREEMENT"
    else:
        note = None
        system_text = f"[{category_label}] 문제가 접수되었습니다. 사전합의가 없어 채팅으로 해결 방법을 정해주세요."
        next_action = "OPEN_CHAT"

    post_system_message(
        db,
        contract.id,
        models.ChatMessageType.SYSTEM_ISSUE,
        system_text,
        ref_id=issue.id,
    )

    return schemas.IssueCreateResponse(
        issue=issue,
        agreement_matched=agreement is not None,
        agreement_note=note,
        next_action=next_action,
    )


@router.get("", response_model=list[schemas.IssueReportResponse])
def list_issues(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_accessible_contract(contract_id, current_user, db)
    return (
        db.query(models.IssueReport)
        .filter(models.IssueReport.contract_id == contract_id)
        .order_by(models.IssueReport.created_at.desc())
        .all()
    )


@router.get("/{issue_id}", response_model=schemas.IssueReportResponse)
def get_issue(
    contract_id: str,
    issue_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_accessible_contract(contract_id, current_user, db)
    return _get_issue(contract_id, issue_id, db)


@router.patch("/{issue_id}/status", response_model=schemas.IssueReportResponse)
def update_issue_status(
    contract_id: str,
    issue_id: str,
    payload: schemas.IssueStatusUpdateRequest,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    contract = (
        db.query(models.Contract)
        .filter(models.Contract.id == contract_id, models.Contract.landlord_id == landlord.id)
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")

    issue = _get_issue(contract_id, issue_id, db)
    issue.status = payload.status
    db.commit()
    db.refresh(issue)

    post_system_message(
        db,
        contract_id,
        models.ChatMessageType.SYSTEM_ISSUE,
        f"문제접수 처리 상태가 {payload.status.value}(으)로 변경되었습니다.",
        ref_id=issue.id,
    )
    return issue


@router.post("/{issue_id}/resolve", response_model=schemas.IssueReportResponse)
def resolve_issue(
    contract_id: str,
    issue_id: str,
    payload: schemas.IssueResolveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_accessible_contract(contract_id, current_user, db)
    issue = _get_issue(contract_id, issue_id, db)

    issue.resolver = payload.resolver
    issue.resolved_detail = payload.resolved_detail
    issue.cost = payload.cost
    issue.payer = payload.payer
    issue.payment_status = payload.payment_status
    issue.receipt_image_url = payload.receipt_image_url
    issue.status = models.IssueStatus.RESOLVED
    issue.resolved_at = payload.completed_at or datetime.utcnow()

    db.commit()
    db.refresh(issue)

    post_system_message(
        db,
        contract_id,
        models.ChatMessageType.SYSTEM_ISSUE,
        f"[{issue.category.value}] 문제 처리가 완료되었습니다. 비용 {issue.cost:,}원 / 부담 {issue.payer.value}",
        ref_id=issue.id,
    )
    return issue
