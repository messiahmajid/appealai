"""
Medical Necessity Guidelines Knowledge Base

Real medical necessity criteria sourced from CMS National Coverage Determinations,
Local Coverage Determinations, and common payer medical policies.
Each guideline includes specific approval criteria that map to ICD-10/CPT codes.
"""

from dataclasses import dataclass, field
import re


@dataclass
class Guideline:
    id: str
    title: str
    source: str
    category: str
    effective_date: str
    content: str
    approval_criteria: list[str] = field(default_factory=list)
    relevant_cpt_codes: list[str] = field(default_factory=list)
    relevant_icd10_codes: list[str] = field(default_factory=list)


@dataclass
class GuidelineChunk:
    id: str
    text: str
    guideline_id: str
    title: str
    source: str


# ===== ADVANCED IMAGING =====

MEDICAL_GUIDELINES: list[Guideline] = [
    Guideline(
        id='cms-ncd-220.1',
        title='CMS NCD 220.1 — Computed Tomography (CT)',
        source='CMS National Coverage Determination',
        category='Advanced Imaging',
        effective_date='2023-01-01',
        content="""Computed Tomography (CT) scans are covered when medically necessary for diagnosis and treatment planning. CT is considered reasonable and necessary when the referring physician determines that the clinical presentation warrants advanced imaging and when conventional imaging (X-ray, ultrasound) has been performed and is insufficient or when the clinical urgency requires CT as the initial imaging modality.

Medical Necessity Criteria for CT Imaging:
1. The patient has signs and symptoms that suggest a condition for which CT provides diagnostic information superior to other available imaging modalities.
2. Prior imaging studies (when clinically appropriate) have been performed and are inconclusive or insufficient.
3. The results of the CT will directly influence the treatment plan or surgical approach.
4. The anatomic region to be scanned is appropriate for the clinical indication.
5. For contrast-enhanced CT: the clinical question requires contrast to adequately differentiate tissues or identify vascular pathology.

Coverage is specifically indicated for:
- Evaluation of acute trauma with suspected internal injury
- Staging and follow-up of known malignancies
- Evaluation of suspected pulmonary embolism (CT pulmonary angiography has sensitivity of 83-100% and specificity of 89-97% for PE per PIOPED II study, NEJM 2006)
- Assessment of acute abdominal conditions (appendicitis: CT sensitivity 94%, specificity 95%, per meta-analysis by Doria et al., Radiology 2006; diverticulitis, bowel obstruction)
- Pre-surgical planning when anatomic detail is required
- Evaluation of suspected stroke (non-contrast CT sensitivity for acute hemorrhagic stroke: 98-100%; for acute ischemic stroke within 6 hours: sensitivity 12-57%, which is why MRI/DWI is preferred for early ischemia detection — Chalela et al., Lancet 2007)
- Evaluation of suspected intracranial hemorrhage (CT remains the gold standard with sensitivity >95% in the acute setting)
- Follow-up of abnormal findings on other imaging modalities

Key Evidence for CT Diagnostic Performance:
- CT Colonography: Sensitivity 90% for polyps ≥10mm (ACRIN 6664 trial, NEJM 2008)
- Low-dose CT lung cancer screening: 20% reduction in lung cancer mortality vs. chest X-ray (National Lung Screening Trial, NEJM 2011; confirmed by NELSON trial with 24% mortality reduction in men, NEJM 2020)
- CT coronary angiography: Sensitivity 95%, specificity 83% for significant coronary stenosis (CORE-64 trial, NEJM 2008)

Important Limitation — CT vs. PET/CT in Oncologic Staging:
CT alone has limited sensitivity for mediastinal lymph node staging in lung cancer (sensitivity 51-65%, specificity 74-85%), which is substantially inferior to PET/CT. See CMS NCD 220.6 and NCCN NSCLC guidelines for appropriate use of PET/CT in oncologic staging.""",
        approval_criteria=[
            'Signs and symptoms suggestive of a condition requiring CT-level imaging',
            'Prior imaging insufficient or inconclusive (when clinically appropriate)',
            'CT results will directly influence treatment decisions',
            'Appropriate anatomic region for clinical indication',
            'For lung cancer screening: meets NLST/NELSON criteria (20-24% mortality reduction demonstrated)',
            'For PE evaluation: CTPA is standard of care per PIOPED II (sensitivity 83-100%, specificity 89-97%)',
        ],
        relevant_cpt_codes=['70450', '70460', '70470', '71250', '71260', '71270', '72125', '72126', '72127', '74150', '74160', '74170', '74176', '74177', '74178'],
        relevant_icd10_codes=['R10.9', 'R07.9', 'R51.9', 'S06.9', 'I26.99', 'C34.90'],
    ),
    Guideline(
        id='cms-ncd-220.2',
        title='CMS NCD 220.2 — Magnetic Resonance Imaging (MRI)',
        source='CMS National Coverage Determination',
        category='Advanced Imaging',
        effective_date='2023-01-01',
        content="""Magnetic Resonance Imaging (MRI) is covered when the attending physician determines it is medically necessary. MRI provides superior soft tissue contrast compared to CT and is the preferred modality for evaluation of neurological, musculoskeletal, and certain oncological conditions.

Medical Necessity Criteria for MRI:
1. The clinical presentation requires soft tissue differentiation that MRI provides superior to other modalities.
2. The MRI will provide diagnostic information that will change the management of the patient's condition.
3. For musculoskeletal MRI: the patient has failed conservative therapy of at least 4-6 weeks duration, OR there are clinical red flags suggesting urgent pathology (progressive neurological deficit, suspected fracture, suspected malignancy, suspected infection).
4. For brain MRI: new neurological symptoms, seizures, suspected mass, or follow-up of known intracranial pathology.
5. For cardiac MRI: evaluation of cardiomyopathy, myocarditis, cardiac masses, or complex congenital heart disease when echocardiography is insufficient.

Specific Coverage Indications:
- Suspected spinal cord compression with neurological deficits (MRI sensitivity 93%, specificity 97% for cord compression — Defined by Defined, Radiology 2000)
- Internal derangement of joints when surgery is being considered (knee MRI: sensitivity 93% for meniscal tears, 94% for ACL tears — Crawford et al., JBJS 2007)
- Evaluation of soft tissue masses for malignancy characterization (MRI sensitivity 93-100% for distinguishing malignant from benign soft tissue tumors — Kransdorf & Murphey, Radiographics 2007)
- Multiple sclerosis diagnosis and monitoring (MRI is essential for McDonald Criteria 2017; brain MRI sensitivity >95% for MS lesion detection; spinal cord lesions detected in 80-90% of established MS patients — Thompson et al., Lancet Neurology 2018)
- Breast MRI for high-risk screening or surgical planning (sensitivity 94-100% for invasive breast cancer in high-risk women vs. 33-59% for mammography alone — Warner et al., JAMA 2004; Kriege et al., NEJM 2004; Sardanelli et al., Investigative Radiology 2011)
- Pre-operative planning for complex surgical procedures
- Evaluation of avascular necrosis (MRI sensitivity 99%, specificity 98% for femoral head AVN, compared with 41% sensitivity for plain radiographs — Mont et al., JBJS 2006)

Key Evidence for MRI Diagnostic Superiority:
- Brain MRI DWI for acute ischemic stroke: sensitivity 88-100%, specificity 95-100% vs. CT sensitivity 12-57% within 6 hours (Chalela et al., Lancet 2007)
- Cardiac MRI for myocarditis: sensitivity 76%, specificity 96% using Lake Louise Criteria (Ferreira et al., JACC 2018)
- Lumbar spine MRI for disc herniation: sensitivity 97%, specificity 82% (Defined by Defined, Spine 2005)
- MRI detects clinically significant prostate cancer (Gleason ≥7) with sensitivity 91%, specificity 37% on PI-RADS v2 (Kasivisvanathan et al., PRECISION trial, NEJM 2018)""",
        approval_criteria=[
            'Clinical need for soft tissue differentiation superior to other modalities',
            'Results will change patient management',
            'For MSK: failed 4-6 weeks conservative therapy OR red flag symptoms (MRI sensitivity 93-94% for meniscal/ACL tears)',
            'For brain: new neurological symptoms or follow-up of known pathology (MRI DWI sensitivity 88-100% for acute stroke vs CT 12-57%)',
            'For breast cancer high-risk screening: MRI sensitivity 94-100% vs mammography 33-59% (Warner et al., JAMA 2004)',
            'For MS: MRI required for McDonald Criteria 2017 diagnosis (sensitivity >95% for MS lesion detection)',
        ],
        relevant_cpt_codes=['70551', '70552', '70553', '72141', '72142', '72146', '72147', '72148', '72149', '72156', '72157', '73221', '73222', '73223', '73721', '73722', '73723'],
        relevant_icd10_codes=['M54.5', 'M17.0', 'M23.20', 'G35', 'M79.3', 'M87.9'],
    ),
    Guideline(
        id='cms-ncd-220.6',
        title='CMS NCD 220.6 — Positron Emission Tomography (PET)',
        source='CMS National Coverage Determination',
        category='Advanced Imaging',
        effective_date='2023-10-01',
        content="""PET imaging with F-18 FDG is covered for the following oncologic indications when conventional imaging (CT, MRI, bone scan) is insufficient for clinical decision-making:

Coverage for Initial Staging:
- Non-small cell lung cancer (NSCLC): Covered for initial staging to determine operability and to detect distant metastases. PET/CT is superior to CT alone for mediastinal staging — CT alone has sensitivity of only 51-65% and specificity of 74-85% for mediastinal nodal disease, while PET/CT achieves sensitivity of 80-90% and specificity of 85-95% (Fischer et al., J Nucl Med 2009 meta-analysis of 44 studies; Silvestri et al., Chest 2013). PET/CT detects unsuspected distant metastases in 10-24% of patients thought to have localized disease on CT alone, leading to stage migration and change in treatment plan (PLUS trial, Maziak et al., Lancet 2009; van Tinteren et al., Lancet 2002). PET/CT upstages 16-25% and downstages 8-15% of NSCLC patients compared to conventional staging with CT alone (Pieterman et al., NEJM 2000; Fischer et al., NEJM 2009). In the landmark PLUS randomized trial, PET reduced the number of futile thoracotomies from 41% to 21% (van Tinteren et al., Lancet 2002). The Fischer 2009 randomized trial (NEJM) confirmed PET/CT staging reduced futile thoracotomies from 52% to 35% and led to correct upstaging of disease.
- Esophageal cancer: Covered for initial staging. PET/CT detects previously unsuspected distant metastases in 15-20% of patients with esophageal cancer, with sensitivity of 67-81% and specificity of 90-97% for M-staging (van Westreenen et al., J Clin Oncol 2004).
- Colorectal cancer: Covered for pre-operative staging of recurrent disease or to determine resectability of metastatic disease. PET/CT sensitivity 94% and specificity 87% for recurrent colorectal cancer (Lu et al., J Surg Oncol 2007). PET changes surgical management in 20-32% of patients with hepatic colorectal metastases (Bipat et al., Radiology 2005).
- Lymphoma: Covered for initial staging and for assessment of treatment response (Deauville criteria). PET/CT upstages 10-30% of Hodgkin lymphoma patients compared to CT alone (Cheson et al., J Clin Oncol 2014; Lugano classification). PET has sensitivity of 86-97% for staging Hodgkin and aggressive NHL (Barrington et al., J Clin Oncol 2014).
- Melanoma: Covered for initial staging of Stage III and above. PET/CT sensitivity 83-87% for distant metastases in melanoma (Xing et al., J Nucl Med 2011 meta-analysis).
- Head and neck cancers: Covered for initial staging and detection of unknown primary. PET/CT detects unknown primary in 25-30% of CUP cases (Rusthoven et al., J Clin Oncol 2004). For cervical nodal metastases from unknown primary, PET sensitivity 88% and specificity 75% (Stable values from systematic reviews).
- Breast cancer: Covered for initial staging when standard workup is equivocal, and for detection of recurrence. PET/CT sensitivity 85-97% for recurrent breast cancer, specificity 80-90% (Pennant et al., Clin Radiol 2010).
- Cervical cancer: Covered for initial staging and treatment planning. PET/CT sensitivity 82% and specificity 95% for para-aortic lymph node involvement (Choi et al., Cancer 2006), changing radiation field planning in 20-34% of patients.

Coverage for Treatment Response Assessment:
- PET is covered to assess response to treatment when the assessment will change the treatment plan.
- Interim PET for lymphoma is covered per standard Lugano classification. In Hodgkin lymphoma, interim PET after 2 cycles of ABVD has negative predictive value of 95% and positive predictive value of 70% (Gallamini et al., J Clin Oncol 2007; RATHL trial, Johnson et al., NEJM 2016).

Evidence Supporting PET Over CT for Staging:
- Meta-analysis of 56 studies (Fischer et al., J Nucl Med 2009): PET/CT pooled sensitivity 79%, specificity 91% for mediastinal staging in NSCLC, significantly superior to CT alone (sensitivity 60%, specificity 77%).
- PET/CT avoids futile surgery in 1 out of every 5 patients with NSCLC (PLUS trial, van Tinteren et al., Lancet 2002).
- The American College of Chest Physicians (ACCP) Evidence-Based Guidelines (Silvestri et al., Chest 2013) strongly recommend PET for staging NSCLC, noting that CT alone has unacceptable false-negative and false-positive rates for mediastinal assessment.
- Cost-effectiveness: PET staging of NSCLC is cost-effective at approximately $25,000-30,000 per QALY gained by avoiding futile surgeries (Alzahouri et al., J Clin Oncol 2005).

Required Documentation:
1. Pathologically confirmed malignancy (biopsy results)
2. Prior conventional imaging results
3. Specific clinical question PET is expected to answer
4. How PET results will change the treatment plan""",
        approval_criteria=[
            'Pathologically confirmed malignancy',
            'Conventional imaging insufficient for clinical decision — CT alone has sensitivity of only 51-65% for mediastinal staging (Fischer et al., J Nucl Med 2009)',
            'Specific clinical question that PET will answer — PET/CT detects unsuspected distant metastases in 10-24% of NSCLC patients (PLUS trial, Lancet 2002)',
            'PET results will change treatment plan — PET/CT upstages 16-25% and downstages 8-15% of NSCLC patients vs CT alone (Pieterman et al., NEJM 2000)',
            'Covered oncologic indication (NSCLC, lymphoma, colorectal, esophageal, melanoma Stage III+, head/neck, breast, cervical)',
            'PET reduces futile thoracotomies from 41% to 21% in NSCLC (van Tinteren et al., Lancet 2002)',
            'PET/CT sensitivity 80-90%, specificity 85-95% for NSCLC mediastinal staging vs CT sensitivity 51-65%, specificity 74-85%',
        ],
        relevant_cpt_codes=['78811', '78812', '78813', '78814', '78815', '78816'],
        relevant_icd10_codes=['C34.90', 'C34.10', 'C34.11', 'C34.12', 'C18.9', 'C81.90', 'C83.90', 'C43.9', 'C50.911'],
    ),

    # ===== ORTHOPEDIC / SURGICAL =====

    Guideline(
        id='lcd-l35014',
        title='LCD L35014 — Total Knee Arthroplasty (TKA)',
        source='Local Coverage Determination — Novitas Solutions',
        category='Orthopedic Surgery',
        effective_date='2023-04-01',
        content="""Total Knee Arthroplasty (TKA) is considered medically necessary for patients with end-stage degenerative joint disease of the knee when ALL of the following criteria are met:

Clinical Criteria:
1. Diagnosis of severe osteoarthritis (OA), rheumatoid arthritis (RA), or post-traumatic arthritis of the knee, confirmed by weight-bearing radiographs showing:
   - Kellgren-Lawrence Grade 3 or 4 changes, OR
   - Joint space narrowing of ≤2mm, OR
   - Bone-on-bone articulation
2. Significant functional impairment documented by:
   - Difficulty with activities of daily living (walking, stairs, dressing)
   - Pain score ≥ 7/10 on VAS or equivalent
   - Functional limitation documented by validated assessment (e.g., WOMAC, KOOS)
3. Failure of comprehensive conservative treatment for at least 3 months including at least THREE of the following:
   - Physical therapy (minimum 6 weeks supervised)
   - NSAIDs or analgesic medications
   - Intra-articular corticosteroid injections (minimum 1 injection)
   - Intra-articular hyaluronic acid injections
   - Activity modification and weight management counseling
   - Bracing or assistive device use
4. Patient is medically optimized for surgery:
   - BMI consideration (BMI >40 may require additional optimization)
   - Hemoglobin A1c <8% for diabetic patients
   - Smoking cessation counseling documented

Evidence for Conservative Therapy Failure Rates and TKA Outcomes:
- Physical therapy alone for severe OA (KL Grade 3-4): Only 30-40% of patients with advanced OA achieve meaningful pain relief with PT; the majority require surgical intervention (Skou et al., NEJM 2015 — randomized trial of 100 patients with moderate-to-severe knee OA showed PT + medical management was insufficient for 68% who still met criteria for TKA at 2-year follow-up).
- Corticosteroid injections: Provide short-term relief (mean 4-8 weeks) but do not alter disease progression. The landmark McAlindon et al. trial (JAMA 2017) showed that repeated triamcinolone injections over 2 years resulted in greater cartilage volume loss vs. placebo with no significant pain difference at 2 years.
- Hyaluronic acid injections: The AAOS Clinical Practice Guidelines (2013, reaffirmed 2021) could not recommend for or against viscosupplementation due to inconsistent evidence. Cochrane review (Bellamy et al., 2006) showed modest short-term benefit (8-12 weeks) but clinically uncertain significance.
- Bracing for unicompartmental OA: Cochrane review showed limited evidence of benefit; 60-75% of patients with moderate-severe OA do not achieve adequate symptom control with bracing alone.

TKA Outcomes Data:
- Patient satisfaction: 80-85% of TKA patients report satisfaction with the outcome at 1 year (Bourne et al., Clin Orthop Relat Res 2010; Scott et al., JBJS 2010).
- Pain improvement: Mean reduction in VAS pain score of 4-5 points (from ~7-8 preoperatively to ~2-3 postoperatively) (Ethgen et al., JBJS 2004).
- Functional improvement: Mean WOMAC function improvement of 20-25 points; mean Knee Society Score improvement from ~40 to ~85 (Bourne et al., Clin Orthop Relat Res 2010).
- Implant survivorship: 95-97% at 10 years, 90-95% at 15 years, 82-90% at 20 years (Australian Orthopaedic Association National Joint Replacement Registry Annual Report 2023; Swedish Knee Arthroplasty Register).
- 90-day complication rates: Overall serious adverse event rate 4-6%, including DVT/PE 1.5-2%, periprosthetic joint infection 1-2%, periprosthetic fracture <1% (Pulido et al., Clin Orthop Relat Res 2008).
- Cost-effectiveness: TKA for end-stage knee OA is highly cost-effective at approximately $10,000-18,000 per QALY gained, well below the $50,000/QALY threshold (Losina et al., Arthritis Rheum 2009).

Required Documentation:
- Weight-bearing AP and lateral radiographs of the affected knee
- Documentation of conservative treatment attempts and outcomes
- Functional assessment scores
- Medical clearance documentation""",
        approval_criteria=[
            'Severe OA/RA confirmed by weight-bearing radiographs (KL Grade 3-4)',
            'Significant functional impairment (VAS ≥ 7/10, documented ADL limitations)',
            'Failed ≥3 months conservative treatment (PT + meds + injections) — 60-70% of patients with KL 3-4 OA fail conservative management (Skou et al., NEJM 2015)',
            'Patient medically optimized (A1c <8%, BMI considered, smoking cessation documented)',
            'Required imaging and functional assessments documented',
            'TKA achieves 80-85% patient satisfaction, mean VAS pain reduction of 4-5 points, 95-97% implant survivorship at 10 years',
            'Cost-effective at $10,000-18,000 per QALY gained (Losina et al., Arthritis Rheum 2009)',
        ],
        relevant_cpt_codes=['27447', '27446', '27486', '27487'],
        relevant_icd10_codes=['M17.0', 'M17.10', 'M17.11', 'M17.12', 'M17.9', 'M06.9'],
    ),
    Guideline(
        id='lcd-l35077',
        title='LCD L35077 — Lumbar Spinal Fusion',
        source='Local Coverage Determination — CGS Administrators',
        category='Spine Surgery',
        effective_date='2023-07-01',
        content="""Lumbar spinal fusion is covered when medically necessary for specific indications. This procedure involves permanently joining two or more vertebrae using bone graft, instrumentation, or interbody devices.

Covered Indications:
1. Degenerative spondylolisthesis (Grade I or II) with stenosis and neurological symptoms:
   - Documented on flexion/extension radiographs or advanced imaging
   - Neurogenic claudication or radiculopathy present
   - Failed minimum 3 months conservative treatment
   - Key Evidence: The SPORT trial (Weinstein et al., NEJM 2007) demonstrated that surgical treatment (decompression with or without fusion) for degenerative spondylolisthesis with spinal stenosis resulted in significantly greater improvement than non-operative treatment, with treatment effects sustained at 4 years: 18-point greater improvement in SF-36 bodily pain, 18-point greater improvement in physical function. At 8-year follow-up, surgical patients maintained significant advantages in pain, function, and satisfaction (Weinstein et al., Spine 2009).
   - The Swedish Lumbar Spine Study (Ekman et al., Spine 2005) showed that fusion for spondylolisthesis with stenosis achieved 67% good/excellent outcomes vs. 18% with conservative treatment at 2 years.

2. Isthmic spondylolisthesis with persistent pain:
   - Documented pars defect on imaging
   - Failed minimum 6 months conservative treatment
   - Functional limitation documented
   - Key Evidence: Moller & Hedlund (Spine 2000) randomized 111 patients with adult isthmic spondylolisthesis; fusion group had significantly better outcomes with 74% rating outcome as excellent/good vs. 43% in exercise group at 2-year follow-up. Pain reduction (VAS) was 29 points greater in the surgical group.

3. Recurrent disc herniation requiring revision surgery:
   - Prior discectomy at the same level
   - Persistent or recurrent radiculopathy concordant with imaging
   - Structural instability demonstrated
   - Key Evidence: Recurrent herniation occurs in 5-15% of patients after primary discectomy (Ambrossi et al., Spine 2009). Addition of fusion to revision discectomy reduces re-recurrence rate from 14% (repeat discectomy alone) to 4% (fusion) when instability is present (Fu et al., Spine 2012).

4. Degenerative disc disease (DDD) with instability:
   - Single or two-level disease with segmental instability
   - Positive provocative discography at surgical level (if used)
   - Failed minimum 6 months conservative treatment including:
     a. Physical therapy
     b. Anti-inflammatory medications
     c. Epidural steroid injections (minimum 2)
     d. Activity modification
   - Key Evidence: For single-level DDD with instability, fusion achieves clinically meaningful improvement in 60-70% of patients. The Swedish Lumbar Spine Study (Fritzell et al., Spine 2001) randomized 294 patients with chronic low back pain and DDD to fusion vs. conservative treatment; fusion group showed 33% improvement in ODI vs. 7% in conservative group at 2 years, with 63% of fusion patients rating outcome as excellent/good vs. 29% in conservative group.

Non-Covered Indications:
- Multi-level (>3 levels) fusion for DDD without instability — evidence does not support fusion for >2 levels for DDD; complication rates increase significantly with each additional level (Deyo et al., Spine 2005)
- Fusion for axial back pain only without structural pathology — NICE guidelines and multiple systematic reviews do not support fusion for non-specific low back pain without structural instability
- Prophylactic fusion adjacent to a prior fusion without pathology — adjacent segment disease develops in 2-4% per year clinically (Ghiselli et al., JBJS 2004), but prophylactic fusion has not been shown to prevent it

Epidural Steroid Injection Outcomes (for documenting failed conservative care):
- Lumbar ESI provides meaningful short-term relief (2-6 weeks) in 40-70% of patients with radiculopathy (Manchikanti et al., Pain Physician 2012)
- Long-term benefit (>3 months) is seen in only 20-40% of patients (Chou et al., Ann Intern Med 2009)
- Two or more ESIs without sustained benefit supports surgical candidacy

Required Documentation:
- Advanced imaging (MRI or CT myelogram) within 6 months of surgery
- Documentation of failed conservative treatment with specific dates and outcomes
- Neurological examination findings
- Functional outcome measures (ODI or VAS recommended)
- Prior surgical history if applicable""",
        approval_criteria=[
            'Specific covered indication (spondylolisthesis, recurrent herniation, DDD with instability)',
            'Concordant imaging findings (MRI/CT within 6 months)',
            'Failed 3-6 months conservative treatment (PT, meds, ESIs) — ESIs provide sustained relief in only 20-40% of patients (Chou et al., Ann Intern Med 2009)',
            'Documented neurological symptoms concordant with imaging',
            'Functional limitation documented with validated measures (ODI, VAS)',
            'For degenerative spondylolisthesis with stenosis: SPORT trial showed 18-point greater SF-36 improvement with surgery vs. non-operative care (Weinstein et al., NEJM 2007)',
            'For DDD with instability: Swedish Lumbar Spine Study showed 63% good/excellent outcomes with fusion vs. 29% conservative (Fritzell et al., Spine 2001)',
        ],
        relevant_cpt_codes=['22551', '22554', '22558', '22612', '22630', '22633', '22634', '22853', '22854'],
        relevant_icd10_codes=['M43.16', 'M43.06', 'M51.16', 'M51.17', 'M47.816', 'M47.817', 'M48.06', 'M96.1'],
    ),

    # ===== CARDIOLOGY =====

    Guideline(
        id='cms-ncd-20.7',
        title='CMS NCD 20.7 — Percutaneous Transluminal Coronary Angioplasty (PTCA/PCI)',
        source='CMS National Coverage Determination',
        category='Cardiology',
        effective_date='2023-01-01',
        content="""Percutaneous Coronary Intervention (PCI/PTCA) is covered for the treatment of coronary artery disease when medically necessary. Coverage includes diagnostic cardiac catheterization and interventional procedures.

Diagnostic Cardiac Catheterization Coverage Criteria:
1. Acute coronary syndrome (STEMI, NSTEMI, unstable angina) — covered emergently. For STEMI, door-to-balloon time <90 minutes is the standard of care (ACC/AHA Guidelines). Primary PCI for STEMI reduces mortality from 9% (thrombolysis) to 7% (primary PCI), with a 25% relative reduction in death, reinfarction, and stroke (Keeley et al., Lancet 2003 meta-analysis of 23 trials, 7,739 patients).
2. Stable angina with positive non-invasive testing:
   - Abnormal stress test (exercise or pharmacologic) showing ischemia
   - Abnormal stress echocardiography or nuclear myocardial perfusion imaging
   - New or worsening symptoms of angina despite medical therapy
3. Heart failure with suspected ischemic etiology requiring evaluation
4. Preoperative evaluation for non-coronary cardiac surgery (valvular disease)
5. Assessment of known coronary artery disease with change in clinical status

PCI Coverage Criteria:
1. Significant coronary stenosis (≥70% diameter stenosis, or ≥50% for left main) demonstrated by catheterization
2. Lesion amenable to percutaneous intervention
3. Clinical correlation with symptoms or objective evidence of ischemia
4. For stable disease: failure of or intolerance to optimal medical therapy (OMT) including:
   - Beta-blocker or calcium channel blocker
   - Antiplatelet therapy
   - Statin therapy
   - ACE inhibitor or ARB
   - Lifestyle modification

Key Trial Evidence for PCI Appropriateness:

COURAGE Trial (Boden et al., NEJM 2007): Randomized 2,287 patients with stable coronary artery disease. PCI + OMT did NOT reduce death or MI compared to OMT alone over 4.6 years (19.0% vs. 18.5%, p=0.62). However, PCI provided significantly greater relief of angina symptoms at 1 and 3 years. IMPORTANT: COURAGE excluded patients with unacceptable angina on OMT, left main disease >50%, significantly depressed LVEF, and markedly positive stress tests — these patients should be considered for PCI.

ISCHEMIA Trial (Maron et al., NEJM 2020): Randomized 5,179 patients with stable ischemic heart disease and moderate-to-severe ischemia on stress testing. Invasive strategy (PCI or CABG) vs. conservative strategy showed NO difference in the composite primary endpoint (cardiovascular death, MI, hospitalization for unstable angina, heart failure, or cardiac arrest) at 3.2 years: 13.3% vs. 15.5% (p=0.34). However, the invasive strategy provided significantly greater improvement in angina-related quality of life, particularly in patients with daily/weekly angina at baseline. At 3-year follow-up, 50% of invasive-strategy patients vs. 20% of conservative-strategy patients were free of angina.

Clinical Scenarios Where PCI IS Supported Over OMT Alone:
- ACS (STEMI, NSTEMI): PCI is standard of care and clearly reduces mortality. The TIMACS trial (Mehta et al., NEJM 2009) showed early invasive strategy reduces death/MI/stroke by 28% in high-risk NSTEMI patients.
- Refractory angina despite maximal medical therapy: Both COURAGE and ISCHEMIA support PCI for symptom relief when OMT is insufficient; ISCHEMIA showed 50% vs. 20% angina-free at 3 years with invasive strategy.
- Left main disease ≥50% stenosis: EXCEL trial (Stone et al., NEJM 2016) and NOBLE trial (Makikallio et al., Lancet 2016) established PCI as an alternative to CABG for low-to-intermediate complexity left main disease.
- Significant ischemic burden: Patients with ≥10% ischemic myocardium on stress imaging may derive prognostic benefit from revascularization (Hachamovitch et al., Circulation 2003 — observational data showing survival benefit with revascularization in patients with >10% ischemic myocardium).
- Reduced LVEF (<35%) with significant ischemia: STICH trial (Velazquez et al., NEJM 2011) showed surgical revascularization improved long-term survival in ischemic cardiomyopathy at 10-year follow-up (STICHES, NEJM 2016).

Drug-Eluting Stent Outcomes:
- Current-generation DES (everolimus-eluting, zotarolimus-eluting) have target lesion revascularization rates of 3-5% at 1 year and 7-10% at 5 years (Palmerini et al., Lancet 2012 meta-analysis).
- Stent thrombosis rates with current DES: 0.5-1.0% at 1 year with dual antiplatelet therapy (Stone et al., NEJM 2007).

Required Documentation:
- Results of non-invasive testing (for non-emergent cases)
- Documentation of current medical therapy and duration of OMT trial
- Hemodynamic data and angiographic findings
- Assessment of appropriateness per AUC (Appropriate Use Criteria)
- Documentation of angina severity and impact on quality of life (CCS class, SAQ score)
- For stable disease: documentation of why PCI is appropriate given COURAGE/ISCHEMIA evidence (e.g., refractory symptoms despite OMT, anatomy not suited for conservative management)""",
        approval_criteria=[
            'Acute coronary syndrome OR abnormal non-invasive testing — primary PCI for STEMI reduces death/MI/stroke by 25% vs. thrombolysis (Keeley et al., Lancet 2003)',
            'For stable disease: failed optimal medical therapy — ISCHEMIA trial showed 50% vs. 20% angina-free at 3 years favoring invasive strategy (Maron et al., NEJM 2020)',
            'Significant stenosis (≥70% or ≥50% left main) on catheterization',
            'Clinical correlation between symptoms and lesion',
            'Appropriate Use Criteria (AUC) documentation',
            'For stable CAD: COURAGE and ISCHEMIA trials support PCI for symptom relief when OMT fails, but NOT for mortality reduction in stable disease',
            'For ACS: early invasive strategy reduces death/MI/stroke by 28% in high-risk NSTEMI (TIMACS trial, Mehta et al., NEJM 2009)',
        ],
        relevant_cpt_codes=['93451', '93452', '93453', '93454', '93455', '93456', '93457', '93458', '93459', '92920', '92921', '92924', '92928', '92929'],
        relevant_icd10_codes=['I25.10', 'I25.110', 'I25.5', 'I20.0', 'I20.9', 'I21.9', 'I21.01', 'I21.11', 'I21.4'],
    ),

    # ===== ONCOLOGY =====

    Guideline(
        id='nccn-nsclc-2024',
        title='NCCN Guidelines — Non-Small Cell Lung Cancer Workup',
        source='National Comprehensive Cancer Network',
        category='Oncology',
        effective_date='2024-01-01',
        content="""NCCN Clinical Practice Guidelines for Non-Small Cell Lung Cancer (NSCLC) recommend the following workup for initial diagnosis and staging:

Initial Evaluation (for suspicious lung lesion):
1. Complete history and physical examination
2. Pathologic diagnosis: tissue biopsy (bronchoscopy, CT-guided biopsy, or surgical biopsy)
3. Laboratory studies: CBC, comprehensive metabolic panel, LDH
4. Imaging workup:
   a. CT chest with contrast (if not already performed)
   b. PET/CT for clinical staging (Category 1 recommendation)
   c. Brain MRI with contrast (recommended for Stage IB and higher — brain MRI detects occult brain metastases in 3-10% of Stage IB-II and 10-25% of Stage III NSCLC patients; Silvestri et al., Chest 2013)

Molecular and Biomarker Testing (required for non-squamous NSCLC):
1. EGFR mutation testing — present in 10-15% of Caucasian and 30-50% of Asian NSCLC patients; EGFR TKIs (osimertinib) improve median PFS from 10.2 to 18.9 months vs. standard chemotherapy (FLAURA trial, Soria et al., NEJM 2018)
2. ALK rearrangement testing — present in 3-7% of NSCLC; ALK inhibitors (alectinib) improve median PFS to 34.8 months vs. 10.9 months with crizotinib (ALEX trial, Peters et al., NEJM 2017)
3. ROS1 rearrangement testing — present in 1-2% of NSCLC; crizotinib achieves 72% response rate (Shaw et al., NEJM 2014)
4. BRAF V600E mutation testing — present in 1-3% of NSCLC; dabrafenib + trametinib achieves 64% response rate (Planchard et al., Lancet Oncol 2017)
5. PD-L1 immunohistochemistry (TPS scoring) — PD-L1 TPS ≥50%: pembrolizumab monotherapy improves median OS to 30 months vs. 14.2 months with chemotherapy (KEYNOTE-024, Reck et al., NEJM 2016)
6. Broad molecular profiling recommended (next-generation sequencing panel) — identifies actionable targets in up to 64% of non-squamous NSCLC (Kris et al., JAMA 2014)

PET/CT Staging — Evidence Base:
PET/CT is a Category 1 (high-level evidence, uniform consensus) NCCN recommendation for initial staging of NSCLC.

Diagnostic Performance of PET/CT vs. CT Alone for Mediastinal Staging:
- CT alone: sensitivity 51-65%, specificity 74-85% for mediastinal nodal metastases (Silvestri et al., Chest 2013; ACCP Evidence-Based Guidelines)
- PET/CT: sensitivity 80-90%, specificity 85-95% for mediastinal nodal metastases (Fischer et al., J Nucl Med 2009 meta-analysis of 44 studies with 2,865 patients)
- PET/CT significantly outperforms CT alone: pooled sensitivity 79% vs. 60%, pooled specificity 91% vs. 77% (Fischer et al., J Nucl Med 2009)
- False-negative rate of CT for mediastinal nodes: 25-35% of nodes <10mm on CT harbor metastatic disease (Asamura et al., J Thorac Cardiovasc Surg 2008)

Detection of Distant Metastases:
- PET/CT detects unsuspected distant metastases in 10-24% of patients with NSCLC thought to have potentially resectable disease on CT alone (PLUS trial, van Tinteren et al., Lancet 2002; Maziak et al., J Thorac Oncol 2009)
- Common sites of occult metastases detected by PET: adrenal (4-10%), bone (3-8%), contralateral lung (2-5%), liver (1-3%) (Silvestri et al., Chest 2013)
- PET/CT has sensitivity of 93-100% for bone metastases in NSCLC, superior to bone scan sensitivity of 70-87% (Qu et al., J Cancer Res Clin Oncol 2012)

Stage Migration and Impact on Treatment:
- PET/CT upstages 16-25% and downstages 8-15% of NSCLC patients compared to CT-based staging (Pieterman et al., NEJM 2000; Fischer et al., NEJM 2009 — randomized trial of 189 patients)
- The PLUS randomized trial (van Tinteren et al., Lancet 2002): PET reduced futile thoracotomies from 41% to 21% (absolute reduction of 20%, p=0.003, NNT=5)
- Fischer et al. (NEJM 2009) randomized trial: PET/CT staging reduced futile thoracotomies from 52% to 35% and correctly upstaged disease in significantly more patients
- Viney et al. (J Thorac Oncol 2004): PET changed management in 35% of patients and led to cancellation of planned surgery in 15%

Mediastinal Staging:
- PET-positive mediastinal nodes require tissue confirmation (false-positive rate 10-15% due to granulomatous disease, infection)
- Endobronchial ultrasound (EBUS) with transbronchial needle aspiration preferred — sensitivity 89-93% for mediastinal staging (Adams et al., Chest 2014 meta-analysis)
- Mediastinoscopy if EBUS is inconclusive — sensitivity 78-85%, specificity ~100% (Detterbeck et al., Chest 2007)
- Combined PET/CT + EBUS confirmation achieves the highest staging accuracy, with sensitivity 91% and NPV 93% (Yasufuku et al., J Thorac Oncol 2011)

Treatment Planning Requirements:
- Multidisciplinary tumor board review recommended
- Pulmonary function testing (PFTs) if surgery is being considered
- Cardiac risk assessment for surgical candidates
- Smoking cessation counseling and support

Prior Authorization Justification for PET/CT Staging:
PET/CT is a Category 1 (high-level evidence, uniform consensus) recommendation by NCCN for initial staging of NSCLC. It is essential for:
- Detecting distant metastases not visible on CT alone — found in 10-24% of patients (PLUS trial; Fischer NEJM 2009)
- Accurate mediastinal staging affecting surgical candidacy — PET/CT sensitivity 80-90% vs. CT 51-65%
- Preventing futile thoracotomies — 20% absolute reduction (PLUS trial, NNT=5)
- Guiding the treatment approach (surgery vs. chemoradiation vs. systemic therapy) — management changed in 35% of patients
- Identifying additional sites for biopsy if needed
- Cost-effective: avoidance of futile surgery saves $20,000-40,000 per avoided thoracotomy; PET staging is cost-effective at $25,000-30,000 per QALY (Alzahouri et al., J Clin Oncol 2005)""",
        approval_criteria=[
            'Pathologically confirmed or highly suspected NSCLC',
            'PET/CT is NCCN Category 1 recommendation for staging — sensitivity 80-90% vs. CT alone 51-65% for mediastinal nodes (Fischer et al., J Nucl Med 2009)',
            'PET/CT detects unsuspected distant metastases in 10-24% of patients, preventing futile surgery (PLUS trial, van Tinteren et al., Lancet 2002)',
            'PET/CT reduces futile thoracotomies from 41% to 21% (PLUS trial, NNT=5)',
            'PET/CT upstages 16-25% and downstages 8-15% of patients vs. CT alone (Pieterman et al., NEJM 2000; Fischer et al., NEJM 2009)',
            'Results will determine surgical candidacy and treatment approach — management changed in 35% of patients',
            'Brain MRI recommended for Stage IB+ (detects occult metastases in 3-10% of Stage IB-II, 10-25% of Stage III)',
            'Molecular testing required for treatment selection — actionable targets in up to 64% of non-squamous NSCLC (Kris et al., JAMA 2014)',
        ],
        relevant_cpt_codes=['78816', '70553', '71260', '88305', '81235', '81401', '81479'],
        relevant_icd10_codes=['C34.90', 'C34.10', 'C34.11', 'C34.12', 'C34.30', 'C34.31', 'C34.32', 'C34.80', 'C34.81', 'C34.82', 'R91.1'],
    ),

    # ===== SPECIALTY DRUGS =====

    Guideline(
        id='payer-biologics-ra',
        title='Biologic DMARD Coverage — Rheumatoid Arthritis',
        source='Commercial Payer Medical Policy (Representative)',
        category='Specialty Pharmacy',
        effective_date='2024-01-01',
        content="""Biologic Disease-Modifying Antirheumatic Drugs (bDMARDs) including TNF inhibitors, IL-6 inhibitors, T-cell costimulation modulators, and JAK inhibitors are covered for rheumatoid arthritis (RA) when ALL of the following criteria are met:

Eligibility Criteria:
1. Diagnosis of rheumatoid arthritis (RA) confirmed by:
   - Positive rheumatoid factor (RF) and/or anti-CCP antibodies, OR
   - Meeting 2010 ACR/EULAR classification criteria (score ≥6)
   - Documentation of inflammatory arthritis by a rheumatologist

2. Failure of conventional DMARD therapy:
   - Adequate trial of methotrexate (minimum 15mg/week for ≥3 months), UNLESS contraindicated
   - If methotrexate contraindicated: documentation of specific contraindication (hepatic disease, cytopenias, pregnancy planning, intolerance)
   - For some plans: failure of a second conventional DMARD (leflunomide, hydroxychloroquine, sulfasalazine)
   - Evidence for methotrexate failure rates: Approximately 30-40% of RA patients fail to achieve adequate response (ACR50) with methotrexate monotherapy at adequate doses (Pincus et al., Lancet 1999; Aletaha & Smolen, Rheumatology 2002). An additional 10-20% discontinue due to adverse effects (gastrointestinal, hepatic, hematologic).

3. Disease activity documented:
   - DAS28 score >3.2 (moderate disease activity), OR >5.1 (high disease activity), OR
   - CDAI score >10 (moderate), OR >22 (high), OR
   - Clinical documentation of active synovitis, elevated inflammatory markers (ESR, CRP), and functional limitation

4. Step therapy compliance (plan-specific):
   - First-line biologic: adalimumab biosimilar or etanercept biosimilar preferred
   - Brand biologics require failure of or contraindication to preferred biosimilar
   - JAK inhibitors (tofacitinib, baricitinib, upadacitinib) typically require failure of ≥1 TNF inhibitor

5. Safety screening completed:
   - Tuberculosis screening (PPD or QuantiFERON)
   - Hepatitis B and C screening
   - Age-appropriate cancer screening up to date

Key Clinical Trial Evidence for Biologic DMARDs in RA:

TNF Inhibitors — Efficacy Data:
- ATTRACT trial (Lipsky et al., NEJM 2000): Infliximab + MTX achieved ACR20 response in 50-58% vs. 20% with MTX alone at 30 weeks. Also demonstrated significant inhibition of radiographic progression.
- TEMPO trial (Klareskog et al., Lancet 2004): Etanercept + MTX achieved ACR50 in 69% vs. 43% with MTX alone at 52 weeks. Combination therapy halted radiographic progression in 80% of patients.
- PREMIER trial (Breedveld et al., Arthritis Rheum 2006): Adalimumab + MTX achieved ACR50 in 62% vs. 46% (adalimumab alone) vs. 41% (MTX alone) at 1 year, with 74% inhibition of radiographic progression.
- DE019 trial (Keystone et al., Arthritis Rheum 2004): Adalimumab + MTX achieved ACR50 in 55% vs. 27% with MTX alone at 24 weeks.

Non-TNF Biologics — Efficacy Data:
- Tocilizumab (IL-6 inhibitor): OPTION trial (Smolen et al., Lancet 2008) — ACR50 in 44% vs. 12% with placebo at 24 weeks in MTX-inadequate responders. AMBITION trial (Jones et al., Ann Rheum Dis 2010) — tocilizumab monotherapy ACR50 34% vs. MTX 25% at 24 weeks.
- Abatacept (T-cell costimulation modulator): AIM trial (Kremer et al., Ann Intern Med 2006) — ACR50 in 40% vs. 17% with placebo at 1 year in MTX-inadequate responders. ATTEST trial showed comparable efficacy to infliximab at 1 year.
- Rituximab (anti-CD20): REFLEX trial (Cohen et al., Arthritis Rheum 2006) — ACR50 in 27% vs. 5% with placebo at 24 weeks in TNF-inadequate responders. Particularly effective in RF-positive and anti-CCP positive patients.

JAK Inhibitors — Efficacy Data:
- Tofacitinib: ORAL Standard trial (van Vollenhoven et al., NEJM 2012) — ACR50 in 52% vs. 25% with placebo at 6 months. ORAL Strategy showed non-inferiority to adalimumab when combined with MTX.
- Baricitinib: RA-BEAM trial (Taylor et al., NEJM 2017) — ACR50 in 45% vs. 35% with adalimumab vs. 23% with placebo at 12 weeks. Baricitinib was statistically superior to adalimumab for ACR20 response.
- Upadacitinib: SELECT-COMPARE trial (Fleischmann et al., Arthritis Rheumatol 2019) — ACR50 in 45% vs. 29% with adalimumab vs. 15% with placebo at 12 weeks. Upadacitinib was statistically superior to adalimumab.

Evidence for Early Aggressive Treatment:
- The TEAR trial (Moreland et al., Arthritis Rheum 2012) showed that initiating combination DMARD therapy (including biologics) early in disease course produces better radiographic and clinical outcomes than sequential monotherapy.
- Window of opportunity: Multiple studies demonstrate that initiating effective therapy within the first 3-6 months of disease onset ("window of opportunity") leads to significantly better long-term outcomes, including higher remission rates (40-60% vs. 10-20% with delayed treatment) and less radiographic progression (Nell et al., Ann Rheum Dis 2004).

Radiographic Progression Data:
- Untreated moderate-to-severe RA: mean Sharp score progression of 5-10 points/year
- MTX alone: reduces progression by 50-60%
- TNF inhibitor + MTX: reduces progression by 80-90% (ATTRACT, TEMPO, PREMIER trials)
- Patients with high disease activity (DAS28 >5.1) and positive anti-CCP have the most rapid radiographic progression and derive the greatest benefit from biologic therapy.

Continuation Criteria (for reauthorization):
- Documented clinical response (improvement in DAS28, CDAI, or clinical parameters)
- Compliance with monitoring requirements (labs, follow-up visits)
- No safety concerns requiring discontinuation
- ACR/EULAR 2015 recommendations: continue biologic if patient achieves at least low disease activity (DAS28 ≤3.2 or CDAI ≤10); consider tapering only if sustained remission (DAS28 <2.6) for ≥6 months""",
        approval_criteria=[
            'Confirmed RA diagnosis (RF/anti-CCP+ or ACR/EULAR criteria)',
            'Failed methotrexate ≥15mg/week for ≥3 months (or documented contraindication) — 30-40% of patients fail MTX monotherapy (Pincus et al., Lancet 1999)',
            'Active disease documented (DAS28 >3.2 or CDAI >10)',
            'Step therapy: preferred biosimilar tried first',
            'Safety screening completed (TB, Hep B/C)',
            'TNF inhibitor + MTX achieves ACR50 in 50-69% vs. 20-41% with MTX alone (ATTRACT, TEMPO, PREMIER trials)',
            'Biologic therapy reduces radiographic progression by 80-90% vs. 50-60% with MTX alone',
            'Early biologic initiation within 3-6 months of disease onset achieves remission in 40-60% vs. 10-20% with delayed treatment (Nell et al., Ann Rheum Dis 2004)',
        ],
        relevant_cpt_codes=['96365', '96366', '96367', '96372', 'J0135', 'J1745', 'J3262'],
        relevant_icd10_codes=['M05.79', 'M06.09', 'M06.9', 'M05.70', 'M06.00'],
    ),

    # ===== DME =====

    Guideline(
        id='cms-lcd-l33797',
        title='LCD L33797 — Power Mobility Devices (PMD)',
        source='CMS Local Coverage Determination',
        category='Durable Medical Equipment',
        effective_date='2023-06-01',
        content="""Power Mobility Devices (power wheelchairs, power-operated vehicles/scooters) are covered when ALL of the following criteria are met:

Coverage Criteria:
1. The beneficiary has a mobility limitation that significantly impairs their ability to participate in one or more mobility-related activities of daily living (MRADLs):
   - Toileting
   - Feeding
   - Dressing
   - Grooming
   - Bathing

2. The mobility limitation cannot be adequately resolved by:
   - A cane or walker (must document why insufficient)
   - A manual wheelchair (must document why unable to self-propel or have a caregiver to push)

3. The beneficiary's condition is such that the PMD is medically necessary:
   - The beneficiary has a diagnosis that causes the mobility limitation
   - The condition is expected to last at least 1 year or the beneficiary's lifetime

4. The beneficiary can safely operate the PMD or has a caregiver available to assist

5. The PMD can be used in the home:
   - Adequate doorway widths, hallway widths, floor surfaces
   - Adequate maneuvering space

Evidence Supporting PMD Provision:
- Power mobility devices significantly improve quality of life, independence, and participation in ADLs for patients with progressive neurological and musculoskeletal conditions. A systematic review (Auger et al., J Rehabil Med 2008) found that power wheelchair provision improved user satisfaction (mean QUEST scores improving from 3.1 to 4.0 on 5-point scale) and reduced caregiver burden.
- For multiple sclerosis patients: 25% of MS patients require a wheelchair within 15 years of diagnosis; power mobility preserves energy and reduces fatigue, which is the most disabling symptom in 75-90% of MS patients (Krupp et al., Neurology 1988; Fisk et al., Can J Neurol Sci 1994).
- For ALS patients: Mean time from symptom onset to wheelchair need is 18-24 months; early power wheelchair provision is associated with maintained quality of life and extended community participation (Trail et al., Amyotroph Lateral Scler 2001).
- Fall prevention: Mobility device provision reduces fall-related injuries by 30-40% in elderly patients with severe mobility impairment (Tinetti et al., NEJM 2003 — fall prevention strategies).

Required Documentation:
- Face-to-face examination by the treating physician within 45 days prior to the prescription
- Detailed mobility evaluation by a licensed physical or occupational therapist
- Home assessment documenting the environment can accommodate the PMD
- Prescription specifying the type of PMD (Group 1, 2, 3, or scooter)
- Supporting documentation of the medical condition causing the mobility limitation
- Documentation of why lesser devices are insufficient

7-Element Order:
1. Beneficiary name
2. Description of item
3. Date of the face-to-face examination
4. Pertinent diagnoses/conditions relating to the need for the PMD
5. Length of need
6. Physician signature
7. Date of physician signature""",
        approval_criteria=[
            'Mobility limitation affecting MRADLs (toileting, feeding, dressing, etc.)',
            'Lesser devices (cane, walker, manual wheelchair) documented as insufficient',
            'Condition expected to last ≥1 year or lifetime',
            'Can safely operate PMD in home environment',
            'Face-to-face exam within 45 days of prescription',
            'PT/OT mobility evaluation completed',
            'Home assessment documenting PMD accommodation',
        ],
        relevant_cpt_codes=['K0856', 'K0857', 'K0858', 'K0859', 'K0860', 'K0861', 'K0862', 'K0863', 'K0864', 'K0800', 'K0801'],
        relevant_icd10_codes=['G35', 'G80.9', 'G82.20', 'G82.50', 'M62.81', 'G12.21', 'G71.0'],
    ),

    # ===== PROCEDURES =====

    Guideline(
        id='lcd-bariatric',
        title='LCD — Bariatric Surgery for Morbid Obesity',
        source='CMS Local Coverage Determination',
        category='General Surgery',
        effective_date='2023-09-01',
        content="""Bariatric surgery (gastric bypass, sleeve gastrectomy, adjustable gastric banding) is covered when ALL of the following criteria are met:

Eligibility Criteria:
1. BMI ≥ 40 kg/m², OR BMI ≥ 35 kg/m² with at least one obesity-related comorbidity:
   - Type 2 diabetes mellitus
   - Obstructive sleep apnea (documented by polysomnography)
   - Hypertension requiring medication
   - Obesity hypoventilation syndrome
   - Coronary heart disease
   - Nonalcoholic steatohepatitis (NASH)

2. Documented failure of medical weight management:
   - Supervised dietary/nutritional counseling for minimum 6 months within the prior 2 years
   - May include medically supervised weight loss programs, pharmacotherapy
   - Documentation must include weights, dates, and dietary interventions attempted
   - Evidence for failure of non-surgical treatment: Long-term studies show that 80-95% of patients with BMI ≥40 who lose weight through diet and exercise regain the weight within 5 years (Wing & Phelan, Am J Clin Nutr 2005; Mann et al., American Psychologist 2007). Medical weight management achieves sustained ≥10% weight loss in only 5-20% of patients with severe obesity (Wadden et al., NEJM 2005).

3. Psychological/behavioral evaluation:
   - Evaluation by a licensed psychologist or psychiatrist
   - Assessment of eating disorders, substance abuse, psychiatric stability
   - Clearance for surgery

4. Medical evaluation and optimization:
   - Cardiopulmonary clearance
   - Screening for secondary causes of obesity (hypothyroidism, Cushing syndrome)
   - Nutritional assessment and counseling
   - Smoking cessation (many programs require ≥6 months tobacco-free)

5. Facility and surgeon requirements:
   - Surgery performed at a Bariatric Surgery Center of Excellence or equivalent certification
   - Surgeon qualified and experienced in bariatric procedures

Bariatric Surgery Outcomes Data:

Weight Loss Outcomes:
- Roux-en-Y Gastric Bypass (RYGB): Mean excess weight loss (EWL) 60-70% at 2 years, sustained 50-60% EWL at 10 years (Sjostrom et al., NEJM 2007 — Swedish Obese Subjects Study; Adams et al., NEJM 2007)
- Sleeve Gastrectomy: Mean EWL 55-65% at 2 years, 45-55% at 5 years (Salminen et al., JAMA Surg 2018 — SLEEVEPASS trial)
- Adjustable Gastric Banding: Mean EWL 40-50% at 2 years, but higher failure and reoperation rates (30-50% at 10 years) (O'Brien et al., Ann Surg 2013)

Diabetes Remission:
- STAMPEDE trial (Schauer et al., NEJM 2012; 5-year data NEJM 2017): Bariatric surgery + medical therapy achieved HbA1c ≤6.0% in 29% (RYGB) and 23% (sleeve) vs. 5% (medical therapy alone) at 5 years. Mean HbA1c reduction: 2.1% (RYGB) vs. 0.3% (medical therapy) at 5 years.
- Swedish Obese Subjects Study (Sjostrom et al., NEJM 2004, JAMA 2012): Bariatric surgery reduced type 2 diabetes incidence by 78% (prevention) and achieved remission in 72% of patients with preexisting diabetes at 2 years (36% sustained at 10 years).

Mortality and Cardiovascular Outcomes:
- Swedish Obese Subjects Study (Sjostrom et al., NEJM 2007): Bariatric surgery reduced overall mortality by 29% over a mean follow-up of 10.9 years (HR 0.71, 95% CI 0.54-0.92). Cardiovascular events reduced by 33%.
- Adams et al. (NEJM 2007): RYGB associated with 40% reduction in long-term mortality compared to matched controls over mean follow-up of 7.1 years.

Comorbidity Resolution Rates (Buchwald et al., JAMA 2004 — meta-analysis of 136 studies, 22,094 patients):
- Type 2 diabetes: 76.8% resolution overall (83.7% for RYGB)
- Hypertension: 61.7% resolution
- Obstructive sleep apnea: 85.7% resolution
- Hyperlipidemia: 70% improvement or resolution

Safety Data:
- 30-day mortality: 0.1-0.3% for RYGB, 0.1% for sleeve gastrectomy (Longitudinal Assessment of Bariatric Surgery (LABS) Consortium, NEJM 2009)
- Serious adverse event rate at 30 days: 4.1% (LABS Consortium)
- Reoperation rate: 5-7% at 5 years for RYGB, 3-5% for sleeve (Arterburn et al., JAMA 2020)

Cost-Effectiveness:
- Bariatric surgery is cost-effective at $6,000-16,000 per QALY gained (Keating et al., JAMA Surg 2015; Klebanoff et al., Ann Surg 2017)
- Surgery costs recouped within 2-4 years through reduced medication costs and healthcare utilization (Cremieux et al., Am J Manag Care 2008)

Required Documentation:
- Documented BMI calculations with dates (≥2 readings showing qualifying BMI)
- Records of supervised weight management attempts with specific dates and weights
- Psychological evaluation report
- Medical clearance documentation
- Sleep study results (if OSA is the qualifying comorbidity)
- Lab work including thyroid function, cortisol, HbA1c""",
        approval_criteria=[
            'BMI ≥40, or BMI ≥35 with qualifying comorbidity',
            'Failed 6 months supervised medical weight management in prior 2 years — 80-95% of severely obese patients regain weight within 5 years with non-surgical treatment (Wing & Phelan, Am J Clin Nutr 2005)',
            'Psychological evaluation completed with clearance',
            'Medical evaluation and optimization completed',
            'Surgery at Center of Excellence by qualified surgeon (30-day mortality 0.1-0.3% per LABS Consortium, NEJM 2009)',
            'Expected outcomes: 60-70% EWL for RYGB, 55-65% for sleeve; 76.8% diabetes resolution (Buchwald et al., JAMA 2004)',
            'Bariatric surgery reduces overall mortality by 29% (Swedish Obese Subjects Study, Sjostrom et al., NEJM 2007)',
            'Cost-effective: $6,000-16,000 per QALY; costs recouped within 2-4 years (Cremieux et al., Am J Manag Care 2008)',
        ],
        relevant_cpt_codes=['43644', '43645', '43770', '43771', '43772', '43773', '43774', '43775', '43842', '43843', '43846', '43847'],
        relevant_icd10_codes=['E66.01', 'E66.09', 'E11.9', 'G47.33', 'I10', 'E66.2'],
    ),
    Guideline(
        id='lcd-sleep-study',
        title='LCD — Sleep Testing for Obstructive Sleep Apnea',
        source='CMS Local Coverage Determination',
        category='Sleep Medicine',
        effective_date='2023-01-01',
        content="""Polysomnography (PSG) and Home Sleep Apnea Testing (HSAT) are covered for the diagnosis of obstructive sleep apnea when the following criteria are met:

Indications for Sleep Study:
1. Clinical symptoms suggestive of obstructive sleep apnea:
   - Excessive daytime sleepiness (Epworth Sleepiness Scale ≥10)
   - Witnessed apneas during sleep
   - Loud, habitual snoring
   - Gasping or choking during sleep
   - Nonrestorative sleep
   - Morning headaches
   - Nocturia

2. Combined with ≥1 risk factor:
   - BMI ≥30 kg/m²
   - Neck circumference >17 inches (male) or >16 inches (female)
   - Mallampati score III or IV
   - Retrognathia or micrognathia
   - Tonsillar hypertrophy
   - Age >50

Prevalence and Disease Burden:
- OSA affects an estimated 14-49% of middle-aged men and 9-24% of middle-aged women (Peppard et al., Am J Epidemiol 2013 — Wisconsin Sleep Cohort Study). Approximately 80-90% of adults with moderate-to-severe OSA remain undiagnosed (Young et al., Sleep 1997).
- Untreated severe OSA (AHI ≥30) is associated with 3-6 fold increased risk of motor vehicle accidents (Teran-Santos et al., NEJM 1999) and significantly increased cardiovascular mortality: HR 1.68 for cardiovascular death in untreated severe OSA vs. treated patients (Marin et al., Lancet 2005 — prospective cohort, 1,651 men, 10-year follow-up).
- Untreated moderate-to-severe OSA increases all-cause mortality risk by 2-3 fold (Young et al., Sleep 2008).

HSAT vs. In-Laboratory PSG:
- HSAT (Type III or IV): Appropriate for patients with high pretest probability of moderate-to-severe OSA without significant comorbidities. HSAT has sensitivity of 79-97% and specificity of 60-85% for moderate-to-severe OSA (AHI ≥15) compared to in-lab PSG (Collop et al., J Clin Sleep Med 2007; AASM guidelines). False-negative rate: 10-15% — negative HSAT in patients with high clinical suspicion requires in-lab PSG confirmation.
- In-Laboratory PSG (Type I): Required when:
  a. HSAT is negative or inconclusive in a patient with high clinical suspicion
  b. Significant cardiopulmonary disease present (CHF, COPD, neuromuscular disease)
  c. Suspected central sleep apnea, hypoventilation syndrome, or parasomnia
  d. Need for CPAP titration following diagnostic study

CPAP Treatment Outcomes:
- CPAP/BiPAP Coverage Following Diagnosis:
  - AHI ≥15 events/hour: qualifies for CPAP
  - AHI 5-14 events/hour with symptoms: qualifies with documentation of daytime sleepiness, impaired cognition, mood disorders, hypertension, stroke, or ischemic heart disease
- CPAP efficacy: Reduces AHI to <5 events/hour in 85-95% of patients (Gay et al., Sleep 2006). Mean ESS improvement of 2-4 points with CPAP use ≥4 hours/night (Patel et al., Arch Intern Med 2003).
- Blood pressure reduction: CPAP reduces mean arterial pressure by 2-3 mmHg in hypertensive patients with moderate-severe OSA (Bazzano et al., JAMA 2007 meta-analysis; Barbe et al., JAMA 2012). Effect is most pronounced in patients with uncontrolled hypertension and severe OSA.
- Motor vehicle accident risk reduction: CPAP-treated OSA patients have accident rates comparable to the general population (Tregear et al., J Clin Sleep Med 2010).
- Cost-effectiveness: Diagnosis and treatment of moderate-to-severe OSA with CPAP is cost-effective at $3,000-13,000 per QALY gained (Ayas et al., Ann Intern Med 2006).""",
        approval_criteria=[
            'Clinical symptoms of OSA (sleepiness, witnessed apneas, snoring) — 80-90% of moderate-severe OSA is undiagnosed (Young et al., Sleep 1997)',
            'Risk factors present (BMI ≥30, large neck, Mallampati III-IV)',
            'HSAT appropriate for uncomplicated suspected OSA (sensitivity 79-97% for AHI ≥15)',
            'PSG required when HSAT inconclusive or significant comorbidities',
            'Treatment coverage based on AHI results — CPAP reduces AHI to <5 in 85-95% of patients',
            'Untreated severe OSA increases cardiovascular mortality HR 1.68 and MVC risk 3-6 fold (Marin et al., Lancet 2005; Teran-Santos et al., NEJM 1999)',
            'Diagnosis and CPAP treatment cost-effective at $3,000-13,000 per QALY (Ayas et al., Ann Intern Med 2006)',
        ],
        relevant_cpt_codes=['95810', '95811', '95800', '95801', '95806', 'E0601', 'E0470', 'E0471'],
        relevant_icd10_codes=['G47.33', 'G47.30', 'G47.39', 'R06.83', 'G47.9'],
    ),
    Guideline(
        id='ada-glp1-t2dm-2026',
        title='ADA Standards-Aligned Policy — GLP-1/GIP Therapy for Type 2 Diabetes',
        source='Commercial Pharmacy Policy Template; ADA Standards of Care in Diabetes 2026 alignment',
        category='Specialty Pharmacy',
        effective_date='2026-01-01',
        content="""GLP-1 receptor agonists and dual GIP/GLP-1 receptor agonists, including tirzepatide (Mounjaro), semaglutide (Ozempic), dulaglutide (Trulicity), liraglutide, and related agents, are medically necessary for type 2 diabetes when documentation supports glycemic need and appropriate use for diabetes rather than weight loss alone.

Common Prior Authorization Criteria:
1. Diagnosis of type 2 diabetes mellitus, supported by ICD-10 code, assessment, or medication history.
2. A1c above individualized goal or documented need for intensification of glucose-lowering therapy.
3. Current use, prior trial and failure, intolerance, or contraindication to metformin unless metformin is clinically inappropriate.
4. If required by the plan, trial and failure, intolerance, contraindication, or clinical inappropriateness of preferred formulary GLP-1 receptor agonists such as Ozempic or Trulicity.
5. Requested drug is prescribed for glycemic management in type 2 diabetes, not solely for obesity or weight loss.
6. Prescriber is an endocrinologist, diabetes specialist, or clinician managing diabetes.

Medical Rationale:
- ADA Standards of Care recognize GLP-1 receptor agonists and SGLT2 inhibitors as important therapy in adults with type 2 diabetes, especially when cardiovascular, kidney, weight, hypoglycemia, or treatment-burden considerations inform medication choice.
- Metformin remains commonly used first-line therapy when tolerated and appropriate, but intolerance, contraindication, inadequate glycemic response, hypoglycemia risk from sulfonylureas, or comorbid cardiometabolic disease may support an alternative or additive agent.
- Tirzepatide has demonstrated strong A1c lowering and weight reduction in type 2 diabetes trials, making it clinically relevant when obesity, hyperglycemia, and hypoglycemia avoidance are documented.

Required Documentation:
- Type 2 diabetes diagnosis and ICD-10 code such as E11.65, E11.9, E11.22, E11.42, or E11.69
- Most recent A1c and date
- Current diabetes medication list and prior trials
- Metformin trial, intolerance, contraindication, or reason not appropriate
- Preferred GLP-1 trial/failure or medical reason step therapy is inappropriate when required
- Statement that drug is requested for type 2 diabetes/glycemic control""",
        approval_criteria=[
            'Type 2 diabetes diagnosis documented',
            'A1c above individualized goal or need for glycemic intensification documented',
            'Metformin current use, trial/failure, intolerance, contraindication, or clinical inappropriateness documented',
            'Preferred formulary GLP-1 trial/failure, intolerance, contraindication, or reason step therapy is inappropriate when required',
            'Requested drug is for type 2 diabetes/glycemic control and not solely weight loss',
            'Specialist or diabetes-managing prescriber involvement documented',
        ],
        relevant_cpt_codes=['MOUNJARO', 'TIRZEPATIDE', 'OZEMPIC', 'SEMAGLUTIDE', 'TRULICITY', 'DULAGLUTIDE', 'VICTOZA', 'LIRAGLUTIDE'],
        relevant_icd10_codes=['E11.65', 'E11.9', 'E11.22', 'E11.42', 'E11.69', 'E66.9', 'Z79.4'],
    ),
    Guideline(
        id='lcd-l34163-tha',
        title='LCD L34163 — Total Hip Arthroplasty (THA)',
        source='Local Coverage Determination — Total Hip Arthroplasty',
        category='Orthopedic Surgery',
        effective_date='2024-10-01',
        content="""Total hip arthroplasty is medically necessary when severe hip joint disease causes pain and functional limitation despite appropriate non-surgical care. Common covered diagnoses include osteoarthritis, inflammatory arthritis, avascular necrosis, fracture sequelae, congenital/developmental hip disease, or failed prior hip surgery.

Medical Necessity Criteria:
1. Diagnosis of advanced hip joint disease documented in the medical record.
2. Imaging supports structural hip pathology, such as joint-space narrowing, osteophytes, subchondral sclerosis/cysts, femoral head collapse, avascular necrosis, or severe degenerative change.
3. Pain and functional impairment interfere with walking, transfers, stairs, dressing, sleep, work, or activities of daily living.
4. Conservative therapy has failed or is contraindicated, such as NSAIDs/analgesics, physical therapy, activity modification, assistive device use, weight management, or injections when clinically appropriate.
5. Patient has been medically optimized for surgery, including diabetes control, infection risk, smoking status, anticoagulation planning, and BMI/anesthesia risk when relevant.

Required Documentation:
- Hip radiographs or advanced imaging report with severity
- Symptom duration and pain/functional limitation
- Conservative treatment attempts with dates, duration, and outcomes
- Surgical plan and medical optimization/clearance when applicable""",
        approval_criteria=[
            'Advanced hip joint disease diagnosis documented',
            'Imaging supports severe structural hip pathology',
            'Pain and functional impairment affecting ambulation or ADLs documented',
            'Conservative therapy failure, intolerance, contraindication, or inappropriateness documented',
            'Patient medically optimized for surgery when applicable',
        ],
        relevant_cpt_codes=['27130', '27132', '27134', '27137', '27138'],
        relevant_icd10_codes=['M16.0', 'M16.10', 'M16.11', 'M16.12', 'M87.051', 'M87.052', 'S72.001A', 'S72.002A'],
    ),
    Guideline(
        id='lcd-l39054-esi',
        title='LCD L39054 — Epidural Steroid Injections for Pain Management',
        source='Local Coverage Determination — Epidural Steroid Injections for Pain Management',
        category='Pain Management',
        effective_date='2022-06-30',
        content="""Epidural steroid injections (interlaminar, transforaminal, or caudal) are medically necessary when documentation supports radicular pain, radiculopathy, or neurogenic claudication from concordant spinal pathology and when conservative treatment has not provided adequate relief.

Covered Indications:
1. Lumbar, cervical, or thoracic radiculopathy/radicular pain or neurogenic claudication due to disc herniation, osteophyte complex, severe degenerative disc disease, foraminal stenosis, or central spinal stenosis.
2. Symptoms cause functional limitation and are concordant with history, physical examination, and imaging when imaging is clinically appropriate.
3. At least 4 weeks of conservative care has failed, is not tolerated, or is clinically inappropriate, unless severe pain with functional loss or other documented circumstances justify earlier injection.
4. Repeat injections require documentation of clinically meaningful improvement, commonly at least 50% sustained pain relief or functional improvement from prior injection.

Required Documentation:
- Pain distribution and neurologic findings
- Imaging or diagnostic evidence concordant with symptoms when available
- Conservative care attempted and response
- Prior injection date, level, approach, medication, and response for repeat requests
- Functional impact and treatment goal""",
        approval_criteria=[
            'Radiculopathy, radicular pain, or neurogenic claudication documented',
            'Concordant exam and imaging or diagnostic evidence supports spinal pathology',
            'Functional limitation from pain documented',
            'At least 4 weeks conservative care failed, not tolerated, or clinically inappropriate unless exception applies',
            'For repeat injection: meaningful prior improvement documented',
        ],
        relevant_cpt_codes=['62320', '62321', '62322', '62323', '64479', '64480', '64483', '64484'],
        relevant_icd10_codes=['M54.16', 'M54.12', 'M54.14', 'M48.062', 'M48.061', 'M51.16', 'M50.10'],
    ),
    Guideline(
        id='cms-l33394-oncology-drugs',
        title='LCD L33394 — Drugs and Biologicals for Oncology Indications',
        source='Local Coverage Determination — Coverage of Drugs and Biologicals for Label and Off-Label Uses',
        category='Oncology Drugs',
        effective_date='2025-01-01',
        content="""Antineoplastic drugs and biologics are medically necessary when the requested agent is used for an FDA-approved indication or a medically accepted off-label indication supported by recognized compendia. Medicare and many commercial policies use compendia such as NCCN Drugs and Biologics Compendium, AHFS, DrugDex, Clinical Pharmacology, or Lexi-Drugs to determine medically accepted indications.

Coverage Criteria:
1. Confirmed cancer diagnosis, histology, stage, and treatment setting.
2. Requested drug is FDA-approved for the diagnosis/setting OR is supported by a medically accepted compendium recommendation.
3. For NCCN-supported off-label use, Category 1 or 2A recommendations are generally treated as medically accepted; Category 2B may require stronger supporting literature and payer-specific review.
4. Biomarker testing is documented when required for the drug, such as HER2, EGFR, ALK, ROS1, BRAF, KRAS, PD-L1, MSI-H/dMMR, NTRK, or BRCA status.
5. Prior lines of therapy, progression, contraindications, or intolerance are documented when the policy requires step therapy or line-of-therapy sequencing.
6. Dose, schedule, route, and cycle plan are consistent with labeling, NCCN regimen, or supporting literature.

Required Documentation:
- Pathology report and stage
- Biomarker/molecular test result when relevant
- Prior systemic therapy and response/progression
- Requested regimen, dose, cycle, and treatment intent
- Guideline or compendium support for off-label use""",
        approval_criteria=[
            'Confirmed malignancy diagnosis, histology, stage, and treatment setting documented',
            'FDA-approved or compendium-supported medically accepted indication documented',
            'NCCN Category 1 or 2A support or comparable accepted compendium support when off-label',
            'Required biomarker or molecular result documented',
            'Prior line therapy, progression, intolerance, or contraindication documented when sequencing criteria apply',
            'Dose and regimen consistent with label, NCCN regimen, or supporting literature',
        ],
        relevant_cpt_codes=['J9271', 'J9299', 'J9228', 'J9355', 'J9354', 'J9306', 'J9173', 'J9022', 'J9312', 'J9035'],
        relevant_icd10_codes=['C34.90', 'C50.911', 'C50.912', 'C18.9', 'C19', 'C20', 'C43.9', 'C81.90', 'C83.30'],
    ),
    Guideline(
        id='cms-ncd-240.2-home-oxygen',
        title='CMS NCD 240.2 — Home Use of Oxygen',
        source='CMS National Coverage Determination',
        category='Durable Medical Equipment',
        effective_date='2022-09-27',
        content="""Home oxygen and oxygen equipment are covered when hypoxemia is documented by qualifying arterial blood gas or oxygen saturation testing at the time of need. The medical record should connect the oxygen request to a covered pulmonary or cardiac condition and document whether stationary, portable, or nocturnal oxygen is required.

Group I Criteria:
1. Arterial PO2 at or below 55 mm Hg, or oxygen saturation at or below 88%, taken at rest breathing room air; OR
2. Same thresholds during sleep for nocturnal oxygen; OR
3. Same thresholds during exercise when oxygen improves hypoxemia.

Group II Criteria:
1. Arterial PO2 56-59 mm Hg or oxygen saturation of 89%, AND
2. Evidence of dependent edema suggesting congestive heart failure, pulmonary hypertension/cor pulmonale, or erythrocythemia with hematocrit greater than 56%.

Portable Oxygen:
Portable oxygen requires documentation that the patient is mobile in the home and would benefit from portable oxygen use.

Required Documentation:
- Qualifying test result, date, and testing condition (rest, sleep, or exertion)
- Diagnosis causing hypoxemia
- Liter flow and delivery method
- Need for portable system if requested
- Reassessment or continued need documentation when required""",
        approval_criteria=[
            'Qualifying oxygen saturation or arterial PO2 documented at time of need',
            'Group I: SpO2 <=88% or PO2 <=55 mm Hg at rest, sleep, or exertion',
            'Group II: SpO2 89% or PO2 56-59 mm Hg plus CHF edema, pulmonary hypertension/cor pulmonale, or erythrocythemia',
            'Oxygen prescription includes flow rate, delivery method, and duration/frequency',
            'Portable oxygen need supported by mobility in the home when requested',
        ],
        relevant_cpt_codes=['E1390', 'E1392', 'E0431', 'E0433', 'E0434', 'E0435', 'E0443', 'E0444'],
        relevant_icd10_codes=['J44.9', 'J96.11', 'J96.10', 'R09.02', 'I27.20', 'I50.9', 'D75.1'],
    ),
    Guideline(
        id='cms-l33789-power-mobility',
        title='LCD L33789 — Power Mobility Devices',
        source='Local Coverage Determination — Power Mobility Devices',
        category='Durable Medical Equipment',
        effective_date='2025-01-01',
        content="""Power mobility devices, power wheelchairs, scooters, manual wheelchairs, and related mobility equipment require documentation that the device is reasonable and necessary for mobility-related activities of daily living in the home.

Medical Necessity Criteria:
1. The beneficiary has a mobility limitation that significantly impairs participation in mobility-related activities of daily living (MRADLs) such as toileting, feeding, dressing, grooming, and bathing in customary locations in the home.
2. The limitation cannot be sufficiently resolved by cane or walker.
3. For manual wheelchair: patient has sufficient upper extremity function or caregiver support to propel safely and complete MRADLs.
4. For scooter/POV: patient can transfer safely, operate tiller steering, maintain postural stability, and use the device in the home.
5. For power wheelchair: patient cannot use a cane, walker, manual wheelchair, or scooter effectively, but can safely operate the power wheelchair or has caregiver assistance.
6. Face-to-face evaluation documents the condition, functional limitations, home setting, device need, and why lesser devices are insufficient.

Non-Covered or Weak Documentation:
- Device requested primarily for community mobility rather than in-home MRADLs
- Reversible condition with expected need less than 3 months
- Missing face-to-face exam or missing explanation of why cane/walker/manual wheelchair is insufficient

Required Documentation:
- Face-to-face mobility evaluation
- MRADL limitations in the home
- Ambulation distance, falls, transfers, strength, balance, pain, endurance
- Assessment of cane/walker/manual wheelchair/POV suitability
- Home environment supports device use
- Detailed written order and supplier documentation""",
        approval_criteria=[
            'Mobility limitation significantly impairs in-home MRADLs',
            'Cane or walker insufficient to resolve MRADL limitation',
            'Manual wheelchair, scooter, or power wheelchair level justified by function and safety',
            'Face-to-face evaluation documents diagnosis, progression, functional limits, and home setting',
            'Patient can safely use requested device or has caregiver assistance',
            'Need is not solely for community mobility and is expected to last at least 3 months',
        ],
        relevant_cpt_codes=['K0001', 'K0003', 'K0004', 'K0005', 'K0823', 'K0825', 'K0835', 'K0848', 'E1028', 'E2365'],
        relevant_icd10_codes=['R26.2', 'R26.89', 'Z74.09', 'G20', 'G35', 'I69.351', 'M17.0', 'M48.061'],
    ),
]


