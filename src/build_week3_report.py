from pathlib import Path
import json
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports' / 'Week_3_Predictive_Analytics_and_Risk_Modeling.docx'
SUMMARY = json.loads((ROOT / 'data' / 'processed' / 'week3_risk_model_summary.json').read_text(encoding='utf-8'))
reg = pd.read_csv(ROOT / 'data' / 'processed' / 'week3_delay_regression_metrics.csv')
clf = pd.read_csv(ROOT / 'data' / 'processed' / 'week3_cost_overrun_classification_metrics.csv')
scenarios = pd.read_csv(ROOT / 'data' / 'processed' / 'week3_scenario_analysis.csv')
coefs = pd.read_csv(ROOT / 'data' / 'processed' / 'week3_interpretable_model_coefficients.csv')

NAVY = '17365D'
BLUE = '2878A5'
TEAL = '168C8C'
ORANGE = 'E78132'
NUM_COUNTER = 0
PALE = 'EAF2F8'
PALE_ORANGE = 'FDF0E4'
GREY = 'F3F5F7'
DARK = '243447'
MUTED = '5E6B75'
WHITE = 'FFFFFF'


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn('w:shd'))
    if shd is None:
        shd = OxmlElement('w:shd')
        tcPr.append(shd)
    shd.set(qn('w:fill'), fill)


def set_cell_margins(cell, top=70, start=95, bottom=70, end=95):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.first_child_found_in('w:tcMar')
    if tcMar is None:
        tcMar = OxmlElement('w:tcMar')
        tcPr.append(tcMar)
    for m, v in [('top', top), ('start', start), ('bottom', bottom), ('end', end)]:
        node = tcMar.find(qn('w:' + m))
        if node is None:
            node = OxmlElement('w:' + m)
            tcMar.append(node)
        node.set(qn('w:w'), str(v))
        node.set(qn('w:type'), 'dxa')


def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader')
    tblHeader.set(qn('w:val'), 'true')
    trPr.append(tblHeader)


def set_cell_text(cell, text, bold=False, color=DARK, size=8.5):
    cell.text = ''
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.03
    r = p.add_run(str(text))
    r.bold = bold
    r.font.name = 'Aptos'
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_margins(cell)


def set_table_borders(table, color='CCD6E0', sz='5'):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = tblPr.first_child_found_in('w:tblBorders')
    if borders is None:
        borders = OxmlElement('w:tblBorders')
        tblPr.append(borders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        tag = 'w:' + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn('w:val'), 'single')
        element.set(qn('w:sz'), sz)
        element.set(qn('w:space'), '0')
        element.set(qn('w:color'), color)


def add_table(doc, headers, rows, widths=None, font_size=8.3):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False if widths else True
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for j, h in enumerate(headers):
        set_cell_text(hdr.cells[j], h, True, WHITE, font_size)
        shade(hdr.cells[j], NAVY)
        if widths: hdr.cells[j].width = Inches(widths[j])
    for i, row in enumerate(rows):
        cells = table.add_row().cells
        for j, value in enumerate(row):
            set_cell_text(cells[j], value, False, DARK, font_size)
            if i % 2 == 1:
                shade(cells[j], GREY)
            if widths: cells[j].width = Inches(widths[j])
    set_table_borders(table)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_par(doc, text='', style=None, bold_lead=None, color=None, size=None, italic=False):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.12
    if bold_lead and text.startswith(bold_lead):
        r1 = p.add_run(bold_lead); r1.bold = True
        r2 = p.add_run(text[len(bold_lead):])
        runs = [r1, r2]
    else:
        runs = [p.add_run(text)]
    for r in runs:
        r.font.name = 'Aptos'
        if size: r.font.size = Pt(size)
        if color: r.font.color.rgb = RGBColor.from_string(color)
        r.italic = italic
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style='List Bullet' if level == 0 else 'List Bullet 2')
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.08
    r = p.add_run(text)
    r.font.name = 'Aptos'; r.font.size = Pt(9.2); r.font.color.rgb = RGBColor.from_string(DARK)
    return p


def add_num(doc, text):
    global NUM_COUNTER
    NUM_COUNTER += 1
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.22)
    p.paragraph_format.first_line_indent = Inches(-0.22)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.08
    r = p.add_run(f'{NUM_COUNTER}.  {text}')
    r.font.name='Aptos'; r.font.size=Pt(9.2); r.font.color.rgb=RGBColor.from_string(DARK)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.space_before = Pt(5 if level == 1 else 3)
    p.paragraph_format.space_after = Pt(5 if level == 1 else 3)
    return p


def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run(text)
    r.italic = True; r.font.name = 'Aptos'; r.font.size = Pt(8); r.font.color.rgb = RGBColor.from_string(MUTED)
    return p


def add_image(doc, filename, width=6.25):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(ROOT / 'reports' / 'figures' / filename), width=Inches(width))
    return p


