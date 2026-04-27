import streamlit as st
import math

# 严格复用你原有的模块，不改变任何算法与底层逻辑
from optimal_sample_selection.solver import estimate_coverage_entries, solve
from optimal_sample_selection.storage import (
    delete_result_file,
    display_result_file,
    list_result_files,
    save_result,
)
from optimal_sample_selection.utils import (
    LARGE_COMBINATION_WARNING_THRESHOLD,
    choose_samples_randomly,
    parse_user_samples,
    validate_parameters,
)

# 页面基础配置：优化移动端显示比例
st.set_page_config(page_title="最优样本选择系统", layout="centered", initial_sidebar_state="collapsed")

st.title("最优样本选择系统")

# 使用移动端友好的标签页代替原本的数字菜单
tab1, tab2 = st.tabs(["▶️ 运行新选择", "📁 历史结果管理"])

with tab1:
    st.header("参数设置")
    
    # 移动端会自动将 columns 折叠为上下排列
    col1, col2 = st.columns(2)
    with col1:
        m = st.number_input("m (样本池大小)", min_value=1, value=50, step=1)
        n = st.number_input("n (抽取样本数)", min_value=1, value=10, step=1)
        k = st.number_input("k (候选组合大小)", min_value=1, value=5, step=1)
    with col2:
        j = st.number_input("j (目标组合大小)", min_value=1, value=4, step=1)
        s = st.number_input("s (覆盖重叠要求)", min_value=1, value=3, step=1)

    st.divider()
    st.subheader("样本输入模式")
    sample_mode = st.radio("请选择数据生成方式：", ["随机生成 n 个样本", "手动输入 n 个样本"])

    samples = []
    if sample_mode == "手动输入 n 个样本":
        raw_samples = st.text_input(f"请输入 {n} 个数字（用空格隔开）：")
        if raw_samples:
            try:
                samples = parse_user_samples(raw_samples, m, n)
                st.success(f"已成功解析样本: {samples}")
            except ValueError as e:
                st.error(f"样本输入错误: {e}")
    else:
        # 缓存随机结果，防止每次页面交互时样本乱跳
        if st.button("生成随机样本预览"):
            st.session_state['random_samples'] = choose_samples_randomly(m, n)
            
        if 'random_samples' in st.session_state:
            samples = st.session_state['random_samples']
            st.info(f"当前锁定的随机样本: {samples}")

    st.divider()
    st.subheader("算法选项")
    randomized = st.toggle("启用 Randomized Greedy (随机贪心)?")
    runs = 1
    if randomized:
        runs = st.number_input("运行次数 (Runs):", min_value=1, value=10, step=1)

    st.write("") # 增加点击留白
    if st.button("🚀 开始执行求解", type="primary", use_container_width=True):
        try:
            # 1. 验证参数
            validate_parameters(m, n, k, j, s)

            if not samples:
                if sample_mode == "随机生成 n 个样本":
                    samples = choose_samples_randomly(m, n)
                else:
                    st.warning("请先输入合法的样本数据。")
                    st.stop()

            # 2. 检查大计算量警告
            candidate_count = math.comb(n, k)
            target_count = math.comb(n, j)
            estimated_entries = estimate_coverage_entries(n, k, j, s)

            warning_msg = []
            if candidate_count > LARGE_COMBINATION_WARNING_THRESHOLD:
                warning_msg.append(f"候选组合数量较大 ({candidate_count})")
            if target_count > LARGE_COMBINATION_WARNING_THRESHOLD:
                warning_msg.append(f"目标组合数量较大 ({target_count})")
            if estimated_entries > LARGE_COMBINATION_WARNING_THRESHOLD * 20:
                warning_msg.append("预估覆盖图映射可能会消耗大量内存与时间")

            if warning_msg:
                st.warning("⚠️ 警告: " + "；".join(warning_msg) + "。正在强制运行中...")

            # 3. 运行核心算法
            with st.spinner('底层算法正在高强度运算中，请保持屏幕常亮...'):
                results, stats = solve(samples, k, j, s, runs=runs, randomized=randomized)
                file_path = save_result(m, n, k, j, s, samples, results, stats)

            # 4. 展示结果
            st.success("运算完成！")
            
            with st.expander("📊 查看算法统计数据", expanded=True):
                st.json(stats)

            st.write("### 最终结果组合")
            for idx, grp in enumerate(results, start=1):
                st.code(f"{idx}: " + " ".join(str(v) for v in grp))

            st.info(f"结果已调用 storage.py 保存至: {file_path}")

        except ValueError as e:
            st.error(f"参数验证失败: {e}")
        except Exception as e:
            st.error(f"执行时发生底层错误: {e}")

with tab2:
    st.header("已保存的结果文件")
    filenames = list_result_files()

    if not filenames:
        st.info("当前 data 目录下暂无历史结果。")
    else:
        selected_file = st.selectbox("选择要管理的文件：", filenames)

        col_view, col_del = st.columns(2)
        with col_view:
            if st.button("📄 查看内容", use_container_width=True):
                try:
                    content = display_result_file(selected_file)
                    st.text_area("文件内容 (只读)", content, height=400)
                except Exception as e:
                    st.error(f"读取失败: {e}")

        with col_del:
            if st.button("🗑️ 删除文件", type="primary", use_container_width=True):
                try:
                    delete_result_file(selected_file)
                    st.success(f"文件 {selected_file} 已删除！(请切换一下标签页刷新列表)")
                except Exception as e:
                    st.error(f"删除失败: {e}")
