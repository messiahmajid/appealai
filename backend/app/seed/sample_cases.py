from dataclasses import dataclass


@dataclass
class SampleCase:
    id: str
    title: str
    specialty: str
    summary: str
    clinical_notes: str
    patient_name: str
    patient_dob: str
    member_id: str
    insurance_company: str
    claim_number: str
    denial_date: str
    denial_reason: str
    denied_service: str
    cpt_codes: str
    icd10_codes: str
    physician_name: str
    physician_npi: str
    practice_name: str


SAMPLE_CASES: list[SampleCase] = [
    SampleCase(
        id="sample-ortho-tka",
        title="Total Knee Arthroplasty — Failed Conservative Treatment",
        specialty="Orthopedics",
        summary="68-year-old woman with severe bilateral knee OA, Kellgren-Lawrence Grade 4, failed 8 months of conservative therapy. TKA denied for 'insufficient documentation of conservative management.'",
        clinical_notes="""OFFICE VISIT — ORTHOPEDIC SURGERY
Date: 01/15/2026
Provider: Dr. Sarah Mitchell, MD — Board Certified Orthopedic Surgeon
Practice: Advanced Orthopedic Associates
NPI: 1234567890

PATIENT: Margaret Thompson
DOB: 05/12/1957 (Age 68)
MRN: OA-2025-4481

CHIEF COMPLAINT: Severe bilateral knee pain, worse on the right, significantly limiting mobility and daily activities. Patient is here for surgical consultation after exhausting conservative measures.

HISTORY OF PRESENT ILLNESS:
Mrs. Thompson is a 68-year-old retired school teacher presenting with a 4-year history of progressive bilateral knee pain, right worse than left. Over the past 8 months, her symptoms have significantly worsened despite comprehensive conservative management. She reports constant pain rated 8/10 on the right knee and 6/10 on the left. Pain is worse with weight-bearing, stairs, and prolonged standing. She now requires a rolling walker for ambulation outside the home and reports difficulty with basic ADLs including bathing, dressing (particularly putting on shoes and socks), and toileting (difficulty sitting and rising from toilet).

She has been unable to continue her volunteer work at the local library due to inability to stand or walk for more than 10 minutes. Sleep is significantly disrupted with multiple nighttime awakenings due to pain despite medication.

CONSERVATIVE TREATMENT HISTORY:
1. Physical Therapy: Completed 24 sessions of supervised physical therapy at Valley Rehabilitation Center from 03/2025 to 06/2025 (14 weeks). Therapist notes documented only 10% improvement in function. Patient unable to tolerate advanced strengthening exercises due to pain and effusion.

2. Medications:
   - Meloxicam 15mg daily x 6 months — partial relief, discontinued due to GI symptoms
   - Acetaminophen 1000mg TID — minimal relief
   - Topical diclofenac gel — minimal relief
   - Tramadol 50mg PRN — moderate relief but causes significant drowsiness

3. Injections:
   - Right knee corticosteroid injection (triamcinolone 40mg) — 04/2025 — provided 3 weeks of partial relief
   - Right knee corticosteroid injection (triamcinolone 40mg) — 07/2025 — provided 10 days of relief
   - Right knee hyaluronic acid injection series (Synvisc-One) — 09/2025 — no significant improvement
   - Left knee corticosteroid injection (triamcinolone 40mg) — 08/2025 — 2 weeks partial relief

4. Bracing: Custom unloader brace fitted 05/2025 — unable to tolerate due to skin irritation and insufficient pain relief

5. Activity Modification: Patient has eliminated all high-impact activities, uses assistive devices, and has modified home environment with raised toilet seat and grab bars.

6. Weight Management: Patient has lost 12 pounds through dietary modification with nutritionist (BMI decreased from 31.2 to 29.8).

PAST MEDICAL HISTORY:
- Hypertension, well controlled on lisinopril 20mg daily
- Type 2 Diabetes Mellitus — HbA1c 6.8% (last checked 12/2025), on metformin 1000mg BID
- Hyperlipidemia — on atorvastatin 20mg daily
- GERD
- No prior surgeries

MEDICATIONS:
Lisinopril 20mg daily, Metformin 1000mg BID, Atorvastatin 20mg daily, Omeprazole 20mg daily, Acetaminophen 1000mg TID, Tramadol 50mg PRN

ALLERGIES: Sulfa drugs (rash)

SOCIAL HISTORY: Non-smoker x 30 years (quit 1995). No alcohol. Retired school teacher. Lives alone. No home health aide. Independent community dwelling.

PHYSICAL EXAMINATION:
Vitals: BP 128/78, HR 72, BMI 29.8

Right Knee:
- Obvious varus deformity, approximately 8 degrees
- Large effusion present
- Range of motion: 5° to 95° (severely limited; normal 0-135°)
- Crepitus throughout range of motion
- Tenderness along medial and lateral joint lines
- Positive valgus stress test with 1+ opening
- Ligaments stable to AP testing
- Patellar grind test positive
- Antalgic gait favoring right lower extremity

Left Knee:
- Mild varus deformity, approximately 4 degrees
- Small effusion
- Range of motion: 0° to 110°
- Crepitus in mid-range
- Medial joint line tenderness
- Ligaments stable

Functional Assessment:
- WOMAC Score: 72/96 (indicating severe disability)
- VAS Pain Score: 8/10 (right), 6/10 (left)
- Timed Up and Go: 28 seconds (>12 seconds = fall risk)
- 6-Minute Walk Test: 180 meters (normal >400m age-adjusted)

IMAGING:
Weight-bearing AP and lateral radiographs of bilateral knees (01/15/2026):
Right Knee:
- Kellgren-Lawrence Grade 4: Complete loss of joint space in medial compartment
- Bone-on-bone articulation medially
- Large marginal osteophytes medially and laterally
- Subchondral sclerosis and cyst formation
- 8-degree varus angulation on standing films

Left Knee:
- Kellgren-Lawrence Grade 3: Significant joint space narrowing, approximately 1.5mm remaining
- Moderate osteophyte formation
- Early subchondral sclerosis

MRI Right Knee (11/2025):
- Complete loss of articular cartilage in medial compartment
- Grade 4 chondromalacia of medial femoral condyle and medial tibial plateau
- Complex degenerative medial meniscus tear
- Moderate joint effusion
- Bone marrow edema in medial compartment

ASSESSMENT:
1. Severe primary osteoarthritis, right knee (M17.11) — Kellgren-Lawrence Grade 4 with bone-on-bone articulation, failed comprehensive conservative management
2. Moderate primary osteoarthritis, left knee (M17.12) — Kellgren-Lawrence Grade 3

PLAN:
Recommend right total knee arthroplasty (CPT 27447). Patient has exhausted all reasonable conservative treatment options over 8+ months including physical therapy, multiple medication trials, corticosteroid injections, hyaluronic acid injection, bracing, activity modification, and weight management. She has severe functional impairment with validated outcome measures confirming disability (WOMAC 72/96, TUG 28 seconds). Radiographic findings confirm end-stage disease with bone-on-bone articulation. Patient is medically optimized with controlled diabetes (A1c 6.8%), controlled hypertension, and BMI 29.8.

Patient counseled extensively regarding surgical risks, benefits, alternatives, and expectations. Patient understands and wishes to proceed. Pre-operative clearance will be obtained. Surgical date pending insurance authorization.

Signed: Dr. Sarah Mitchell, MD
Board Certified Orthopedic Surgery
NPI: 1234567890""",
        patient_name="Margaret Thompson",
        patient_dob="05/12/1957",
        member_id="UHC-887234561",
        insurance_company="UnitedHealthcare",
        claim_number="PA-2026-0115-89234",
        denial_date="01/28/2026",
        denial_reason="Insufficient documentation of conservative management. Medical records do not adequately demonstrate failure of conservative treatment modalities prior to surgical intervention. Please resubmit with complete documentation of conservative treatment attempts including dates, duration, and specific outcomes.",
        denied_service="Total Knee Arthroplasty, Right",
        cpt_codes="27447",
        icd10_codes="M17.11",
        physician_name="Dr. Sarah Mitchell, MD",
        physician_npi="1234567890",
        practice_name="Advanced Orthopedic Associates",
    ),
    SampleCase(
        id="sample-cardio-cath",
        title="Cardiac Catheterization — Abnormal Stress Test",
        specialty="Cardiology",
        summary="72-year-old man with new-onset exertional chest pain, markedly abnormal stress echo showing anterior wall ischemia. Cardiac catheterization denied as 'not medically necessary.'",
        clinical_notes="""CARDIOLOGY CONSULTATION NOTE
Date: 02/01/2026
Provider: Dr. James Chen, MD, FACC — Interventional Cardiologist
Practice: Heart & Vascular Institute of Northern Virginia
NPI: 9876543210

PATIENT: Robert Williams
DOB: 08/23/1953 (Age 72)
MRN: CV-2026-1122

REASON FOR CONSULTATION: New-onset exertional angina with markedly abnormal stress echocardiogram

HISTORY OF PRESENT ILLNESS:
Mr. Williams is a 72-year-old gentleman referred by his primary care physician Dr. Jennifer Park for evaluation of new-onset chest pain over the past 6 weeks. He describes a substernal pressure sensation that occurs with moderate exertion — specifically when walking up hills or climbing more than one flight of stairs. The chest pressure radiates to his left arm and is associated with mild dyspnea. Symptoms consistently resolve within 3-5 minutes of rest. He denies chest pain at rest, orthopnea, PND, syncope, or palpitations.

He reports the symptoms have been progressively worsening, with the onset distance decreasing from approximately 3 blocks to 1.5 blocks over the past 6 weeks. He has had to discontinue his regular daily walks with his wife due to symptoms.

CARDIAC RISK FACTORS:
- Hypertension x 20 years
- Type 2 Diabetes Mellitus x 12 years (A1c 7.2%)
- Hyperlipidemia (LDL 142 mg/dL on current statin)
- Former smoker — 30 pack-year history, quit 2010
- Family history: father died of MI at age 62, brother with CABG at age 65
- Sedentary lifestyle (limited by current chest pain)

CURRENT MEDICATIONS:
Metoprolol succinate 50mg daily, Lisinopril 20mg daily, Amlodipine 5mg daily, Metformin 1000mg BID, Atorvastatin 40mg daily, Aspirin 81mg daily

STRESS ECHOCARDIOGRAM (01/28/2026):
Protocol: Standard Bruce treadmill protocol
Exercise Duration: 5 minutes 30 seconds (Stage 2) — stopped due to chest pain and ST changes
Heart Rate: Resting 68 bpm, Peak 132 bpm (85% MPHR achieved)
Blood Pressure: Resting 138/82, Peak 168/90
ECG Findings: 2.5mm horizontal ST-segment depression in leads V2-V5 at peak exercise, resolving 6 minutes into recovery
Symptoms: Typical substernal chest pressure reproduced at 5 minutes, consistent with presenting complaint
Echocardiographic Findings:
- Resting: Normal LV systolic function, EF 55-60%, no wall motion abnormalities
- Stress: NEW hypokinesis of the anterior wall, anterior septum, and apex — consistent with LAD territory ischemia
- Estimated 3+ segments with inducible ischemia (moderate-large territory)
CONCLUSION: MARKEDLY ABNORMAL stress echocardiogram. High-risk features: early ischemia (Stage 2), large ischemic territory (LAD distribution), significant ST depression (2.5mm), and symptomatic at low workload.

RESTING ECHOCARDIOGRAM:
- LV ejection fraction 55-60%
- Normal LV dimensions
- Grade 1 diastolic dysfunction
- No significant valvular disease
- No pericardial effusion

LABORATORY:
- Troponin I: <0.01 (normal)
- BNP: 89 pg/mL (mildly elevated)
- Creatinine: 1.1 mg/dL, eGFR 68
- Total cholesterol: 228, LDL 142, HDL 38, TG 240
- HbA1c: 7.2%
- CBC: WNL

PHYSICAL EXAMINATION:
Vitals: BP 140/84 (both arms), HR 72 regular, SpO2 97% on RA
General: Alert, well-appearing gentleman in no acute distress
Cardiac: Regular rate and rhythm, no murmurs, gallops, or rubs, S4 present
Lungs: Clear to auscultation bilaterally
Extremities: No edema, pulses 2+ bilaterally
Neck: JVP 6cm, no carotid bruits

ASSESSMENT:
1. New-onset stable angina (I20.9) with markedly abnormal stress echocardiogram showing moderate-large territory anterior wall ischemia consistent with significant LAD disease
2. Multiple high-risk features on non-invasive testing: early ischemia at low workload, large ischemic territory, significant ST depression, symptomatic
3. Significant atherosclerotic cardiovascular disease risk factors: diabetes, hypertension, dyslipidemia, former smoker, strong family history

PLAN:
1. DIAGNOSTIC CARDIAC CATHETERIZATION (CPT 93458) is medically necessary and urgently indicated based on:
   - High-risk stress test results with multiple high-risk features per ACC/AHA guidelines
   - New-onset angina with objective evidence of large-territory ischemia
   - Multiple ASCVD risk factors including diabetes and family history
   - Results will directly determine treatment strategy (medical management vs. PCI vs. CABG referral)

2. Medical therapy optimization pending catheterization:
   - Increase atorvastatin to 80mg daily
   - Add isosorbide mononitrate 30mg daily
   - Add sublingual nitroglycerin PRN for acute chest pain
   - Continue aspirin
   - Continue beta-blocker

3. Patient educated on activity restrictions — avoid exertion that precipitates chest pain. Call 911 if chest pain at rest or lasting >10 minutes.

4. Risk stratification per ACC/AHA Appropriate Use Criteria: THIS IS AN APPROPRIATE INDICATION FOR CARDIAC CATHETERIZATION (Score: Appropriate — Category A7: Symptomatic, high-risk stress test findings).

Signed: Dr. James Chen, MD, FACC
Interventional Cardiology
NPI: 9876543210""",
        patient_name="Robert Williams",
        patient_dob="08/23/1953",
        member_id="ANT-443876210",
        insurance_company="Anthem Blue Cross Blue Shield",
        claim_number="PA-2026-0203-55612",
        denial_date="02/08/2026",
        denial_reason="The requested procedure is not medically necessary. Stress testing results do not meet criteria for invasive cardiac catheterization. Recommend continued medical management and repeat non-invasive testing in 3-6 months.",
        denied_service="Left Heart Catheterization with Coronary Angiography and Left Ventriculography",
        cpt_codes="93458",
        icd10_codes="I20.9, I25.10",
        physician_name="Dr. James Chen, MD, FACC",
        physician_npi="9876543210",
        practice_name="Heart & Vascular Institute of Northern Virginia",
    ),
    SampleCase(
        id="sample-onc-pet",
        title="PET/CT Staging — Newly Diagnosed Lung Cancer",
        specialty="Oncology",
        summary="61-year-old man with biopsy-confirmed Stage IIIA NSCLC. PET/CT for staging denied as 'experimental/investigational.' This is actually an NCCN Category 1 recommendation.",
        clinical_notes="""ONCOLOGY CONSULTATION NOTE
Date: 02/10/2026
Provider: Dr. Aisha Patel, MD — Medical Oncology / Hematology
Practice: Cancer Center of Greater Philadelphia
NPI: 5678901234

PATIENT: David Kowalski
DOB: 11/30/1964 (Age 61)
MRN: ONC-2026-0892

REASON FOR CONSULTATION: Newly diagnosed non-small cell lung cancer (NSCLC), adenocarcinoma, for staging workup and treatment planning

HISTORY OF PRESENT ILLNESS:
Mr. Kowalski is a 61-year-old construction supervisor who presented to his PCP 3 weeks ago with a 2-month history of persistent cough, progressive dyspnea on exertion, and 15-pound unintentional weight loss over 3 months. He also reports mild, intermittent right-sided chest discomfort and one episode of hemoptysis 1 week ago. He has been a current smoker with 40 pack-year history.

A chest X-ray (01/20/2026) revealed a 4.2cm right upper lobe mass with associated right hilar lymphadenopathy. Subsequent CT chest with contrast (01/25/2026) confirmed a 4.5 x 3.8cm spiculated mass in the right upper lobe with ipsilateral mediastinal lymphadenopathy (station 4R lymph node measuring 2.1cm, station 7 lymph node measuring 1.8cm). No pleural effusion. No obvious distant metastatic disease on CT of the chest, although the study was limited to the thorax.

CT-guided percutaneous biopsy of the RUL mass (01/30/2026):
- Histopathology: Invasive adenocarcinoma of the lung, acinar predominant
- Immunohistochemistry: TTF-1 positive, Napsin A positive, CK7 positive, CK20 negative
- Consistent with primary lung adenocarcinoma

PAST MEDICAL HISTORY:
- COPD (moderate, FEV1 62% predicted on last PFTs 2024)
- Hypertension
- Coronary artery disease — status post PCI with DES to LAD (2019)
- Type 2 Diabetes Mellitus (A1c 7.8%)
- History of DVT (2018), completed 6 months of anticoagulation

MEDICATIONS:
Tiotropium 18mcg inhaler daily, Albuterol inhaler PRN, Lisinopril 40mg daily, Metoprolol 50mg daily, Aspirin 81mg daily, Clopidogrel 75mg daily (post-PCI), Metformin 1000mg BID, Glipizide 5mg BID

SOCIAL HISTORY: Current smoker — 40 pack-years. Social alcohol use. Works as construction supervisor. Married, 2 adult children.

FAMILY HISTORY: Mother — breast cancer, age 70. Father — MI, age 58 (deceased). No family history of lung cancer.

PHYSICAL EXAMINATION:
Vitals: BP 132/78, HR 80, RR 18, SpO2 94% on RA, Weight 175 lbs (down from 190 lbs 3 months ago)
General: Well-nourished male appearing stated age, mild cachexia noted
HEENT: No cervical or supraclavicular lymphadenopathy
Lungs: Decreased breath sounds right upper field, few scattered rhonchi bilaterally
Cardiac: RRR, no murmurs
Abdomen: Soft, non-tender, no hepatomegaly
Extremities: No clubbing, cyanosis, or edema
Neuro: Alert and oriented, no focal deficits

CURRENT STAGING ASSESSMENT:
Clinical Stage: cT2b N2 M0 — Stage IIIA (pending completion of staging workup)
- T2b: Tumor >4cm but ≤5cm
- N2: Ipsilateral mediastinal lymph nodes enlarged on CT (station 4R and 7)
- M0: No distant metastases identified on CT chest (BUT staging is incomplete — CT abdomen/pelvis not yet performed, brain MRI not yet performed, PET/CT not yet performed)

ASSESSMENT AND PLAN:
Mr. Kowalski has biopsy-confirmed adenocarcinoma of the right upper lobe, clinically Stage IIIA (cT2bN2M0 pending staging completion). Per NCCN Guidelines for NSCLC (v1.2026), the following staging workup is essential for treatment planning:

1. **PET/CT WHOLE BODY (CPT 78816)** — NCCN CATEGORY 1 RECOMMENDATION
   This is the single most critical pending study. PET/CT is essential for:
   a. Accurate mediastinal staging — CT-based N staging has a 40% error rate. PET/CT has superior sensitivity and specificity for mediastinal nodal involvement.
   b. Detection of occult distant metastases — up to 20% of patients with clinical Stage III NSCLC are found to have distant metastases on PET/CT that were not apparent on conventional CT.
   c. Treatment decision: If PET/CT confirms N2 disease without distant metastases → patient may be a candidate for concurrent chemoradiation ± consolidation immunotherapy. If PET/CT shows distant metastases → patient has Stage IV disease and systemic therapy is indicated instead.
   d. PET/CT findings will determine whether this patient needs mediastinal tissue confirmation (EBUS) vs. proceeding directly to treatment.
   WITHOUT PET/CT, WE CANNOT APPROPRIATELY SELECT BETWEEN CURATIVE AND PALLIATIVE TREATMENT INTENT.

2. Brain MRI with contrast — to rule out brain metastases (NCCN Category 2A for Stage IIB+)

3. Molecular testing (already sent):
   - EGFR, ALK, ROS1, BRAF, PD-L1 IHC, comprehensive NGS panel
   - Results pending, expected in 10-14 business days

4. Pulmonary function testing — pre-treatment baseline, particularly important given COPD history

5. Cardiology clearance — given history of CAD and PCI

6. Smoking cessation counseling provided — patient is motivated to quit, referred to cessation program

7. Multidisciplinary tumor board presentation — scheduled for 02/20/2026, pending completion of staging workup

CLINICAL URGENCY:
This patient has a newly diagnosed lung cancer that requires expedient staging for treatment planning. Delay in staging directly impacts the window for potentially curative therapy. NCCN guidelines recommend initiating treatment within 6-8 weeks of diagnosis for optimal outcomes. Every week of delay in completing the staging workup delays treatment initiation.

Signed: Dr. Aisha Patel, MD
Medical Oncology / Hematology
NPI: 5678901234""",
        patient_name="David Kowalski",
        patient_dob="11/30/1964",
        member_id="AET-776543890",
        insurance_company="Aetna",
        claim_number="PA-2026-0212-33478",
        denial_date="02/15/2026",
        denial_reason="The requested PET/CT scan is considered experimental/investigational for this indication. Clinical evidence does not support the use of PET imaging for this diagnosis. Standard CT imaging is sufficient for staging purposes.",
        denied_service="PET/CT Whole Body for Tumor Staging",
        cpt_codes="78816",
        icd10_codes="C34.11, R91.1",
        physician_name="Dr. Aisha Patel, MD",
        physician_npi="5678901234",
        practice_name="Cancer Center of Greater Philadelphia",
    ),
]
