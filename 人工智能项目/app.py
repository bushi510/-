import streamlit as st
import math

# Strictly reusing your existing modules without changing any core logic
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

# Page configuration optimized for mobile
st.set_page_config(page_title="Optimal Samples Selection System", layout="centered", initial_sidebar_state="collapsed")

st.title("Optimal Samples Selection System")

# Mobile-friendly tabs instead of CLI numbered menus
tab1, tab2 = st.tabs(["▶️ Run New Selection", "📁 Manage Saved Results"])

with tab1:
    st.header("Parameter Settings")
    
    # Columns will automatically stack vertically on mobile screens
    col1, col2 = st.columns(2)
    with col1:
        m = st.number_input("m (Sample Pool Size)", min_value=1, value=50, step=1)
        n = st.number_input("n (Number of Samples)", min_value=1, value=10, step=1)
        k = st.number_input("k (Candidate Combination Size)", min_value=1, value=5, step=1)
    with col2:
        j = st.number_input("j (Target Combination Size)", min_value=1, value=4, step=1)
        s = st.number_input("s (Coverage Overlap Requirement)", min_value=1, value=3, step=1)

    st.divider()
    st.subheader("Sample Input Mode")
    sample_mode = st.radio("Select data generation method:", ["Random n samples", "Manual input n samples"])

    samples = []
    if sample_mode == "Manual input n samples":
        raw_samples = st.text_input(f"Enter {n} sample numbers separated by spaces:")
        if raw_samples:
            try:
                samples = parse_user_samples(raw_samples, m, n)
                st.success(f"Successfully parsed samples: {samples}")
            except ValueError as e:
                st.error(f"Sample input error: {e}")
    else:
        # Cache random results to prevent samples from changing on every UI interaction
        if st.button("Generate Random Samples Preview"):
            st.session_state['random_samples'] = choose_samples_randomly(m, n)
            
        if 'random_samples' in st.session_state:
            samples = st.session_state['random_samples']
            st.info(f"Currently locked random samples: {samples}")

    st.divider()
    st.subheader("Algorithm Options")
    randomized = st.toggle("Enable randomized greedy?")
    runs = 1
    if randomized:
        runs = st.number_input("Enter number of runs:", min_value=1, value=10, step=1)

    st.write("") # Add spacing for mobile tapping
    if st.button("🚀 Execute Selection", type="primary", use_container_width=True):
        try:
            # 1. Validate parameters
            validate_parameters(m, n, k, j, s)

            if not samples:
                if sample_mode == "Random n samples":
                    samples = choose_samples_randomly(m, n)
                else:
                    st.warning("Please enter valid sample data first.")
                    st.stop()

            # 2. Check for large calculation warnings
            candidate_count = math.comb(n, k)
            target_count = math.comb(n, j)
            estimated_entries = estimate_coverage_entries(n, k, j, s)

            warning_msg = []
            if candidate_count > LARGE_COMBINATION_WARNING_THRESHOLD:
                warning_msg.append(f"candidate combination count is large ({candidate_count})")
            if target_count > LARGE_COMBINATION_WARNING_THRESHOLD:
                warning_msg.append(f"target combination count is large ({target_count})")
            if estimated_entries > LARGE_COMBINATION_WARNING_THRESHOLD * 20:
                warning_msg.append("coverage map may require significant memory/time")

            if warning_msg:
                st.warning("⚠️ Warning: " + "; ".join(warning_msg) + ". Forcing execution anyway...")

            # 3. Run core algorithm
            with st.spinner('Algorithm is running intensive computations, please keep the screen on...'):
                results, stats = solve(samples, k, j, s, runs=runs, randomized=randomized)
                file_path = save_result(m, n, k, j, s, samples, results, stats)

            # 4. Display results
            st.success("Computation complete!")
            
            with st.expander("📊 View Algorithm Statistics", expanded=True):
                st.json(stats)

            st.write("### Final Result Groups")
            for idx, grp in enumerate(results, start=1):
                st.code(f"{idx}: " + " ".join(str(v) for v in grp))

            st.info(f"Saved file path: {file_path}")

        except ValueError as e:
            st.error(f"Parameter error: {e}")
        except Exception as e:
            st.error(f"Execution failed: {e}")

with tab2:
    st.header("Saved Result Files")
    filenames = list_result_files()

    if not filenames:
        st.info("No saved result files found.")
    else:
        selected_file = st.selectbox("Select a file to manage:", filenames)

        col_view, col_del = st.columns(2)
        with col_view:
            if st.button("📄 View Content", use_container_width=True):
                try:
                    content = display_result_file(selected_file)
                    st.text_area("File Content (Read-only)", content, height=400)
                except Exception as e:
                    st.error(f"Failed to display file: {e}")

        with col_del:
            if st.button("🗑️ Delete File", type="primary", use_container_width=True):
                try:
                    delete_result_file(selected_file)
                    st.success(f"File {selected_file} deleted successfully! (Please switch tabs to refresh the list)")
                except Exception as e:
                    st.error(f"Failed to delete file: {e}")
