"""
Debate routes — Tạo phiên tranh luận + xem lịch sử + SSE streaming.
Endpoints:
  POST /api/debate         — chạy debate đồng bộ (chờ hết 6 agents)
  GET  /api/debate/stream  — SSE streaming realtime từng agent
  GET  /api/debate         — danh sách phiên
  GET  /api/debate/{id}    — chi tiết phiên
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.requests import Request
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from backend.app.api.deps import get_db, get_current_user, get_current_user_from_token
from backend.app.models.user import User
from backend.app.models.session import DebateSession
from backend.app.models.message import Message
from backend.app.schemas.debate import DebateCreate, DebateSessionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debate", tags=["Debate — Tranh luận"])


@router.post(
    "",
    response_model=DebateSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo phiên tranh luận mới",
)
def create_debate(
    data: DebateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Người dùng nhập ý tưởng → tạo phiên mới → gọi 5 AI agents phản biện + Moderator tổng hợp.
    Thứ tự: Thị Trường → Chiến Lược → Tài Chính → Kỹ Thuật → Pháp Lý → Moderator.
    """
    # Tạo phiên mới
    session = DebateSession(
        user_id=current_user.id,
        idea=data.idea,
        industry=data.industry,
        status="debating",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # -- GỌI DEBATE CHAIN (5 agents + Moderator) --
    from ai_engine.debate_chain import run_debate

    try:
        debate_result = run_debate(
            idea=data.idea,
            industry=data.industry,
        )

        if debate_result["status"] == "error":
            raise Exception(debate_result.get("error", "Unknown debate error"))

        # Lưu 5 agent responses vào DB
        for i, result in enumerate(debate_result["responses"], 1):
            message = Message(
                session_id=session.id,
                agent_name=result["agent_name"],
                agent_display=result["agent_display"],
                content=result["content"],
                round_number=1,
                tokens_used=result.get("tokens_used"),
                cost_usd=result.get("cost_usd"),
            )
            db.add(message)

        # Lưu Moderator summary
        if debate_result["summary"]:
            summary = debate_result["summary"]
            moderator_msg = Message(
                session_id=session.id,
                agent_name=summary["agent_name"],
                agent_display=summary["agent_display"],
                content=summary["content"],
                round_number=1,
                tokens_used=summary.get("tokens_used"),
                cost_usd=summary.get("cost_usd"),
            )
            db.add(moderator_msg)

        session.status = "completed"
        session.round_count = 1
        db.commit()
        db.refresh(session)

    except Exception as e:
        session.status = "error"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi gọi AI agents: {str(e)}",
        )

    return DebateSessionResponse.model_validate(session)


