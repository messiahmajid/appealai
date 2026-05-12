"""
Medical Code Databases -- ICD-10 and CPT
Common codes relevant to prior authorization denials
"""

from dataclasses import dataclass


@dataclass
class MedicalCode:
    code: str
    description: str
    category: str


ICD10_CODES: list[MedicalCode] = [
    # Musculoskeletal
    MedicalCode(code="M17.0", description="Bilateral primary osteoarthritis of knee", category="Musculoskeletal"),
    MedicalCode(code="M17.10", description="Primary osteoarthritis, unspecified knee", category="Musculoskeletal"),
    MedicalCode(code="M17.11", description="Primary osteoarthritis, right knee", category="Musculoskeletal"),
    MedicalCode(code="M17.12", description="Primary osteoarthritis, left knee", category="Musculoskeletal"),
    MedicalCode(code="M16.0", description="Bilateral primary osteoarthritis of hip", category="Musculoskeletal"),
    MedicalCode(code="M16.11", description="Primary osteoarthritis, right hip", category="Musculoskeletal"),
    MedicalCode(code="M16.12", description="Primary osteoarthritis, left hip", category="Musculoskeletal"),
    MedicalCode(code="M54.5", description="Low back pain", category="Musculoskeletal"),
    MedicalCode(code="M54.41", description="Lumbago with sciatica, right side", category="Musculoskeletal"),
    MedicalCode(code="M54.42", description="Lumbago with sciatica, left side", category="Musculoskeletal"),
    MedicalCode(code="M51.16", description="Intervertebral disc disorders with radiculopathy, lumbar region", category="Musculoskeletal"),
    MedicalCode(code="M51.17", description="Intervertebral disc disorders with radiculopathy, lumbosacral region", category="Musculoskeletal"),
    MedicalCode(code="M43.16", description="Spondylolisthesis, lumbar region", category="Musculoskeletal"),
    MedicalCode(code="M43.06", description="Spondylolysis, lumbar region", category="Musculoskeletal"),
    MedicalCode(code="M47.816", description="Spondylosis without myelopathy, lumbar region", category="Musculoskeletal"),
    MedicalCode(code="M48.06", description="Spinal stenosis, lumbar region", category="Musculoskeletal"),
    MedicalCode(code="M23.20", description="Derangement of unspecified meniscus due to old tear", category="Musculoskeletal"),
    MedicalCode(code="M75.10", description="Rotator cuff tear, unspecified shoulder", category="Musculoskeletal"),
    MedicalCode(code="M79.3", description="Panniculitis, unspecified", category="Musculoskeletal"),
    MedicalCode(code="M62.81", description="Muscle weakness (generalized)", category="Musculoskeletal"),
    MedicalCode(code="M06.9", description="Rheumatoid arthritis, unspecified", category="Musculoskeletal"),
    MedicalCode(code="M05.79", description="Rheumatoid arthritis with rheumatoid factor, multiple sites", category="Musculoskeletal"),
    MedicalCode(code="M87.9", description="Osteonecrosis, unspecified", category="Musculoskeletal"),

    # Cardiovascular
    MedicalCode(code="I25.10", description="Atherosclerotic heart disease of native coronary artery without angina pectoris", category="Cardiovascular"),
    MedicalCode(code="I25.110", description="Atherosclerotic heart disease of native coronary artery with unstable angina pectoris", category="Cardiovascular"),
    MedicalCode(code="I25.5", description="Ischemic cardiomyopathy", category="Cardiovascular"),
    MedicalCode(code="I20.0", description="Unstable angina", category="Cardiovascular"),
    MedicalCode(code="I20.9", description="Angina pectoris, unspecified", category="Cardiovascular"),
    MedicalCode(code="I21.9", description="Acute myocardial infarction, unspecified", category="Cardiovascular"),
    MedicalCode(code="I21.01", description="ST elevation myocardial infarction involving left main coronary artery", category="Cardiovascular"),
    MedicalCode(code="I21.11", description="ST elevation myocardial infarction involving right coronary artery", category="Cardiovascular"),
    MedicalCode(code="I21.4", description="Non-ST elevation myocardial infarction", category="Cardiovascular"),
    MedicalCode(code="I10", description="Essential (primary) hypertension", category="Cardiovascular"),
    MedicalCode(code="I50.9", description="Heart failure, unspecified", category="Cardiovascular"),
    MedicalCode(code="I26.99", description="Other pulmonary embolism without acute cor pulmonale", category="Cardiovascular"),
    MedicalCode(code="I48.91", description="Unspecified atrial fibrillation", category="Cardiovascular"),

    # Oncology
    MedicalCode(code="C34.90", description="Malignant neoplasm of unspecified part of unspecified bronchus or lung", category="Oncology"),
    MedicalCode(code="C34.10", description="Malignant neoplasm of upper lobe, unspecified bronchus or lung", category="Oncology"),
    MedicalCode(code="C34.11", description="Malignant neoplasm of upper lobe, right bronchus or lung", category="Oncology"),
    MedicalCode(code="C34.12", description="Malignant neoplasm of upper lobe, left bronchus or lung", category="Oncology"),
    MedicalCode(code="C18.9", description="Malignant neoplasm of colon, unspecified", category="Oncology"),
    MedicalCode(code="C50.911", description="Malignant neoplasm of unspecified site of right female breast", category="Oncology"),
    MedicalCode(code="C50.912", description="Malignant neoplasm of unspecified site of left female breast", category="Oncology"),
    MedicalCode(code="C61", description="Malignant neoplasm of prostate", category="Oncology"),
    MedicalCode(code="C81.90", description="Hodgkin lymphoma, unspecified, unspecified site", category="Oncology"),
    MedicalCode(code="C83.90", description="Non-follicular lymphoma, unspecified, unspecified site", category="Oncology"),
    MedicalCode(code="C43.9", description="Malignant melanoma of skin, unspecified", category="Oncology"),
    MedicalCode(code="R91.1", description="Solitary pulmonary nodule", category="Oncology"),

    # Endocrine/Metabolic
    MedicalCode(code="E11.9", description="Type 2 diabetes mellitus without complications", category="Endocrine"),
    MedicalCode(code="E11.65", description="Type 2 diabetes mellitus with hyperglycemia", category="Endocrine"),
    MedicalCode(code="E66.01", description="Morbid (severe) obesity due to excess calories", category="Endocrine"),
    MedicalCode(code="E66.09", description="Other obesity due to excess calories", category="Endocrine"),
    MedicalCode(code="E66.2", description="Morbid (severe) obesity with alveolar hypoventilation", category="Endocrine"),

    # Neurological
    MedicalCode(code="G35", description="Multiple sclerosis", category="Neurological"),
    MedicalCode(code="G47.33", description="Obstructive sleep apnea", category="Neurological"),
    MedicalCode(code="G47.30", description="Sleep apnea, unspecified", category="Neurological"),
    MedicalCode(code="G80.9", description="Cerebral palsy, unspecified", category="Neurological"),
    MedicalCode(code="G82.20", description="Paraplegia, unspecified", category="Neurological"),
    MedicalCode(code="G82.50", description="Quadriplegia, unspecified", category="Neurological"),
    MedicalCode(code="G12.21", description="Amyotrophic lateral sclerosis", category="Neurological"),
    MedicalCode(code="G71.0", description="Muscular dystrophy", category="Neurological"),
    MedicalCode(code="R51.9", description="Headache, unspecified", category="Neurological"),

    # General/Symptoms
    MedicalCode(code="R10.9", description="Unspecified abdominal pain", category="Symptoms"),
    MedicalCode(code="R07.9", description="Chest pain, unspecified", category="Symptoms"),
    MedicalCode(code="R06.83", description="Snoring", category="Symptoms"),
    MedicalCode(code="S06.9", description="Intracranial injury, unspecified", category="Trauma"),
]

