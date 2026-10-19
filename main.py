import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 스트림릿 페이지 설정 (제목, 레이아웃, 아이콘)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드", page_icon="🏢", layout="wide"
)

# 따뜻한 톤의 스타일 및 타이틀 출력
st.title("🏡 우리 동네 인구 피라미드 탐색기")
st.caption(
    "전국 읍·면·동의 연령별 남/여 인구 구조를 가로 막대그래프로 시각화합니다."
)
st.markdown("---")

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 (캐싱 적용으로 데이터 재로딩 속도 최적화)
# -----------------------------------------------------------------------------
# GitHub Blob URL을 raw 다운로드 가능한 URL로 전환
DATA_URL = "https://raw.githubusercontent.com/thswodud/population2/main/population_ts_yearly_gender.zip"


@st.cache_data
def load_data(url: str) -> pd.DataFrame:
    """GitHub에서 압축(zip) 형태의 CSV 데이터를 가져와 데이터프레임으로 변환합니다."""
    # pandas read_csv는 zip 파일과 그 내부의 csv를 자동으로 압축 해제하여 읽어옵니다.
    df = pd.read_csv(url, compression="zip")
    return df


# 데이터 로딩 안내 문구
with st.spinner("동네별 인구 데이터를 불러오는 중입니다... 잠시만 기다려주세요! ☕"):
    try:
        raw_df = load_data(DATA_URL)
    except Exception as e:
        st.error(
            f"데이터를 불러오는 중 오류가 발생했습니다. URL 및 인터넷 연결을 확인해주세요: {e}"
        )
        st.stop()

# 가장 최신 연도 데이터만 필터링
latest_year = raw_df["연도"].max()
df = raw_df[raw_df["연도"] == latest_year].copy()

st.sidebar.header("📍 지역 선택")
st.sidebar.info(
    f"📅 **기준 연도:** {latest_year}년 (가장 최신 데이터가 자동 선택되었습니다)"
)

# -----------------------------------------------------------------------------
# 3. 시도 -> 시군구 -> 동 3단계 드롭다운(Selectbox) 구성
# -----------------------------------------------------------------------------
# 1) 시도 선택
sido_list = sorted(df["시도"].dropna().unique())
selected_sido = st.sidebar.selectbox("1. 시·도 선택", sido_list)

# 2) 선택된 시도에 해당하는 시군구 필터링 후 선택
filtered_sigungu_df = df[df["시도"] == selected_sido]
sigungu_list = sorted(filtered_sigungu_df["시군구"].dropna().unique())
selected_sigungu = st.sidebar.selectbox("2. 시·군·구 선택", sigungu_list)

# 3) 선택된 시군구에 해당하는 동 필터링 후 선택
filtered_dong_df = filtered_sigungu_df[
    filtered_sigungu_df["시군구"] == selected_sigungu
]
dong_list = sorted(filtered_dong_df["동"].dropna().unique())
selected_dong = st.sidebar.selectbox("3. 읍·면·동 선택", dong_list)

# 최종적으로 선택된 지역의 1개 행 추출
target_row = filtered_dong_df[filtered_dong_df["동"] == selected_dong]

if target_row.empty:
    st.warning("선택한 지역의 데이터가 존재하지 않습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 4. 연령대(0세 ~ 100세 이상) 데이터 정리
# -----------------------------------------------------------------------------
# 0세부터 100세 이상까지의 연령 라벨 생성 (0세, 1세, ..., 99세, 100세 이상)
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

# 데이터프레임 컬럼 이름에 맞게 남성/여성 컬럼 리스트 구성
male_cols = [f"남_{label}" for label in age_labels]
female_cols = [f"여_{label}" for label in age_labels]

# 선택된 동네의 남/여 인구 수 수치 추출 (Series 형태 -> list 변환)
male_pop = target_row[male_cols].iloc[0].values
female_pop = target_row[female_cols].iloc[0].values

# -----------------------------------------------------------------------------
# 5. Plotly 인구 피라미드 (가로 막대그래프) 생성
# -----------------------------------------------------------------------------
# 남성 인구수는 왼쪽 배치를 위해 음수(-) 값으로 변환
male_pop_neg = [-x for x in male_pop]

fig = go.Figure()

# (1) 남성 데이터 추가 (왼쪽 방향) - 따뜻한 네이비/블루 톤
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=male_pop_neg,
        name="남성",
        orientation="h",
        marker=dict(color="#4A7BB0"),  # 포근한 블루
        hovertemplate="<b>%{y} 남성</b><br>인구수: %{customdata:,}명<extra></extra>",
        customdata=male_pop,  # 툴팁에는 실제 양수 인구 표시
    )
)