@router.get(
    "",
    response_model=list[DebateSessionResponse],
    summary="Xem danh sách phiên tranh luận",
)
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
):
    """Trả về danh sách phiên của user hiện tại (mới nhất trước)."""
    sessions = (
        db.query(DebateSession)
        .filter(DebateSession.user_id == current_user.id)
        .order_by(DebateSession.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [DebateSessionResponse.model_validate(s) for s in sessions]


# ── SSE Streaming Endpoint ──────────────────────────────

@router.get(
    "/stream",
    summary="SSE — Tranh luận realtime từng agent",
    description=(
        "Server-Sent Events endpoint. Dùng GET vì EventSource chỉ hỗ trợ GET. "
        "JWT token truyền qua query param `token`."
    ),
)
async def stream_debate(
    request: Request,
    idea: str = Query(..., min_length=5, description="Ý tưởng kinh doanh"),
    industry: str = Query(None, description="Ngành nghề (F&B, Tech, Giáo dục...)"),
    token: str = Query(..., description="JWT access token"),
):
    """
    SSE streaming debate:
    - Auth: JWT qua query param `token` (EventSource không gửi được header)
    - Mỗi agent chạy xong → gửi ngay 1 SSE event
    - Frontend dùng EventSource để nhận realtime

    Event format:
      data: {"type":"agent", "agent_name":"market", "agent_display":"📊 Thị Trường", "content":"...", "done":false}
      data: {"type":"summary", "agent_name":"moderator", "content":"...", "done":true}
    """
    # ── Auth (via query param) ────────────────────────
    db = next(get_db())
    try:
        current_user = get_current_user_from_token(token, db)
    except HTTPException:
        # Trả SSE error event thay vì HTTP error (EventSource không xử lý được HTTP errors tốt)
        async def error_stream():
            yield {
                "event": "error",
                "data": json.dumps({"error": "Token không hợp lệ hoặc đã hết hạn", "done": True}),
            }
        return EventSourceResponse(error_stream())

    # ── Tạo session trong DB ─────────────────────────
    session = DebateSession(
        user_id=current_user.id,
        idea=idea,
        industry=industry,
        status="debating",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    session_id = session.id  # Lưu ID trước khi close db
    user_id = current_user.id  # Lưu user_id cho Mem0
    user_tier = getattr(current_user, "tier", "free") or "free"  # Lưu tier
    db.close()

    # ── SSE Generator ────────────────────────────────
    async def event_generator():
        from ai_engine.debate_stream import run_debate_streaming

        db_save = next(get_db())  # DB session riêng cho save
        messages_to_save = []

        try:
            # Gửi session_id cho frontend (để biết reply vào session nào)
            yield {
                "event": "session",
                "data": json.dumps({"type": "session", "session_id": session_id}),
            }

            # ── Tier enforcement ───────────────────────
            from ai_engine.tier_config import get_tier_limits
            from datetime import datetime, timezone
            limits = get_tier_limits(user_tier)

            # Check session quota per month
            first_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            session_count = db_save.query(DebateSession).filter(
                DebateSession.user_id == user_id,
                DebateSession.created_at >= first_of_month,
                DebateSession.status.notin_(["needs_input"]),  # Không đếm phiên bị hủy/chờ
            ).count()
            if session_count >= limits["max_sessions_per_month"]:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": f"Đã hết quota {limits['max_sessions_per_month']} phiên/tháng. Nâng cấp để có thêm.",
                        "error_code": "QUOTA_EXCEEDED",
                        "done": True,
                    }, ensure_ascii=False),
                }
                return

            # ── Bước 6: Kiểm tra ý tưởng có đủ rõ ────────
            from ai_engine.clarifier import check_idea_clarity
            clarity = check_idea_clarity(idea)
            if clarity["needs_clarification"]:
                yield {
                    "event": "clarification",
                    "data": json.dumps({
                        "type": "clarification",
                        "questions": clarity["questions"],
                        "session_id": session_id,
                    }, ensure_ascii=False),
                }
                # Đặt session status = needs_input, không chạy agents
                db_session = db_save.query(DebateSession).filter(
                    DebateSession.id == session_id
                ).first()
                if db_session:
                    db_session.status = "needs_input"
                    db_save.commit()
                return  # Return sớm — KHÔNG chạy agents

            for event in run_debate_streaming(idea, industry, user_id=user_id, user_tier=user_tier):
                # Kiểm tra client disconnect
                if await request.is_disconnected():
                    logger.info(f"[SSE] Client disconnected — session {session_id}")
                    break

                # Lưu message để save vào DB sau
                if event.get("type") in ("agent", "summary"):
                    messages_to_save.append(event)

                # Yield SSE event (bao gồm cả memory event)
                yield {
                    "event": event.get("type", "message"),
                    "data": json.dumps(event, ensure_ascii=False),
                }

            # ── Lưu vào DB ───────────────────────────
            db_session = db_save.query(DebateSession).filter(
                DebateSession.id == session_id
            ).first()

            if db_session:
                for i, msg in enumerate(messages_to_save, 1):
                    db_msg = Message(
                        session_id=session_id,
                        agent_name=msg.get("agent_name", "unknown"),
                        agent_display=msg.get("agent_display", ""),
                        content=msg.get("content", ""),
                        round_number=1,
                        tokens_used=msg.get("tokens_used"),
                        cost_usd=msg.get("cost_usd"),
                    )
                    db_save.add(db_msg)

                db_session.status = "completed"
                db_session.round_count = 1

                # ── Generate Report Card ──────────────
                try:
                    from ai_engine.report_card import generate_report_card
                    mod_summary = ""
                    for msg in messages_to_save:
                        if msg.get("agent_name") == "moderator":
                            mod_summary = msg.get("content", "")
                    if mod_summary:
                        report = generate_report_card(
                            idea=idea,
                            industry=industry,
                            agent_responses=messages_to_save,
                            moderator_summary=mod_summary,
                        )
                        db_session.report_card = json.dumps(report, ensure_ascii=False)

                        yield {
                            "event": "report_card",
                            "data": json.dumps({"type": "report_card", **report}, ensure_ascii=False),
                        }
                except Exception as rc_err:
                    logger.warning(f"[SSE] Report card generation failed: {rc_err}")

                db_save.commit()
                logger.info(f"[SSE] Session {session_id} saved — {len(messages_to_save)} messages")

        except Exception as e:
            logger.error(f"[SSE] Stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e), "done": True}, ensure_ascii=False),
            }
            # Mark session as error
            try:
                db_session = db_save.query(DebateSession).filter(
                    DebateSession.id == session_id
                ).first()
                if db_session:
                    db_session.status = "error"
                    db_save.commit()
            except Exception:
                pass

        finally:
            db_save.close()

    return EventSourceResponse(event_generator())


