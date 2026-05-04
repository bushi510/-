import streamlit as st
import math

# 恢复你最初正确的包导入方式！
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

# 下面是保留了完美 UI 优化的代码
st.set_page_config(page_title="最优样本选择系统", layout="centered", initial_sidebar_state="collapsed")

st.title("最优样本选择系统")

tab1, tab2 = st.tabs(["▶️ 运行新选择", "📁 历史结果管理"])

with tab1:
    st.header("参数设置")
    st.info("💡 **系统约束说明：** 为防止 NP-Hard 问题引发的内存溢出，抽取样本数 (n) 已限制在 7-25 之间。")

    col1, col2 = st.columns(2)
    with col1:
        m = st.number_input("m (样本池大小, m ≥ n)", min_value=1, value=50, step=1, help="总样本池的大小，数学逻辑上必须大于或等于 n")
        n = st.number_input("n (抽取样本数, 7 ≤ n ≤ 25)", min_value=7, max_value=25, value=10, step=1, help="核心控制参数。受限于组合爆炸，系统硬性限制为 7 到 25 之间")
        k = st.number_input("k (候选组合大小, k ≤ n)", min_value=1, value=6, step=1, help="每个候选组包含的样本数量，不能超过抽取样本数 n")
                            
    with col2:
        j = st.number_input("j (目标组合大小, j < k)", min_value=1, value=4, step=1, help="需要被覆盖的目标子集大小，必须小于候选组大小 k")
        s = st.number_input("s (覆盖重叠要求, s ≤ j)", min_value=1, value=3, step=1, help="每个目标子集必须满足的最小交集/重叠数，不能超过 j")

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

    st.write("") 
    if st.button("🚀 开始执行求解", type="primary", use_container_width=True):
        try:
            validate_parameters(m, n, k, j, s)

            if not samples:
                if sample_mode == "随机生成 n 个样本":
                    samples = choose_samples_randomly(m, n)
                else:
                    st.warning("请先输入合法的样本数据。")
                    st.stop()

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

            with st.spinner('底层算法正在高强度运算中，请保持屏幕常亮...'):
                results, stats = solve(samples, k, j, s, runs=runs, randomized=randomized)
                file_path = save_result(m, n, k, j, s, samples, results, stats)

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