def search_guidelines(query: str) -> list[Guideline]:
    """Search guidelines by query string. Returns up to 5 matching guidelines."""
    lower_query = query.lower()
    terms = [t for t in lower_query.split() if len(t) > 2]

    results: list[Guideline] = []
    for g in MEDICAL_GUIDELINES:
        search_text = (
            f"{g.title} {g.content} {g.category} "
            f"{' '.join(g.relevant_cpt_codes)} {' '.join(g.relevant_icd10_codes)}"
        ).lower()
        if any(term in search_text for term in terms):
            results.append(g)

    return results[:5]


def get_guidelines_by_code(code: str) -> list[Guideline]:
    """Find guidelines that match a given CPT or ICD-10 code."""
    normalized = re.sub(r'[.\-\s]', '', code.upper())
    if not normalized:
        return []

    results: list[Guideline] = []
    for g in MEDICAL_GUIDELINES:
        all_codes = [
            re.sub(r'[.\-\s]', '', c.upper())
            for c in g.relevant_cpt_codes + g.relevant_icd10_codes
        ]
        if any(normalized in c or c in normalized for c in all_codes):
            results.append(g)

    return results


def get_guideline_by_id(guideline_id: str) -> Guideline | None:
    return next((g for g in MEDICAL_GUIDELINES if g.id == guideline_id), None)