def add_side_by_side_images(doc, entries, width=3.05):
    """Place pairs of figures and captions in a borderless two-column table."""
    table = doc.add_table(rows=2, cols=len(entries))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for j, (filename, caption) in enumerate(entries):
        img_cell = table.cell(0, j)
        img_cell.text = ''
        img_p = img_cell.paragraphs[0]
        img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        img_p.paragraph_format.space_after = Pt(0)
        img_p.add_run().add_picture(str(ROOT / 'reports' / 'figures' / filename), width=Inches(width))
        cap_cell = table.cell(1, j)
        cap_cell.text = ''
        cap_p = cap_cell.paragraphs[0]
        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap_p.paragraph_format.space_before = Pt(0)
        cap_p.paragraph_format.space_after = Pt(3)
        run = cap_p.add_run(caption)
        run.italic = True
        run.font.name = 'Aptos'
        run.font.size = Pt(7.2)
        run.font.color.rgb = RGBColor.from_string(MUTED)
        img_cell.width = Inches(width + 0.08)
        cap_cell.width = Inches(width + 0.08)
        for cell in (img_cell, cap_cell):
            set_cell_margins(cell, top=15, start=15, bottom=15, end=15)
    # Hide table borders for an editorial, side-by-side figure treatment.
    tblPr = table._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        el = OxmlElement('w:' + edge)
        el.set(qn('w:val'), 'nil')
        borders.append(el)
    tblPr.append(borders)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_page_field(paragraph):
    run = paragraph.add_run()
    fldChar1 = OxmlElement('w:fldChar'); fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText'); instrText.set(qn('xml:space'), 'preserve'); instrText.text = ' PAGE '
    fldChar2 = OxmlElement('w:fldChar'); fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1); run._r.append(instrText); run._r.append(fldChar2)


def fmt_metric(x, digits=3):
    return f'{float(x):.{digits}f}'


doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(0.62)
sec.bottom_margin = Inches(0.60)
sec.left_margin = Inches(0.70)
sec.right_margin = Inches(0.70)
sec.header_distance = Inches(0.28)
sec.footer_distance = Inches(0.28)

styles = doc.styles
styles['Normal'].font.name = 'Aptos'
styles['Normal'].font.size = Pt(9.4)
styles['Normal'].font.color.rgb = RGBColor.from_string(DARK)
styles['Normal'].paragraph_format.space_after = Pt(4)
for stylename, size, color in [('Title', 30, NAVY), ('Heading 1', 17, NAVY), ('Heading 2', 11.5, BLUE), ('Heading 3', 10, TEAL)]:
    st = styles[stylename]
    st.font.name = 'Aptos Display' if stylename in ('Title','Heading 1') else 'Aptos'
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor.from_string(color)

header = sec.header.paragraphs[0]
header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
header.paragraph_format.space_after = Pt(0)
r = header.add_run('CONSTRUCTION PROJECT DATA SCIENCE ANALYST  |  WEEK 3')
r.font.name = 'Aptos'; r.font.size = Pt(7.2); r.font.bold = True; r.font.color.rgb = RGBColor.from_string(BLUE)
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.paragraph_format.space_before = Pt(0)
r = footer.add_run('Aman Yadav  •  Predictive Analytics & Risk Modeling  |  Page ')
r.font.name = 'Aptos'; r.font.size = Pt(7.5); r.font.color.rgb = RGBColor.from_string(MUTED)
add_page_field(footer)

# PAGE 1 - Cover
p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(82); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('CONSTRUCTION PROJECT\nRISK ANALYTICS')
r.font.name='Aptos Display'; r.font.size=Pt(30); r.font.bold=True; r.font.color.rgb=RGBColor.from_string(NAVY)
p = doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(13); p.paragraph_format.space_after=Pt(14)
r = p.add_run('Predictive Analytics and Risk Modeling')
r.font.name='Aptos Display'; r.font.size=Pt(20); r.font.bold=True; r.font.color.rgb=RGBColor.from_string(ORANGE)
p = doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('Week 3 Technical Deliverable')
r.font.name='Aptos'; r.font.size=Pt(12); r.font.color.rgb=RGBColor.from_string(MUTED)

