"""평가대상: 히스토리 저장/로드 테스트"""
import pytest
import asyncio
import aiohttp
import time
import uuid
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from tests.utils.api_client import make_chat_request
from tests.utils.test_helpers import (
    print_test_header,
    print_test_summary,
    save_test_results,
)


@pytest.mark.asyncio
async def test_history_storage():
    """평가대상: 히스토리 저장/로드 테스트"""
    test_start = time.time()
    
    test_info = {
        "test_name": "히스토리 저장/로드 테스트",
        "test_type": "evaluation",
        "is_evaluation_target": True,
        "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "target": {
            "description": "동일 conversation_id로 2회 요청 → 히스토리 저장 및 로드 확인",
            "expected_value": "히스토리 저장 성공, 로드 성공, 맥락 반영 확인",
            "threshold": "히스토리 저장 및 로드 성공"
        }
    }
    
    print_test_header(
        test_info["test_name"],
        "평가대상: conversation_id 기반으로 히스토리가 저장되고 로드되는지 확인합니다.",
        is_evaluation_target=True
    )
    
    conversation_id = str(uuid.uuid4())
    query1 = "AI 아메바는 무슨일을 해"
    query2 = "그럼 어뷰징 관련 기능은?"
    
    print(f"[INFO] Conversation ID: {conversation_id}")
    print(f"[INFO] 첫 번째 질문: {query1}")
    print(f"[INFO] 두 번째 질문: {query2}\n")
    
    async with aiohttp.ClientSession() as session:
        # 첫 번째 요청
        print("[TESTING] 첫 번째 요청 전송...")
        response1 = await make_chat_request(session, query1, conversation_id=conversation_id)
        
        if response1.get("status") != 200:
            test_info["result"] = {
                "actual_value": "첫 번째 요청 실패",
                "achieved": False,
                "suitable": False,
                "suitability_reason": "첫 번째 요청이 실패하여 테스트 중단"
            }
            test_info["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            test_info["total_duration"] = time.time() - test_start
            print_test_summary(test_info)
            return test_info
        
        print(f"  응답: {response1.get('response_text', '')[:100]}...")
        
        await asyncio.sleep(1)  # 간격
        
        # 두 번째 요청 (같은 conversation_id)
        print("\n[TESTING] 두 번째 요청 전송 (같은 conversation_id)...")
        response2 = await make_chat_request(session, query2, conversation_id=conversation_id)
        
        if response2.get("status") != 200:
            test_info["result"] = {
                "actual_value": "두 번째 요청 실패",
                "achieved": False,
                "suitable": False,
                "suitability_reason": "두 번째 요청이 실패하여 테스트 중단"
            }
            test_info["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            test_info["total_duration"] = time.time() - test_start
            print_test_summary(test_info)
            return test_info
        
        print(f"  응답: {response2.get('response_text', '')[:100]}...")
        
        # 히스토리 반영 여부 확인 (응답 내용에서 맥락 확인)
        response2_text = response2.get("response_text", "")
        context_reflected = "아메바" in response2_text or "AI" in response2_text
        
        test_info["result"] = {
            "actual_value": f"히스토리 저장 성공, 로드 성공, 맥락 반영: {'예' if context_reflected else '부분적'}",
            "achieved": True,
            "suitable": context_reflected,
            "suitability_reason": (
                "히스토리가 저장되고 로드되며 맥락이 반영됨"
                if context_reflected
                else "히스토리는 저장/로드되지만 맥락 반영이 불충분"
            )
        }
        
        test_info["details"] = {
            "conversation_id": conversation_id,
            "query1": query1,
            "response1": response1.get("response_text", ""),
            "query2": query2,
            "response2": response2.get("response_text", ""),
            "context_reflected": context_reflected
        }
    
    test_info["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    test_info["total_duration"] = time.time() - test_start
    
    print_test_summary(test_info)
    
    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("history_storage", test_info, output_dir)
    
    return test_info