# (2) 여성 데이터 추가 (오른쪽 방향) - 따뜻한 핑크/코랄 톤
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=female_pop,
        name="여성",
        orientation="h",
        marker=dict(color="#E88A8A"),  # 포근한 코랄 핑크
        hovertemplate="<b>%{y} 여성</b><br>인구수: %{x:,}명<extra></extra>",
    )
)

# (3) 그래프 레이아웃 설정
# x축의 음수 눈금을 실제 양수로 표시하기 위한 x축 범위 계산
max_val = max(max(male_pop), max(female_pop))
# 여유 공간을 포함한 축 범위 설정
x_limit = max_val * 1.1 if max_val > 0 else 100

fig.update_layout(
    title=dict(
        text=f"<b>{selected_sido} {selected_sigungu} {selected_dong}</b> 인구 피라미드 ({latest_year}년)",
        font=dict(size=20, color="#333333"),
        x=0.0,
        y=0.95,
    ),
    barmode="overlay",  # 양쪽으로 갈라지는 막대 형태
    bargap=0.1,  # 막대 간격
    height=800,  # 0세~100세 이상이 훤히 보이도록 높이 충분히 부여
    paper_bgcolor="#FAF8F5",  # 따뜻한 연한 베이지 바탕
    plot_bgcolor="#FFFFFF",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=13),
    ),
    margin=dict(l=60, r=60, t=100, b=50),
)

# X축 설정 (음수를 절대값 형태의 정수로 보여주기)
# tickvals와 ticktext를 설정하여 -100, 0, 100 -> 100, 0, 100 으로 표기
step = max(1, int(x_limit / 4))
ticks = list(range(0, int(x_limit) + step, step))
tick_vals = [-t for t in reversed(ticks)] + ticks[1:]
tick_text = [f"{abs(t):,}" for t in tick_vals]

fig.update_xaxes(
    title="인구수 (명)",
    range=[-x_limit, x_limit],
    tickvals=tick_vals,
    ticktext=tick_text,
    gridcolor="#EAEAEA",
    zerolinecolor="#888888",
    zerolinewidth=1.5,
)

# Y축 설정 (핵심: 0세가 맨 아래, 100세 이상이 맨 위로 고정)
# y축 카테고리 순서를 0세부터 100세 이상까지 명시적으로 고정
fig.update_yaxes(
    title="연령",
    type="category",
    categoryorder="array",
    categoryarray=age_labels,  # ['0세', '1세', ..., '100세 이상'] 정렬 고정
    gridcolor="#F0F0F0",
    dtick=5,  # 5세 단위로 눈금 라벨 표시 (깔끔한 시각화)
)

# -----------------------------------------------------------------------------
# 6. 대시보드 메인 화면 레이아웃 구성
# -----------------------------------------------------------------------------
# 상단 주요 요약 지표 (Metrics)
col1, col2, col3 = st.columns(3)
total_male = int(sum(male_pop))
total_female = int(sum(female_pop))
total_pop = total_male + total_female

with col1:
    st.metric("총 인구수", f"{total_pop:,} 명")
with col2:
    st.metric("남성 인구수", f"{total_male:,} 명")
with col3:
    st.metric("여성 인구수", f"{total_female:,} 명")

st.markdown("<br>", unsafe_allow_html=True)

# Plotly 차트 출력
st.plotly_chart(fig, use_container_width=True)

# 푸터 문구
st.caption("💡 그래프 막대에 마우스를 올리면 정확한 연령별 인구수를 확인할 수 있습니다.")