# accent line
line = doc.add_paragraph(); line.alignment = WD_ALIGN_PARAGRAPH.CENTER; line.paragraph_format.space_before=Pt(20); line.paragraph_format.space_after=Pt(20)
r=line.add_run('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
r.font.size=Pt(11); r.font.color.rgb=RGBColor.from_string(TEAL)

cover_rows = [
    ('Prepared by', 'Aman Yadav'),
    ('Internship', 'Construction Project Data Science Analyst Internship in Kochi'),
    ('Tools', 'Python, pandas, NumPy, scikit-learn, Matplotlib'),
    ('Dataset', '500 simulated construction-project records'),
    ('Focus', 'Schedule delay forecasting, cost-overrun risk, scenario planning, and mitigation'),
]
add_table(doc, ['PROJECT DETAILS', 'DESCRIPTION'], cover_rows, widths=[1.55, 4.95], font_size=9.4)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(24)
r=p.add_run('SIMULATION-BASED PORTFOLIO REPORT')
r.font.name='Aptos'; r.font.size=Pt(10); r.font.bold=True; r.font.color.rgb=RGBColor.from_string(TEAL)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run('All records and measured outcomes in this report are synthetic. Results demonstrate a modeling workflow; they are not validated forecasts for real projects.')
r.font.name='Aptos'; r.font.size=Pt(8.5); r.font.italic=True; r.font.color.rgb=RGBColor.from_string(MUTED)

doc.add_page_break()

# PAGE 2 - Executive summary
add_heading(doc, '1. Executive Summary', 1)
add_par(doc, 'This report demonstrates a Python-based workflow for identifying construction-project risks, estimating schedule delays, classifying the likelihood of a material cost overrun, and testing illustrative mitigation scenarios. It uses a reproducible synthetic dataset of 500 projects because no verified project-level source data was supplied for this exercise.')
add_par(doc, 'The analysis compares a linear-regression baseline with a random-forest regressor for delay forecasting, and logistic regression with a random-forest classifier for identifying projects expected to exceed a 10% cost-overrun threshold. An 80/20 train-test split is used, with five-fold cross-validation carried out only on the training set. Preprocessing is placed inside scikit-learn pipelines to reduce leakage risk.')

best_reg = reg.iloc[0]
best_clf = clf.iloc[0]
metrics_rows = [
    ('Delay model', str(best_reg['model']), f"Holdout R² = {best_reg['test_R2']:.3f}; MAE = {best_reg['test_MAE_days']:.2f} days"),
    ('Cost-risk model', str(best_clf['model']), f"Holdout ROC-AUC = {best_clf['test_ROC_AUC']:.3f}; recall = {best_clf['test_recall']:.3f}"),
    ('Synthetic projects', str(SUMMARY['dataset_rows']), f"Mean simulated delay = {SUMMARY['mean_delay_days']:.1f} days"),
    ('Cost-overrun label', 'At least 10%', f"{SUMMARY['cost_overrun_rate_10pct']*100:.1f}% of simulated rows meet the threshold"),
]
add_table(doc, ['DECISION AREA', 'SELECTED BASELINE', 'HOLDOUT / DATA SUMMARY'], metrics_rows, widths=[1.3, 1.65, 3.55], font_size=8.4)
add_heading(doc, 'Key findings', 2)
add_bullet(doc, f"The linear-regression model achieved a holdout MAE of {best_reg['test_MAE_days']:.2f} days and R² of {best_reg['test_R2']:.3f}; its five-fold training CV mean R² was {best_reg['cv_R2_mean']:.3f}.")
add_bullet(doc, f"The logistic-regression cost classifier achieved ROC-AUC {best_clf['test_ROC_AUC']:.3f}, recall {best_clf['test_recall']:.3f}, and precision {best_clf['test_precision']:.3f}. The precision-recall trade-off matters when review capacity is limited.")
add_bullet(doc, 'The illustrative combined-control scenario lowered the selected model’s predicted delay from 73.30 to 57.97 days for one representative high-risk project. This is a model-based scenario, not proof that interventions will causally produce the same benefit.')
add_heading(doc, 'Recommended use', 2)
add_par(doc, 'Treat model outputs as an early-warning aid for weekly project-control meetings. Use a risk flag to trigger review by the project manager, planner, procurement lead, cost controller, and safety officer; do not automate contractual, financial, or safety decisions from a model score alone.')


doc.add_page_break()
# PAGE 3 - risk register
add_heading(doc, '2. Construction Risk Identification Framework', 1)
add_par(doc, 'Construction outcomes are affected by interacting schedule, budget, site, people, supply-chain, design, and safety conditions. The risk register below turns the task brief into observable signals and practical responses. Risk occurrence and severity should be assessed with project teams before any formal risk rating is approved.')
risk_rows = [
    ('Schedule delay', 'Late materials, weather, low labor availability, rework, design changes', 'Delayed handovers, liquidated damages, disruption to follow-on trades', 'Schedule variance, supplier delay days, rework count, labor availability'),
    ('Cost overrun', 'Quantity growth, inflation, change orders, rework, delay-related overhead', 'Margin erosion and additional funding requirements', 'Forecast-at-completion variance, change orders, procurement price variance'),
    ('Ground/site conditions', 'Uncertain soil, access constraints, hidden services, drainage', 'Redesign, additional plant, foundation or dewatering costs', 'Ground-risk score, site investigation exceptions, unresolved constraints'),
    ('Procurement and supplier', 'Long lead items, supplier quality, delivery capacity, single-source risk', 'Workface stoppage and substitute-material costs', 'Supplier lead-time variance, on-time-in-full rate, open purchase orders'),
    ('Labor and subcontractors', 'Shortage of skilled workers, absenteeism, low productivity, poor coordination', 'Low output, overtime, rework, unsafe workarounds', 'Labor availability, planned vs actual productivity, subcontractor rating'),
    ('Design/change/rework', 'Incomplete drawings, late client decisions, clashes, unclear requirements', 'Rework, idle crews, claims, delayed approvals', 'Design changes, RFIs aging, inspection failures, rework events'),
    ('Safety incidents', 'Insufficient training, unsafe conditions, fatigue, weak supervision', 'Worker harm, stoppage, investigation, reputational and legal impact', 'Training completion, near misses, inspection close-out, incident counts'),
]
add_table(doc, ['RISK', 'DRIVERS / EARLY SIGNALS', 'POTENTIAL IMPACT', 'MONITORING INDICATORS'], risk_rows, widths=[1.05, 2.1, 1.75, 1.6], font_size=7.6)
add_heading(doc, 'Risk prioritisation principle', 2)
add_par(doc, 'A risk register should combine likelihood, impact, urgency, detectability, and the time available to respond. The numeric models in this exercise forecast schedule and cost outcomes; safety incidents are included as simulated monitoring data but are not presented as a validated safety prediction model. High-consequence safety hazards require formal safety procedures regardless of a statistical score.')


doc.add_page_break()
# PAGE 4 - Data profile and dictionary
add_heading(doc, '3. Simulated Dataset and Target Definitions', 1)
add_par(doc, f"The generated file contains {SUMMARY['dataset_rows']} rows and {SUMMARY['dataset_columns']} columns. Each row represents a simulated project with a synthetic project identifier. The dataset has no real contractor, address, worker, or client records. The fixed random seed makes the exercise reproducible.")
data_rows = [
    ('project_type / project_scale', 'Categorical', 'Group projects for comparisons; one-hot encoded in models.'),
    ('contract_value_inr_mn', 'Numeric', 'Approximate contract value in INR million; project-size context.'),
    ('planned_duration_days', 'Numeric', 'Planned project duration in days.'),
    ('complexity_score_1_5', 'Ordinal numeric', 'Higher score represents greater coordination / technical complexity.'),
    ('rainfall_days', 'Count', 'Simulated days of rainfall disruption.'),
    ('supplier_delay_days', 'Count', 'Simulated procurement delay exposure.'),
    ('labor_availability_pct', 'Percentage', 'Estimated workforce availability.'),
    ('design_changes_count', 'Count', 'Change events recorded for the simulated project.'),
    ('ground_risk_score_1_5', 'Ordinal numeric', 'Risk score for subsurface / site uncertainty.'),
    ('safety_training_score', 'Score', 'Simulated training / preparedness score; not a substitute for safety audits.'),
    ('schedule_buffer_pct', 'Percentage', 'Schedule contingency allowance.'),
    ('subcontractor_rating_1_5', 'Score', 'Simulated subcontractor performance rating.'),
    ('inspection_rework_events', 'Count', 'Simulated inspection issues and rework events.'),
]
add_table(doc, ['INPUT FIELD(S)', 'TYPE', 'MODEL / PROJECT-CONTROL PURPOSE'], data_rows, widths=[2.1, 1.2, 3.2], font_size=7.9)
add_heading(doc, 'Prediction targets', 2)
add_bullet(doc, f"Schedule regression target: actual_delay_days (mean {SUMMARY['mean_delay_days']:.2f}; median {SUMMARY['median_delay_days']:.2f}). Values are generated from selected risk drivers plus random noise and clipped to be non-negative.")
add_bullet(doc, f"Cost classification target: cost_overrun_flag_10pct equals 1 where simulated cost_overrun_pct is at least 10%; {SUMMARY['cost_overrun_rate_10pct']*100:.1f}% of rows are positive cases.")
add_bullet(doc, f"Secondary flags: high_delay_flag_30days indicates 30 or more delay days; safety_incidents_simulated is a simulated count for descriptive monitoring, not a fitted safety classifier.")
add_par(doc, 'Quality checks are applied during generation and re-run analysis. The included CSVs are fully populated, but a real implementation should validate missingness, duplicate identifiers, impossible durations, inconsistent units, out-of-range percentages, late-entered data, and target-label quality before model fitting.', italic=True, color=MUTED, size=8.5)


doc.add_page_break()
# PAGE 5 - feature engineering
add_heading(doc, '4. Feature Engineering and Data Preparation', 1)
add_heading(doc, 'Preparation sequence', 2)
NUM_COUNTER = 0
for text in [
    'Load the raw project CSV and verify column names, expected data types, and a unique project_id for each row.',
    'Profile numeric distributions and categorical frequency counts; inspect ranges such as percentages between 0 and 100 and ratings between 1 and 5.',
    'Separate input features from outcome columns before splitting. Do not use actual_delay_days, cost_overrun_pct, cost_overrun_flag_10pct, high_delay_flag_30days, or safety_incidents_simulated as predictors for the modeled target.',
    'Split records into training and holdout sets with a fixed seed. Stratify the cost-overrun classification split to preserve the target prevalence.',
    'Fit median imputation and standard scaling for numeric fields only where the algorithm benefits from it; apply most-frequent imputation and one-hot encoding to categorical fields.',
    'Keep transformations inside scikit-learn Pipeline / ColumnTransformer objects so they are re-fitted within each cross-validation fold and not learned from the holdout set.',
]: add_num(doc, text)
add_heading(doc, 'Useful engineered features for a production version', 2)
feat_rows = [
    ('Supplier delay ratio', 'Supplier delay days / planned duration', 'Normalises procurement delay exposure across small and large projects.'),
    ('Labor shortfall', 'max(0, target labor level - availability %)', 'Makes workforce gaps easier to monitor than raw availability alone.'),
    ('Change intensity', 'Design changes per planned month or phase', 'Differentiates projects with different durations.'),
    ('Schedule buffer burn', 'Contingency consumed / original buffer', 'Flags projects whose recovery capacity is diminishing.'),
    ('Cost variance trend', 'Latest forecast-at-completion minus approved budget', 'Creates an operational leading indicator if timestamped monthly data exists.'),
    ('Rolling supplier reliability', 'On-time delivery rate over a defined trailing window', 'Measures the trend rather than a single rating snapshot.'),
]
add_table(doc, ['ENGINEERED FEATURE', 'ILLUSTRATIVE TRANSFORMATION', 'WHY IT MAY HELP'], feat_rows, widths=[1.45, 2.4, 2.65], font_size=7.7)
add_heading(doc, 'Leakage and fairness controls', 2)
add_par(doc, 'Only information available at the forecast date should be used. Post-completion measures, final cost, or outcomes derived from future project stages would leak the answer into the model. Missing values should be investigated rather than automatically imputed when they indicate a process failure. Evaluate performance by project type and scale so a seemingly good overall score does not hide weak performance for a specific group.')


doc.add_page_break()
# PAGE 6 - model approach
add_heading(doc, '5. Model Selection and Validation Design', 1)
model_rows = [
    ('Linear Regression', 'Predict delay days', 'Transparent baseline; coefficients show conditional direction and size on scaled numeric inputs.', 'Assumes an approximately linear pattern; vulnerable to nonlinear interactions and outliers.'),
    ('Random Forest Regressor', 'Predict delay days', 'Captures nonlinearities and interactions with limited manual feature engineering.', 'Less transparent, can be less stable on small samples, and does not extrapolate well beyond training ranges.'),
    ('Logistic Regression', 'Classify cost overrun >= 10%', 'Calibrated, interpretable probability baseline; standardization supports fitting.', 'Linear decision boundary; probability calibration and threshold choice still need review.'),
    ('Random Forest Classifier', 'Classify cost overrun >= 10%', 'Captures nonlinear decision patterns and interactions.', 'May miss positive cases at default threshold; feature importance is not causality.'),
]
add_table(doc, ['METHOD', 'TASK', 'SUITABILITY', 'LIMITATION'], model_rows, widths=[1.2, 1.3, 2.2, 1.8], font_size=7.4)
add_heading(doc, 'Validation protocol', 2)
val_rows = [
    ('Holdout split', '80% train / 20% test; fixed random seed; cost class stratification.', 'One final estimate on records not used for fitting.'),
    ('Cross-validation', 'Five-fold KFold for regression; five-fold StratifiedKFold for classification, within training data.', 'Shows variation across folds and helps identify unstable models.'),
    ('Regression metrics', 'MAE, RMSE, R².', 'MAE is interpretable in days; RMSE penalises larger errors; R² measures explained variance relative to a mean baseline.'),
    ('Classification metrics', 'ROC-AUC, precision, recall, F1, accuracy.', 'ROC-AUC ranks cases; recall reveals missed high-cost-risk projects; precision shows how many alerts are correct.'),
    ('Model selection', 'Compare holdout and cross-validation metrics; choose based on operational loss and risk appetite.', 'Do not select by accuracy alone or repeatedly tune against the holdout set.'),
]
add_table(doc, ['STEP', 'IMPLEMENTATION', 'INTERPRETATION'], val_rows, widths=[1.3, 3.15, 2.05], font_size=7.6)
add_heading(doc, 'Decision threshold', 2)
add_par(doc, 'The classification threshold defaults to 0.50 for demonstration. A project organisation should choose a threshold using the cost of missed overruns, review capacity, alert fatigue, and risk appetite. Where missing a high-risk project is costly, a lower threshold may be justified, followed by human review and probability calibration checks.')


doc.add_page_break()
# PAGE 7 - delay results
add_heading(doc, '6. Schedule Delay Forecasting Results', 1)
add_par(doc, f"On the 20% holdout sample, {best_reg['model']} had the strongest R² among the two tested delay models. This is consistent with the deliberately linear outcome-generation process in the synthetic dataset; it is not evidence that linear regression will outperform tree models on actual construction data.")
reg_rows = []
for _, row in reg.iterrows():
    reg_rows.append((row['model'], f"{row['test_MAE_days']:.2f}", f"{row['test_RMSE_days']:.2f}", f"{row['test_R2']:.3f}", f"{row['cv_R2_mean']:.3f} ± {row['cv_R2_std']:.3f}"))
add_table(doc, ['MODEL', 'TEST MAE (DAYS)', 'TEST RMSE (DAYS)', 'TEST R²', '5-FOLD CV R² MEAN ± SD'], reg_rows, widths=[1.75, 1.15, 1.25, 0.9, 1.45], font_size=8.0)
add_heading(doc, 'How to read the diagnostics', 2)
add_side_by_side_images(doc, [
    ('week3_01_actual_vs_predicted_delay.png', 'Figure 1. Holdout actual vs predicted delay; closeness to the diagonal indicates better point predictions.'),
    ('week3_02_delay_model_residuals.png', 'Figure 2. Residual distribution; also inspect residuals by fitted value, project scale, and project type.'),
], width=3.0)
add_par(doc, f"Selected-model holdout MAE is {best_reg['test_MAE_days']:.2f} days. MAE averages the absolute gap between prediction and outcome; it does not mean every forecast is within this number of days. The R² of {best_reg['test_R2']:.3f} indicates partial, not complete, explanation of target variation. Forecast uncertainty and project-specific review remain necessary.")


doc.add_page_break()
# PAGE 8 - classification results
add_heading(doc, '7. Cost-Overrun Risk Classification', 1)
add_par(doc, 'The classification target is a simulated cost overrun of at least 10%. It turns a cost-risk question into an early-warning problem: “Which projects should receive a deeper cost-control review?” The positive class is less frequent than the negative class, so recall and precision are more informative than accuracy alone.')
clf_rows = []
for _, row in clf.iterrows():
    clf_rows.append((row['model'], f"{row['test_accuracy']:.3f}", f"{row['test_precision']:.3f}", f"{row['test_recall']:.3f}", f"{row['test_F1']:.3f}", f"{row['test_ROC_AUC']:.3f}", f"{row['cv_ROC_AUC_mean']:.3f} ± {row['cv_ROC_AUC_std']:.3f}"))
add_table(doc, ['MODEL', 'ACC.', 'PRECISION', 'RECALL', 'F1', 'TEST ROC-AUC', '5-FOLD CV ROC-AUC'], clf_rows, widths=[1.42, 0.56, 0.77, 0.68, 0.48, 0.86, 1.25], font_size=7.3)
add_heading(doc, 'Trade-off interpretation', 2)
add_par(doc, f"{best_clf['model']} recorded test recall of {best_clf['test_recall']:.3f} and precision of {best_clf['test_precision']:.3f}. It catches a larger share of true simulated overrun cases than the random-forest classifier in this experiment, but also produces false-positive alerts. This can be a sensible screening trade-off when the consequence of missing a potentially serious overrun is higher than the cost of an extra review.")
add_side_by_side_images(doc, [
    ('week3_03_cost_overrun_model_comparison.png', 'Figure 3. Holdout ROC-AUC, F1, and recall comparison.'),
    ('week3_04_cost_overrun_confusion_matrix.png', 'Figure 4. Holdout confusion matrix for the selected classifier; positive label is 10%+ simulated overrun.'),
], width=3.0)
add_par(doc, 'Before operational use, examine probability calibration, choose a business-aligned threshold, and report results by project type and scale. A risk probability is not a guarantee of an overrun; it is a prompt to validate the assumptions, estimate-at-completion, change-control log, and procurement status.', size=8.6)


doc.add_page_break()
# PAGE 9 - scenario analysis
add_heading(doc, '8. Scenario Analysis and Expected Outcomes', 1)
add_par(doc, 'For a transparent scenario exercise, the pipeline selects one record from the upper quartile of a simple risk-screening score. The score uses procurement delays, weather disruption, design changes, project complexity, low labor availability, and ground-risk score. It is not a learned target and should be treated as a screening heuristic only.')
scenario_rows = []
base_delay = float(scenarios.iloc[0]['predicted_delay_days'])
base_prob = float(scenarios.iloc[0]['predicted_cost_overrun_probability'])
for _, row in scenarios.iterrows():
    delay_delta = float(row['predicted_delay_days']) - base_delay
    pp_delta = (float(row['predicted_cost_overrun_probability']) - base_prob) * 100
    scenario_rows.append((row['scenario'], f"{row['predicted_delay_days']:.2f}", f"{delay_delta:+.2f}", f"{float(row['predicted_cost_overrun_probability'])*100:.1f}%", f"{pp_delta:+.1f} pp"))
add_table(doc, ['SCENARIO', 'PRED. DELAY (DAYS)', 'CHANGE VS BASELINE', 'COST-RISK PROB.', 'PROB. CHANGE'], scenario_rows, widths=[2.25, 1.15, 1.15, 1.15, 1.0], font_size=7.4)
add_image(doc, 'week3_05_scenario_delay_comparison.png', width=6.2)
add_caption(doc, 'Figure 5. Predicted delay across the baseline and intervention scenarios for one simulated high-risk project.')
add_heading(doc, 'What the simulation suggests', 2)
combined = scenarios.iloc[-1]
add_bullet(doc, f"The combined-control scenario reduces the model-estimated delay by {base_delay - float(combined['predicted_delay_days']):.2f} days versus baseline for the selected record.")
add_bullet(doc, f"The estimated cost-overrun probability changes from {base_prob*100:.1f}% to {float(combined['predicted_cost_overrun_probability'])*100:.1f}% under the combined feature changes. The remaining probability is still high; the case should remain escalated for review.")
add_bullet(doc, 'A one-record scenario is illustrative, not a controlled causal estimate. A stronger analysis would simulate the full portfolio, include intervention costs and dependencies, quantify uncertainty, and validate assumptions with planners and cost controllers.')


doc.add_page_break()
# PAGE 10 - mitigation
add_heading(doc, '9. Risk Mitigation and Response Plan', 1)
mit_rows = [
    ('Schedule delay / weather', 'Use phase-level look-ahead planning; include seasonal weather windows; define recovery activities and schedule buffers.', 'Project planner + site manager', 'Schedule variance, critical-path slippage, buffer consumed'),
    ('Supplier / procurement', 'Track long-lead items early; confirm submittal approvals; maintain supplier alternatives for critical items; review delivery promises weekly.', 'Procurement lead', 'On-time delivery %, supplier delay days, overdue purchase orders'),
    ('Design changes / rework', 'Introduce design-freeze gates; track RFIs and change approvals; conduct multidisciplinary clash reviews before work release.', 'Design manager + client rep', 'Change count, open RFIs, rework and failed inspections'),
    ('Labor availability', 'Use a rolling labor forecast by trade; confirm subcontractor crew commitments; cross-train for critical tasks.', 'Construction manager', 'Labor availability %, productivity variance, overtime'),
    ('Ground/site uncertainty', 'Complete targeted surveys and geotechnical checks; document assumptions; create a contingency for unresolved site conditions.', 'Site engineer + geotechnical lead', 'Open site constraints, investigation exceptions, contingency usage'),
    ('Cost overrun', 'Update estimate-at-completion monthly; reconcile commitments, actuals and forecast; enforce change control and contingency governance.', 'Cost controller / QS', 'Cost variance, estimate-at-completion, pending change value'),
    ('Safety risk', 'Conduct task risk assessments and toolbox talks; verify permits and controls; close inspection actions; investigate near misses.', 'HSE officer + site leadership', 'Training compliance, open actions, near misses, incident trends'),
]
add_table(doc, ['RISK AREA', 'MITIGATION ACTIONS', 'OWNER', 'LEADING / LAGGING INDICATORS'], mit_rows, widths=[1.15, 2.75, 1.15, 1.55], font_size=7.25)
add_heading(doc, 'Escalation rules to define with stakeholders', 2)
add_bullet(doc, 'Set project-specific thresholds for schedule slippage, remaining contingency, overdue critical deliveries, and cost forecast variance before deployment.')
add_bullet(doc, 'Escalate a high-risk flag to a human review; record the decision, action owner, due date, and outcome in a risk log.')
add_bullet(doc, 'Safety-critical signals must activate established safety controls regardless of model confidence or cost/schedule pressure.')


doc.add_page_break()
# PAGE 11 - deployment and code
add_heading(doc, '10. Implementation Workflow and Python Strategy', 1)
add_heading(doc, 'Reproducible workflow', 2)
NUM_COUNTER = 0
for text in [
    'Generate the synthetic project records with a fixed random seed, or replace them with approved and quality-checked historical project data.',
    'Load the data, confirm schema and targets, and split predictors from outcomes to prevent leakage.',
    'Fit regression and classification pipelines on training records; use fold-based validation for model comparison.',
    'Evaluate on the untouched holdout set with regression and classification metrics and diagnostic plots.',
    'Generate project-level risk estimates and scenario outputs; map each alert to a mitigation owner and next review date.',
    'Version the dataset snapshot, feature definitions, package requirements, model metrics, and evaluation date for auditability.',
]: add_num(doc, text)
add_heading(doc, 'Representative code pattern', 2)
code = '''# Inputs are engineered and split before this step. X excludes all outcome columns.
preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

risk_model = Pipeline([
    ("prepare", preprocessor),
    ("classifier", LogisticRegression(class_weight="balanced", max_iter=2500)),
])

# Use a stratified training-fold evaluation; evaluate holdout only after model selection.
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=73)
cv_scores = cross_validate(risk_model, X_train, y_train, cv=cv,
                           scoring=["roc_auc", "recall", "precision", "f1"])
risk_model.fit(X_train, y_train)
risk_probability = risk_model.predict_proba(X_test)[:, 1]'''
p=doc.add_paragraph(); p.paragraph_format.left_indent=Inches(0.16); p.paragraph_format.right_indent=Inches(0.16)
p.paragraph_format.space_before=Pt(3); p.paragraph_format.space_after=Pt(7)
pp = p._p.get_or_add_pPr(); shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), 'F4F7FA'); pp.append(shd)
for i, line in enumerate(code.split('\n')):
    if i: p.add_run().add_break()
    r=p.add_run(line); r.font.name='Consolas'; r.font.size=Pt(7.6); r.font.color.rgb=RGBColor.from_string('263238')