CPT_CODES: list[MedicalCode] = [
    # Advanced Imaging
    MedicalCode(code="70551", description="MRI brain without contrast", category="Advanced Imaging"),
    MedicalCode(code="70552", description="MRI brain with contrast", category="Advanced Imaging"),
    MedicalCode(code="70553", description="MRI brain without contrast, followed by with contrast", category="Advanced Imaging"),
    MedicalCode(code="71250", description="CT chest without contrast", category="Advanced Imaging"),
    MedicalCode(code="71260", description="CT chest with contrast", category="Advanced Imaging"),
    MedicalCode(code="71270", description="CT chest without contrast, followed by with contrast", category="Advanced Imaging"),
    MedicalCode(code="72141", description="MRI cervical spine without contrast", category="Advanced Imaging"),
    MedicalCode(code="72146", description="MRI thoracic spine without contrast", category="Advanced Imaging"),
    MedicalCode(code="72148", description="MRI lumbar spine without contrast", category="Advanced Imaging"),
    MedicalCode(code="72156", description="MRI cervical spine without contrast, followed by with contrast", category="Advanced Imaging"),
    MedicalCode(code="73221", description="MRI upper extremity joint without contrast", category="Advanced Imaging"),
    MedicalCode(code="73721", description="MRI lower extremity joint without contrast (knee, ankle)", category="Advanced Imaging"),
    MedicalCode(code="73722", description="MRI lower extremity joint with contrast", category="Advanced Imaging"),
    MedicalCode(code="74176", description="CT abdomen and pelvis without contrast", category="Advanced Imaging"),
    MedicalCode(code="74177", description="CT abdomen and pelvis with contrast", category="Advanced Imaging"),
    MedicalCode(code="74178", description="CT abdomen and pelvis without contrast, followed by with contrast", category="Advanced Imaging"),
    MedicalCode(code="78816", description="PET/CT for tumor, whole body", category="Advanced Imaging"),
    MedicalCode(code="78814", description="PET/CT for tumor, limited area", category="Advanced Imaging"),

    # Orthopedic Surgery
    MedicalCode(code="27447", description="Total knee arthroplasty (replacement)", category="Orthopedic Surgery"),
    MedicalCode(code="27446", description="Revision of total knee arthroplasty", category="Orthopedic Surgery"),
    MedicalCode(code="27130", description="Total hip arthroplasty (replacement)", category="Orthopedic Surgery"),
    MedicalCode(code="29881", description="Arthroscopy knee, surgical; meniscectomy", category="Orthopedic Surgery"),
    MedicalCode(code="29882", description="Arthroscopy knee, surgical; meniscus repair", category="Orthopedic Surgery"),
    MedicalCode(code="23472", description="Total shoulder arthroplasty (replacement)", category="Orthopedic Surgery"),

    # Spine Surgery
    MedicalCode(code="22551", description="Arthrodesis, anterior interbody, cervical", category="Spine Surgery"),
    MedicalCode(code="22554", description="Arthrodesis, anterior interbody, cervical below C2", category="Spine Surgery"),
    MedicalCode(code="22558", description="Arthrodesis, anterior interbody, lumbar", category="Spine Surgery"),
    MedicalCode(code="22612", description="Arthrodesis, posterior or posterolateral, lumbar", category="Spine Surgery"),
    MedicalCode(code="22630", description="Arthrodesis, posterior interbody technique, lumbar", category="Spine Surgery"),
    MedicalCode(code="22633", description="Arthrodesis, combined posterior/interbody, lumbar", category="Spine Surgery"),
    MedicalCode(code="63030", description="Laminotomy with decompression (discectomy), lumbar", category="Spine Surgery"),
    MedicalCode(code="63047", description="Laminectomy for decompression, lumbar", category="Spine Surgery"),

    # Cardiology
    MedicalCode(code="93451", description="Right heart catheterization", category="Cardiology"),
    MedicalCode(code="93452", description="Left heart catheterization, retrograde", category="Cardiology"),
    MedicalCode(code="93453", description="Combined right and left heart catheterization", category="Cardiology"),
    MedicalCode(code="93454", description="Catheter placement in coronary artery(s) for coronary angiography", category="Cardiology"),
    MedicalCode(code="93458", description="Left heart catheterization with coronary angiography and left ventriculography", category="Cardiology"),
    MedicalCode(code="92920", description="Percutaneous coronary intervention, single vessel", category="Cardiology"),
    MedicalCode(code="92928", description="Percutaneous coronary intervention with stent, single vessel", category="Cardiology"),
    MedicalCode(code="93306", description="Echocardiography, transthoracic, complete", category="Cardiology"),
    MedicalCode(code="93350", description="Stress echocardiography", category="Cardiology"),
    MedicalCode(code="78452", description="Myocardial perfusion imaging (nuclear stress test)", category="Cardiology"),

    # General Surgery
    MedicalCode(code="43644", description="Laparoscopic gastric bypass (Roux-en-Y)", category="Bariatric Surgery"),
    MedicalCode(code="43775", description="Laparoscopic sleeve gastrectomy", category="Bariatric Surgery"),
    MedicalCode(code="43770", description="Laparoscopic adjustable gastric band placement", category="Bariatric Surgery"),
    MedicalCode(code="47562", description="Laparoscopic cholecystectomy", category="General Surgery"),
    MedicalCode(code="49650", description="Laparoscopic inguinal hernia repair", category="General Surgery"),

    # Sleep Medicine
    MedicalCode(code="95810", description="Polysomnography; sleep staging with 4+ channels", category="Sleep Medicine"),
    MedicalCode(code="95811", description="Polysomnography; with CPAP titration", category="Sleep Medicine"),
    MedicalCode(code="95800", description="Sleep study, unattended", category="Sleep Medicine"),

    # Infusion/Injection
    MedicalCode(code="96365", description="Intravenous infusion, for therapy, initial up to 1 hour", category="Infusion"),
    MedicalCode(code="96372", description="Therapeutic, prophylactic, or diagnostic injection, subcutaneous or intramuscular", category="Injection"),
    MedicalCode(code="J0135", description="Adalimumab injection", category="Drug Administration"),
    MedicalCode(code="J1745", description="Infliximab injection", category="Drug Administration"),
    MedicalCode(code="J3262", description="Tocilizumab injection", category="Drug Administration"),

    # DME
    MedicalCode(code="E0601", description="CPAP device", category="DME"),
    MedicalCode(code="E0470", description="RAD (Respiratory Assist Device), BiPAP without backup rate", category="DME"),
    MedicalCode(code="K0856", description="Power wheelchair, Group 3 standard, single power option", category="DME"),

    # Pathology
    MedicalCode(code="88305", description="Level IV - Surgical pathology, gross and microscopic examination", category="Pathology"),
    MedicalCode(code="81235", description="EGFR gene analysis", category="Molecular Pathology"),
    MedicalCode(code="81401", description="Molecular pathology procedure, Level 2", category="Molecular Pathology"),
    MedicalCode(code="81479", description="Unlisted molecular pathology procedure (NGS panel)", category="Molecular Pathology"),
]


def search_icd10(query: str) -> list[MedicalCode]:
    """Search ICD-10 codes by code, description, or category."""
    if not query or len(query) < 2:
        return []
    lower = query.lower()
    return [
        c for c in ICD10_CODES
        if lower in c.code.lower()
        or lower in c.description.lower()
        or lower in c.category.lower()
    ][:15]


def search_cpt(query: str) -> list[MedicalCode]:
    """Search CPT codes by code, description, or category."""
    if not query or len(query) < 2:
        return []
    lower = query.lower()
    return [
        c for c in CPT_CODES
        if lower in c.code.lower()
        or lower in c.description.lower()
        or lower in c.category.lower()
    ][:15]