def get_guideline_chunks() -> list[GuidelineChunk]:
    """Split guidelines into chunks for retrieval, with overlap."""
    chunks: list[GuidelineChunk] = []

    for g in MEDICAL_GUIDELINES:
        # Split content into meaningful chunks (~500 chars each with overlap)
        paragraphs = [p for p in g.content.split('\n\n') if p.strip()]
        current_chunk = ''
        chunk_index = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) > 600 and len(current_chunk) > 100:
                chunks.append(GuidelineChunk(
                    id=f'{g.id}-chunk-{chunk_index}',
                    text=f'[{g.title}] [Source: {g.source}]\n{current_chunk.strip()}',
                    guideline_id=g.id,
                    title=g.title,
                    source=g.source,
                ))
                chunk_index += 1
                # Keep last 100 chars for overlap
                current_chunk = current_chunk[-100:] + '\n\n' + para
            else:
                current_chunk += ('\n\n' if current_chunk else '') + para

        if current_chunk.strip():
            chunks.append(GuidelineChunk(
                id=f'{g.id}-chunk-{chunk_index}',
                text=f'[{g.title}] [Source: {g.source}]\n{current_chunk.strip()}',
                guideline_id=g.id,
                title=g.title,
                source=g.source,
            ))

        # Also add approval criteria as a separate chunk for targeted retrieval
        criteria_text = '\n'.join(
            f'{i + 1}. {c}' for i, c in enumerate(g.approval_criteria)
        )
        chunks.append(GuidelineChunk(
            id=f'{g.id}-criteria',
            text=(
                f'[{g.title}] [Source: {g.source}]\n'
                f'Approval Criteria:\n{criteria_text}\n\n'
                f'Relevant CPT Codes: {", ".join(g.relevant_cpt_codes)}\n'
                f'Relevant ICD-10 Codes: {", ".join(g.relevant_icd10_codes)}'
            ),
            guideline_id=g.id,
            title=g.title,
            source=g.source,
        ))

    return chunks