add_par(doc, 'The repository contains full executable scripts in addition to this representative snippet. Run the generator first, followed by the modeling script. The script writes holdout predictions, metrics, model coefficients, scenario outputs, and plots into the data/processed and reports/figures folders.', size=8.8)
add_heading(doc, 'Operational monitoring', 2)
add_par(doc, 'Revalidate at milestone or monthly intervals. Track feature drift, missingness, forecast errors, recall of projects later confirmed as high risk, and alert workload. Refit only through a controlled versioned process with sign-off from construction, commercial, and safety stakeholders.')


doc.add_page_break()
# PAGE 12 - limitations and close
add_heading(doc, '11. Limitations, Governance, and Conclusion', 1)
add_heading(doc, 'Important limitations', 2)
for text in [
    'Synthetic data: outcomes were created by illustrative formulas and random noise. Model scores measure recovery of patterns in this simulation and may be optimistic or otherwise unlike real projects.',
    'Limited time dimension: this dataset is project-level, not monthly or weekly progress snapshots. It does not support a validated time-series or stage-specific forecast.',
    'Unobserved drivers: contract terms, inflation, design maturity, local regulations, ground investigation detail, claims, project governance, and interactions between risks are simplified or absent.',
    'Threshold dependency: 10% cost overrun and 30-day delay are example labels. Thresholds must reflect contractual and management requirements.',
    'Association is not causation: scenario outputs are model predictions after changing feature values. They do not prove that an intervention causes a particular reduction.',
    'Safety sensitivity: safety-related variables should be governed carefully. The simulation must not be used to rank actual workers, contractors, or sites or to justify reducing mandatory safety controls.',
]: add_bullet(doc, text)
add_heading(doc, 'Conclusion', 2)
add_par(doc, f"This exercise establishes a reproducible baseline for two core questions: forecasting schedule delay and prioritising projects for cost-overrun review. In the simulated experiment, linear regression led delay forecasting (holdout R² {best_reg['test_R2']:.3f}; MAE {best_reg['test_MAE_days']:.2f} days), while logistic regression offered a higher-recall cost-risk screen (holdout recall {best_clf['test_recall']:.3f}; ROC-AUC {best_clf['test_ROC_AUC']:.3f}). Combined risk controls lowered predicted delay for a selected high-risk example, but residual risk remained material.")
add_par(doc, 'The next step for a real project organisation would be to collect dated historical project data, align every input to the forecast date, agree risk thresholds with stakeholders, validate by project/time period, and establish human-reviewed response playbooks. Model metrics should support disciplined project control—not replace construction expertise, contract administration, or safety management.')
add_heading(doc, 'Project artefacts included in the repository', 2)
for text in [
    'src/generate_week3_simulated_data.py - reproducible synthetic data generator.',
    'src/risk_modeling.py - preprocessing pipelines, train/test split, cross-validation, evaluation and scenario outputs.',
    'data/raw/construction_risk_simulated.csv - 500 simulated projects.',
    'data/processed/ - metrics, model coefficients, holdout predictions and scenario outputs.',
    'reports/figures/ - diagnostic, classification and scenario visuals.',
]: add_bullet(doc, text)
add_par(doc, 'End of report.', color=TEAL, size=9.2, italic=True)

# Core properties
props = doc.core_properties
props.title = 'Predictive Analytics and Risk Modeling for Construction Projects'
props.subject = 'Construction Project Data Science Analyst Internship - Week 3'
props.author = 'Aman Yadav'
props.keywords = 'construction, predictive analytics, risk modeling, Python, regression, classification'

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(f'Created {OUT}')