# ── Report Card Endpoint ─────────────────────────────────

@router.get(
    "/{session_id}/report-card",
    summary="Lấy Report Card",
    response_model=None,
)
async def get_report_card(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lấy Report Card cho phiên debate — từ DB hoặc generate on-the-fly."""
    session = db.query(DebateSession).filter(
        DebateSession.id == session_id,
        DebateSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên")

    # Nếu đã có report card trong DB → trả về
    if session.report_card:
        return json.loads(session.report_card)

    # On-the-fly: generate từ messages
    messages = db.query(Message).filter(
        Message.session_id == session_id,
    ).order_by(Message.created_at).all()

    if not messages:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu phân tích")

    mod_summary = ""
    agent_responses = []
    for m in messages:
        resp = {"agent_name": m.agent_name, "agent_display": m.agent_display or m.agent_name, "content": m.content}
        agent_responses.append(resp)
        if m.agent_name == "moderator":
            mod_summary = m.content

    if not mod_summary:
        raise HTTPException(status_code=404, detail="Chưa có tổng kết từ Moderator")

    from ai_engine.report_card import generate_report_card
    report = generate_report_card(
        idea=session.idea,
        industry=session.industry,
        agent_responses=agent_responses,
        moderator_summary=mod_summary,
    )

    # Save to DB
    session.report_card = json.dumps(report, ensure_ascii=False)
    db.commit()

    return report


# ── PDF Export ────────────────────────────────────────────

@router.get(
    "/{session_id}/export/pdf",
    summary="Xuất PDF báo cáo phân tích",
)
async def export_pdf(
    session_id: str,
    token: str = Query(..., description="JWT access token"),
):
    """Tạo PDF từ kết quả debate — Playwright headless Chromium."""
    from backend.app.services.pdf_generator import generate_debate_pdf
    from starlette.responses import StreamingResponse
    import io

    # Auth via query param (giống SSE)
    db_gen = get_db()
    db = next(db_gen)
    try:
        current_user = get_current_user_from_token(token, db)

        # Tier check: only Premium can export PDF
        from ai_engine.tier_config import get_tier_limits
        limits = get_tier_limits(getattr(current_user, "tier", "free") or "free")
        if not limits["can_export_pdf"]:
            raise HTTPException(status_code=403, detail="Nâng cấp Premium để xuất PDF")

        session = db.query(DebateSession).filter(
            DebateSession.id == session_id,
            DebateSession.user_id == current_user.id,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên")

        # Query messages
        messages = db.query(Message).filter(
            Message.session_id == session_id,
        ).order_by(Message.created_at).all()

        if not messages:
            raise HTTPException(status_code=404, detail="Chưa có dữ liệu phân tích")

        # Build session data
        msg_list = []
        for m in messages:
            msg_list.append({
                "agent_name": m.agent_name,
                "agent_display": m.agent_display or m.agent_name,
                "content": m.content,
            })

        report_card = None
        if session.report_card:
            report_card = json.loads(session.report_card)

        session_data = {
            "idea": session.idea,
            "industry": session.industry,
            "messages": msg_list,
            "report_card": report_card,
            "created_at": session.created_at.strftime("%Y-%m-%d %H:%M") if session.created_at else "",
        }

        # Generate PDF
        pdf_bytes = await generate_debate_pdf(session_data)

        # Return as download
        filename = f"covankn-report-{session_id[:8]}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PDF] Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi tạo PDF: {str(e)}")
    finally:
        db.close()


# ── Reply Streaming (Multi-round) ────────────────────────

@router.get(
    "/{session_id}/reply/stream",
    summary="SSE — Phản biện lại (vòng 2, 3)",
    description="User gửi phản biện → agents trả lời cụ thể. Tối đa 3 vòng.",
)
async def stream_reply(
    request: Request,
    session_id: str,
    message: str = Query(..., min_length=5, description="Nội dung phản biện"),
    token: str = Query(..., description="JWT access token"),
):
    """SSE streaming cho vòng phản biện tiếp theo."""
    # ── Auth ──────────────────────────────────────────
    db = next(get_db())
    try:
        current_user = get_current_user_from_token(token, db)
    except HTTPException:
        async def error_stream():
            yield {
                "event": "error",
                "data": json.dumps({"error": "Token không hợp lệ hoặc đã hết hạn", "done": True}),
            }
        return EventSourceResponse(error_stream())

    # ── Validate session ─────────────────────────────
    session = (
        db.query(DebateSession)
        .filter(
            DebateSession.id == session_id,
            DebateSession.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        async def err():
            yield {"event": "error", "data": json.dumps({"error": "Không tìm thấy phiên", "done": True})}
        return EventSourceResponse(err())

    if session.status != "completed":
        async def err():
            yield {"event": "error", "data": json.dumps({"error": "Phiên đang xử lý hoặc chưa hoàn thành", "done": True})}
        return EventSourceResponse(err())

    if session.round_count >= 3:
        async def err():
            yield {"event": "error", "data": json.dumps({"error": "Đã hết 3 lượt phản biện", "done": True})}
        return EventSourceResponse(err())

    # ── Race condition protection: đặt status=debating ─
    new_round = session.round_count + 1
    session.status = "debating"
    db.commit()

    # ── Lưu user reply vào DB TRƯỚC khi gọi agents ───
    user_msg = Message(
        session_id=session_id,
        agent_name="user",
        agent_display="💬 Phản biện",
        content=message,
        round_number=new_round,
    )
    db.add(user_msg)
    db.commit()

    # ── Đọc ALL messages cũ → chuyển thành list[dict] ─
    all_messages = (
        db.query(Message)
        .filter(Message.session_id == session_id, Message.agent_name != "user")
        .order_by(Message.created_at)
        .all()
    )
    previous_messages = [
        {
            "agent_name": m.agent_name,
            "agent_display": m.agent_display or m.agent_name,
            "content": m.content,
        }
        for m in all_messages
    ]

    idea = session.idea
    industry = session.industry
    db.close()

    # ── SSE Generator ────────────────────────────────
    async def event_generator():
        from ai_engine.debate_stream import run_reply_streaming

        db_save = next(get_db())
        messages_to_save = []

        try:
            # Gửi session_id + round info
            yield {
                "event": "session",
                "data": json.dumps({"type": "session", "session_id": session_id, "round_number": new_round}),
            }

            # Tier enforcement for reply
            from ai_engine.tier_config import get_tier_limits
            user_tier = getattr(current_user, "tier", "free") or "free"
            limits = get_tier_limits(user_tier)

            if new_round > limits["max_rounds"]:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": f"Gói {user_tier} chỉ hỗ trợ {limits['max_rounds']} vòng. Nâng cấp để thêm vòng.",
                        "error_code": "ROUND_LIMIT",
                        "done": True,
                    }, ensure_ascii=False),
                }
                return

            for event in run_reply_streaming(
                idea=idea,
                industry=industry,
                previous_messages=previous_messages,
                user_reply=message,
                round_number=new_round,
                user_id=current_user.id,
                user_tier=user_tier,
            ):
                if await request.is_disconnected():
                    logger.info(f"[SSE-reply] Client disconnected — session {session_id}")
                    break

                if event.get("type") in ("agent", "summary"):
                    messages_to_save.append(event)

                yield {
                    "event": event.get("type", "message"),
                    "data": json.dumps(event, ensure_ascii=False),
                }

            # ── Lưu vào DB ───────────────────────────
            db_session = db_save.query(DebateSession).filter(
                DebateSession.id == session_id
            ).first()

            if db_session:
                for msg in messages_to_save:
                    db_msg = Message(
                        session_id=session_id,
                        agent_name=msg.get("agent_name", "unknown"),
                        agent_display=msg.get("agent_display", ""),
                        content=msg.get("content", ""),
                        round_number=new_round,
                        tokens_used=msg.get("tokens_used"),
                        cost_usd=msg.get("cost_usd"),
                    )
                    db_save.add(db_msg)

                db_session.round_count = new_round
                db_session.status = "completed"
                db_save.commit()
                logger.info(f"[SSE-reply] Session {session_id} round {new_round} saved — {len(messages_to_save)} messages")

        except Exception as e:
            logger.error(f"[SSE-reply] Stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e), "done": True}, ensure_ascii=False),
            }
            try:
                db_session = db_save.query(DebateSession).filter(
                    DebateSession.id == session_id
                ).first()
                if db_session:
                    db_session.status = "error"
                    db_save.commit()
            except Exception:
                pass

        finally:
            db_save.close()

    return EventSourceResponse(event_generator())


# ── Get Session Detail (PHẢI ở CUỐI — sau /stream + /reply/stream) ──

@router.get(
    "/{session_id}",
    response_model=DebateSessionResponse,
    summary="Xem chi tiết 1 phiên tranh luận",
)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trả về chi tiết phiên + tất cả messages từ agents."""
    session = (
        db.query(DebateSession)
        .filter(
            DebateSession.id == session_id,
            DebateSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy phiên tranh luận",
        )
    response = DebateSessionResponse.model_validate(session)
    # Parse report_card JSON string → dict
    if session.report_card:
        try:
            response.report_card = json.loads(session.report_card)
        except (json.JSONDecodeError, TypeError):
            pass
    return response
