# CyberGuard Development Workflow

## Branching Strategy

- main contains production-ready code.
- Every new task is developed in a feature branch.
- Branch naming:
  - feature/<description>
  - fix/<description>
  - docs/<description>
  - refactor/<description>
  - chore/<description>
- Branches are deleted after merge.

---

## Commit Convention

Format

[type]: description

Examples

feat: implement authentication pipeline

fix: correct failed login calculation

docs: update dashboard documentation

refactor: simplify risk scoring logic

chore: update dependencies

This convention provides a clean Git history and supports changelog generation.

---

## Pull Request Process

Every PR must:

- Link to related GitHub Issue
- Describe changes
- Pass GitHub Actions
- Receive at least one approval
- Be reviewed for:
  - correctness
  - readability
  - data integrity
  - testing

---

## Issue Tracking

Every feature begins with a GitHub Issue.

Issues include:

- title
- description
- label
- assignee

Issues are closed only after the related Pull Request is merged.

---

## Python Data Workflow Execution

This section documents the production data pipeline script (`scripts/data_workflow.py`).

### How to Execute the Script
The script should be run from the command line inside the project root:
```bash
python scripts/data_workflow.py
```

To capture execution results in a log or report file:
```bash
python scripts/data_workflow.py > output/sample_run.txt
```

### Modular Function Structure
The script implements a three-function pattern to maintain separation of concerns:
1. **`ingest_data(filepath)`**: Loads the raw dataset from a local CSV or JSON file and returns a Pandas DataFrame. It does not perform transformations.
2. **`process_data(df)`**: Cleans and prepares the data. It handles deduplication, missing value imputation using median values, and filters rows.
3. **`output_results(df, output_path)`**: Saves the transformed dataframe to a clean CSV and prints execution metadata and statistics to the console.

### Customizing for New Datasets
To adapt the pipeline for a different input source or target path:
1. Open [data_workflow.py](file:///w:/Kalvium/5th%20Sem/SW2627-DataProduct-CyberGuard/scripts/data_workflow.py).
2. Modify the file path parameters in the main execution block:
   ```python
   input_file = "data/raw/your_new_dataset.csv"
   output_file = "output/your_processed_output.csv"
   ```
3. Update `process_data()` logic to perform dataset-specific validation or cleaning rules.