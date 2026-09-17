import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="AI-CPA 부실예측 시스템", layout="wide")
st.title("📊 AI-CPA Corporate Distress Predictor")
st.markdown("CPA의 회계 논리와 AI 데이터 파이프라인을 융합한 기업 부실 징후 스크리닝 시스템입니다.")

# 2. 사이드바 - 기업 티커 입력
st.sidebar.header("🔍 분석 대상 설정")
ticker = st.sidebar.text_input("구글/애플 등 주식 티커 입력 (예: GOOG, AAPL, TSLA)", "TSLA")

if ticker:
    try:
        with st.spinner("금융 데이터를 실시간으로 추출하고 검증하는 중..."):
            # yfinance 데이터 로드
            stock = yf.Ticker(ticker)
            info = stock.info
            company_name = info.get('longName', ticker)
            
            # 재무제표 로드 (최신 연도 데이터)
            balance_sheet = stock.balance_sheet
            financials = stock.financials
            
            # Z-Score에 필요한 회계 계정 추출
            total_assets = balance_sheet.loc['Total Assets'].iloc[0]
            
            # 야후 파이낸스 업데이트 대응: Total Liabilities 계정명 매칭 보정
            if 'Total Liabilities' in balance_sheet.index:
                total_liab = balance_sheet.loc['Total Liabilities'].iloc[0]
            else:
                total_liab = balance_sheet.loc['Total Liabilities Net Minor Interest'].iloc[0]
                
            working_capital = balance_sheet.loc['Working Capital'].iloc[0]
            re_retained = balance_sheet.loc['Retained Earnings'].iloc[0]
            ebit = financials.loc['EBIT'].iloc[0]
            market_cap = info.get('marketCap', 1)
            
            # 3. 알트만 Z-Score 재무 비율 계산 (CPA 검증 로직)
            X1 = working_capital / total_assets  # 유동성
            X2 = re_retained / total_assets     # 누적 수익성
            X3 = ebit / total_assets            # 자산 수익성
            X4 = market_cap / total_liab        # 재무 구조 (레버리지)
            
            # 제조업/비제조업 범용 모델 기준 가중치 산정 (Z = 1.2X1 + 1.4X2 + 3.3X3 + 0.6X4)
            z_score = (1.2 * X1) + (1.4 * X2) + (3.3 * X3) + (0.6 * X4)
            
            # 4. 결과 화면 UI 구성
            st.subheader(f"🏢 {company_name} ({ticker}) 신용평가 분석 결과")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(label="최종 Altman Z-Score", value=f"{z_score:.2f}")
                
                # 안전 구역 진단
                if z_score > 2.99:
                    st.success("🟢 **Safe Zone (안전)**: 재무 건전성이 매우 우수하며 부실 가능성이 극히 낮습니다.")
                elif 1.81 <= z_score <= 2.99:
                    st.warning("🟡 **Grey Zone (주의)**: 잠재적 리스크 요인이 존재하므로 정밀 모니터링이 필요합니다.")
                else:
                    st.error("🔴 **Distress Zone (부실 위험)**: 2년 내 파산 위험성이 높은 한계기업 징후가 포착되었습니다.")
            
            with col2:
                # 게이지 차트 시각화 (좌표 완벽 수정)
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = z_score,
                    domain = {'x':, 'y': [0, 1]},
                    title = {'text': "부실 예측 신호등"},
                    gauge = {
                        'axis': {'range': [0, 5]},
                        'bar': {'color': "black"},
                        'steps' : [
                            {'range': [0, 1.81], 'color': "red"},
                            {'range': [1.81, 2.99], 'color': "orange"},
                            {'range': [2.99, 5], 'color': "green"}
                        ],
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
                
            # 5. 세부 재무 비율 데이터 테이블 출력
            st.markdown("### 📊 상세 재무 비율 데이터 (CPA AI Validation)")
            df_metrics = pd.DataFrame({
                "재무 비율 지표": ["X1 (유동자산 비중)", "X2 (누적 수익성)", "X3 (총자산 수익률)", "X4 (재무 레버리지)"],
                "계산된 값": [f"{X1:.4f}", f"{X2:.4f}", f"{X3:.4f}", f"{X4:.4f}"],
                "회계적 의미": [
                    "총자산 대비 순유동자본 비율 (단기 지급능력)",
                    "총자산 대비 이익잉여금 비율 (기업의 역사적 생존력)",
                    "총자산 대비 EBIT 비율 (순수한 자산 효율성)",
                    "부채 총계 대비 시가총액 비율 (시장 평가 반영 레버리지)"
                ]
            })
            st.table(df_metrics)
            
    except Exception as e:
        st.error(f"데이터 추출 중 오류 발생: {e}. 회계 계정 매칭을 확인하거나 다른 티커를 입력해 주세요.")
