"""Deterministic evaluation scenarios for retrieval and letter-quality checks."""

DENIAL_VARIANTS = [
    "Insufficient documentation of medical necessity.",
    "Requested service does not meet payer policy criteria.",
    "Records do not show failed conservative management or standard workup.",
    "Clinical documentation does not establish that the service will change management.",
    "Request is considered investigational for the submitted diagnosis.",
]


BASE_SCENARIOS = [
    {
        "id": "ct-pe",
        "expectedGuidelineIds": ["cms-ncd-220.1"],
        "clinicalNotes": "PATIENT: Elena Rivera\nDOB: 04/11/1968\nAcute pleuritic chest pain, tachycardia, elevated D-dimer, and Wells score 6. CT pulmonary angiography requested to evaluate suspected pulmonary embolism after chest X-ray was nondiagnostic.",
        "deniedService": "CT pulmonary angiography chest",
        "cptCodes": "71275",
        "icd10Codes": "I26.99, R07.9",
    },
    {
        "id": "mri-lumbar",
        "expectedGuidelineIds": ["cms-ncd-220.2"],
        "clinicalNotes": "PATIENT: Marcus Green\nDOB: 02/02/1975\nEight weeks of lumbar radiculopathy with right leg weakness, failed NSAIDs and supervised PT. MRI lumbar spine requested for surgical planning.",
        "deniedService": "MRI lumbar spine without contrast",
        "cptCodes": "72148",
        "icd10Codes": "M54.5",
    },
    {
        "id": "pet-nsclc",
        "expectedGuidelineIds": ["cms-ncd-220.6", "nccn-nsclc-2024"],
        "clinicalNotes": "PATIENT: David Kowalski\nDOB: 11/30/1964\nBiopsy-confirmed NSCLC adenocarcinoma RUL with mediastinal lymphadenopathy on CT. PET/CT requested for initial staging and operability planning.",
        "deniedService": "PET/CT whole body tumor staging",
        "cptCodes": "78816",
        "icd10Codes": "C34.11",
    },
    {
        "id": "tka",
        "expectedGuidelineIds": ["lcd-l35014"],
        "clinicalNotes": "PATIENT: Margaret Thompson\nDOB: 05/12/1957\nSevere right knee OA, KL Grade 4 bone-on-bone, WOMAC 72/96, VAS 8/10, failed 8 months PT, NSAIDs, steroid injections, hyaluronic acid, bracing, and weight management.",
        "deniedService": "Total knee arthroplasty right",
        "cptCodes": "27447",
        "icd10Codes": "M17.11",
    },
    {
        "id": "lumbar-fusion",
        "expectedGuidelineIds": ["lcd-l35077"],
        "clinicalNotes": "PATIENT: Hannah Lee\nDOB: 07/19/1961\nGrade II degenerative spondylolisthesis with stenosis, neurogenic claudication, radiculopathy, instability on flexion-extension films, and failed 4 months conservative therapy.",
        "deniedService": "Lumbar spinal fusion",
        "cptCodes": "22612",
        "icd10Codes": "M43.16, M48.06",
    },
    {
        "id": "cardiac-cath",
        "expectedGuidelineIds": ["cms-ncd-20.7"],
        "clinicalNotes": "PATIENT: Robert Williams\nDOB: 08/23/1953\nNew exertional angina with stress echo showing 2.5mm ST depression and new LAD-territory wall motion abnormality at low workload. Cardiac catheterization requested.",
        "deniedService": "Left heart catheterization with coronary angiography",
        "cptCodes": "93458",
        "icd10Codes": "I20.9, I25.10",
    },
    {
        "id": "nsclc-guideline",
        "expectedGuidelineIds": ["nccn-nsclc-2024", "cms-ncd-220.6"],
        "clinicalNotes": "PATIENT: Priya Shah\nDOB: 09/09/1959\nStage IIIA suspected NSCLC with biopsy-proven adenocarcinoma and mediastinal nodes. PET/CT and NCCN-guided staging requested before treatment.",
        "deniedService": "NSCLC staging workup with PET/CT",
        "cptCodes": "78815",
        "icd10Codes": "C34.12",
    },
    {
        "id": "ra-biologic",
        "expectedGuidelineIds": ["payer-biologics-ra"],
        "clinicalNotes": "PATIENT: Sandra Mills\nDOB: 01/21/1970\nSeropositive rheumatoid arthritis with DAS28 6.1 despite methotrexate and hydroxychloroquine for 5 months. Biologic DMARD requested.",
        "deniedService": "Biologic DMARD therapy for rheumatoid arthritis",
        "cptCodes": "J1745",
        "icd10Codes": "M06.9",
    },
    {
        "id": "power-mobility",
        "expectedGuidelineIds": ["cms-lcd-l33797"],
        "clinicalNotes": "PATIENT: Thomas Bell\nDOB: 03/18/1952\nSevere mobility limitation from neuromuscular disease, unable to complete MRADLs with cane or walker, upper-extremity weakness prevents manual wheelchair use. Power mobility device requested.",
        "deniedService": "Power mobility device",
        "cptCodes": "K0823",
        "icd10Codes": "G35",
    },
    {
        "id": "bariatric",
        "expectedGuidelineIds": ["lcd-bariatric"],
        "clinicalNotes": "PATIENT: Angela Brooks\nDOB: 10/10/1984\nBMI 43.2 with type 2 diabetes and hypertension. Completed six months supervised weight loss program and psychological evaluation. Sleeve gastrectomy requested.",
        "deniedService": "Laparoscopic sleeve gastrectomy",
        "cptCodes": "43775",
        "icd10Codes": "E66.01",
    },
    {
        "id": "sleep-study",
        "expectedGuidelineIds": ["lcd-sleep-study"],
        "clinicalNotes": "PATIENT: James Carter\nDOB: 06/14/1978\nLoud snoring, witnessed apneas, Epworth Sleepiness Scale 16, BMI 34, neck circumference 18 inches, hypertension. Sleep study requested for suspected OSA.",
        "deniedService": "Diagnostic polysomnography",
        "cptCodes": "95810",
        "icd10Codes": "G47.33, R06.83",
    },
]


def build_eval_cases() -> list[dict]:
    cases: list[dict] = []
    for base in BASE_SCENARIOS:
        for index, denial_reason in enumerate(DENIAL_VARIANTS, start=1):
            case = {
                **base,
                "id": f"{base['id']}-{index}",
                "denialReason": denial_reason,
                "insuranceCompany": "Evaluation Health Plan",
                "patientName": base["clinicalNotes"].split("\n", 1)[0].replace("PATIENT: ", ""),
                "patientDOB": "01/01/1970",
                "memberId": f"EVAL-{base['id'].upper()}-{index:02d}",
                "claimNumber": f"PA-2026-{base['id'].upper()}-{index:02d}",
                "denialDate": "04/01/2026",
                "physicianName": "Dr. Evaluation",
                "physicianNPI": "1234567890",
                "practiceName": "AppealAI Evaluation Clinic",
            }
            cases.append(case)
    return cases


EVALUATION_CASES = build_eval_cases()
