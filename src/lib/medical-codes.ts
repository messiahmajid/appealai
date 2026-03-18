/**
 * Medical Code Databases — ICD-10 and CPT
 * Common codes relevant to prior authorization denials
 */

export interface MedicalCode {
    code: string;
    description: string;
    category: string;
}

export const ICD10_CODES: MedicalCode[] = [
    // Musculoskeletal
    { code: 'M17.0', description: 'Bilateral primary osteoarthritis of knee', category: 'Musculoskeletal' },
    { code: 'M17.10', description: 'Primary osteoarthritis, unspecified knee', category: 'Musculoskeletal' },
    { code: 'M17.11', description: 'Primary osteoarthritis, right knee', category: 'Musculoskeletal' },
    { code: 'M17.12', description: 'Primary osteoarthritis, left knee', category: 'Musculoskeletal' },
    { code: 'M16.0', description: 'Bilateral primary osteoarthritis of hip', category: 'Musculoskeletal' },
    { code: 'M16.11', description: 'Primary osteoarthritis, right hip', category: 'Musculoskeletal' },
    { code: 'M16.12', description: 'Primary osteoarthritis, left hip', category: 'Musculoskeletal' },
    { code: 'M54.5', description: 'Low back pain', category: 'Musculoskeletal' },
    { code: 'M54.41', description: 'Lumbago with sciatica, right side', category: 'Musculoskeletal' },
    { code: 'M54.42', description: 'Lumbago with sciatica, left side', category: 'Musculoskeletal' },
    { code: 'M51.16', description: 'Intervertebral disc disorders with radiculopathy, lumbar region', category: 'Musculoskeletal' },
    { code: 'M51.17', description: 'Intervertebral disc disorders with radiculopathy, lumbosacral region', category: 'Musculoskeletal' },
    { code: 'M43.16', description: 'Spondylolisthesis, lumbar region', category: 'Musculoskeletal' },
    { code: 'M43.06', description: 'Spondylolysis, lumbar region', category: 'Musculoskeletal' },
    { code: 'M47.816', description: 'Spondylosis without myelopathy, lumbar region', category: 'Musculoskeletal' },
    { code: 'M48.06', description: 'Spinal stenosis, lumbar region', category: 'Musculoskeletal' },
    { code: 'M23.20', description: 'Derangement of unspecified meniscus due to old tear', category: 'Musculoskeletal' },
    { code: 'M75.10', description: 'Rotator cuff tear, unspecified shoulder', category: 'Musculoskeletal' },
    { code: 'M79.3', description: 'Panniculitis, unspecified', category: 'Musculoskeletal' },
    { code: 'M62.81', description: 'Muscle weakness (generalized)', category: 'Musculoskeletal' },
    { code: 'M06.9', description: 'Rheumatoid arthritis, unspecified', category: 'Musculoskeletal' },
    { code: 'M05.79', description: 'Rheumatoid arthritis with rheumatoid factor, multiple sites', category: 'Musculoskeletal' },
    { code: 'M87.9', description: 'Osteonecrosis, unspecified', category: 'Musculoskeletal' },

    // Cardiovascular
    { code: 'I25.10', description: 'Atherosclerotic heart disease of native coronary artery without angina pectoris', category: 'Cardiovascular' },
    { code: 'I25.110', description: 'Atherosclerotic heart disease of native coronary artery with unstable angina pectoris', category: 'Cardiovascular' },
    { code: 'I25.5', description: 'Ischemic cardiomyopathy', category: 'Cardiovascular' },
    { code: 'I20.0', description: 'Unstable angina', category: 'Cardiovascular' },
    { code: 'I20.9', description: 'Angina pectoris, unspecified', category: 'Cardiovascular' },
    { code: 'I21.9', description: 'Acute myocardial infarction, unspecified', category: 'Cardiovascular' },
    { code: 'I21.01', description: 'ST elevation myocardial infarction involving left main coronary artery', category: 'Cardiovascular' },
    { code: 'I21.11', description: 'ST elevation myocardial infarction involving right coronary artery', category: 'Cardiovascular' },
    { code: 'I21.4', description: 'Non-ST elevation myocardial infarction', category: 'Cardiovascular' },
    { code: 'I10', description: 'Essential (primary) hypertension', category: 'Cardiovascular' },
    { code: 'I50.9', description: 'Heart failure, unspecified', category: 'Cardiovascular' },
    { code: 'I26.99', description: 'Other pulmonary embolism without acute cor pulmonale', category: 'Cardiovascular' },
    { code: 'I48.91', description: 'Unspecified atrial fibrillation', category: 'Cardiovascular' },

    // Oncology
    { code: 'C34.90', description: 'Malignant neoplasm of unspecified part of unspecified bronchus or lung', category: 'Oncology' },
    { code: 'C34.10', description: 'Malignant neoplasm of upper lobe, unspecified bronchus or lung', category: 'Oncology' },
    { code: 'C34.11', description: 'Malignant neoplasm of upper lobe, right bronchus or lung', category: 'Oncology' },
    { code: 'C34.12', description: 'Malignant neoplasm of upper lobe, left bronchus or lung', category: 'Oncology' },
    { code: 'C18.9', description: 'Malignant neoplasm of colon, unspecified', category: 'Oncology' },
    { code: 'C50.911', description: 'Malignant neoplasm of unspecified site of right female breast', category: 'Oncology' },
    { code: 'C50.912', description: 'Malignant neoplasm of unspecified site of left female breast', category: 'Oncology' },
    { code: 'C61', description: 'Malignant neoplasm of prostate', category: 'Oncology' },
    { code: 'C81.90', description: 'Hodgkin lymphoma, unspecified, unspecified site', category: 'Oncology' },
    { code: 'C83.90', description: 'Non-follicular lymphoma, unspecified, unspecified site', category: 'Oncology' },
    { code: 'C43.9', description: 'Malignant melanoma of skin, unspecified', category: 'Oncology' },
    { code: 'R91.1', description: 'Solitary pulmonary nodule', category: 'Oncology' },

    // Endocrine/Metabolic
    { code: 'E11.9', description: 'Type 2 diabetes mellitus without complications', category: 'Endocrine' },
    { code: 'E11.65', description: 'Type 2 diabetes mellitus with hyperglycemia', category: 'Endocrine' },
    { code: 'E66.01', description: 'Morbid (severe) obesity due to excess calories', category: 'Endocrine' },
    { code: 'E66.09', description: 'Other obesity due to excess calories', category: 'Endocrine' },
    { code: 'E66.2', description: 'Morbid (severe) obesity with alveolar hypoventilation', category: 'Endocrine' },

    // Neurological
    { code: 'G35', description: 'Multiple sclerosis', category: 'Neurological' },
    { code: 'G47.33', description: 'Obstructive sleep apnea', category: 'Neurological' },
    { code: 'G47.30', description: 'Sleep apnea, unspecified', category: 'Neurological' },
    { code: 'G80.9', description: 'Cerebral palsy, unspecified', category: 'Neurological' },
    { code: 'G82.20', description: 'Paraplegia, unspecified', category: 'Neurological' },
    { code: 'G82.50', description: 'Quadriplegia, unspecified', category: 'Neurological' },
    { code: 'G12.21', description: 'Amyotrophic lateral sclerosis', category: 'Neurological' },
    { code: 'G71.0', description: 'Muscular dystrophy', category: 'Neurological' },
    { code: 'R51.9', description: 'Headache, unspecified', category: 'Neurological' },

    // General/Symptoms
    { code: 'R10.9', description: 'Unspecified abdominal pain', category: 'Symptoms' },
    { code: 'R07.9', description: 'Chest pain, unspecified', category: 'Symptoms' },
    { code: 'R06.83', description: 'Snoring', category: 'Symptoms' },
    { code: 'S06.9', description: 'Intracranial injury, unspecified', category: 'Trauma' },
];

export const CPT_CODES: MedicalCode[] = [
    // Advanced Imaging
    { code: '70551', description: 'MRI brain without contrast', category: 'Advanced Imaging' },
    { code: '70552', description: 'MRI brain with contrast', category: 'Advanced Imaging' },
    { code: '70553', description: 'MRI brain without contrast, followed by with contrast', category: 'Advanced Imaging' },
    { code: '71250', description: 'CT chest without contrast', category: 'Advanced Imaging' },
    { code: '71260', description: 'CT chest with contrast', category: 'Advanced Imaging' },
    { code: '71270', description: 'CT chest without contrast, followed by with contrast', category: 'Advanced Imaging' },
    { code: '72141', description: 'MRI cervical spine without contrast', category: 'Advanced Imaging' },
    { code: '72146', description: 'MRI thoracic spine without contrast', category: 'Advanced Imaging' },
    { code: '72148', description: 'MRI lumbar spine without contrast', category: 'Advanced Imaging' },
    { code: '72156', description: 'MRI cervical spine without contrast, followed by with contrast', category: 'Advanced Imaging' },
    { code: '73221', description: 'MRI upper extremity joint without contrast', category: 'Advanced Imaging' },
    { code: '73721', description: 'MRI lower extremity joint without contrast (knee, ankle)', category: 'Advanced Imaging' },
    { code: '73722', description: 'MRI lower extremity joint with contrast', category: 'Advanced Imaging' },
    { code: '74176', description: 'CT abdomen and pelvis without contrast', category: 'Advanced Imaging' },
    { code: '74177', description: 'CT abdomen and pelvis with contrast', category: 'Advanced Imaging' },
    { code: '74178', description: 'CT abdomen and pelvis without contrast, followed by with contrast', category: 'Advanced Imaging' },
    { code: '78816', description: 'PET/CT for tumor, whole body', category: 'Advanced Imaging' },
    { code: '78814', description: 'PET/CT for tumor, limited area', category: 'Advanced Imaging' },

    // Orthopedic Surgery
    { code: '27447', description: 'Total knee arthroplasty (replacement)', category: 'Orthopedic Surgery' },
    { code: '27446', description: 'Revision of total knee arthroplasty', category: 'Orthopedic Surgery' },
    { code: '27130', description: 'Total hip arthroplasty (replacement)', category: 'Orthopedic Surgery' },
    { code: '29881', description: 'Arthroscopy knee, surgical; meniscectomy', category: 'Orthopedic Surgery' },
    { code: '29882', description: 'Arthroscopy knee, surgical; meniscus repair', category: 'Orthopedic Surgery' },
    { code: '23472', description: 'Total shoulder arthroplasty (replacement)', category: 'Orthopedic Surgery' },

    // Spine Surgery
    { code: '22551', description: 'Arthrodesis, anterior interbody, cervical', category: 'Spine Surgery' },
    { code: '22554', description: 'Arthrodesis, anterior interbody, cervical below C2', category: 'Spine Surgery' },
    { code: '22558', description: 'Arthrodesis, anterior interbody, lumbar', category: 'Spine Surgery' },
    { code: '22612', description: 'Arthrodesis, posterior or posterolateral, lumbar', category: 'Spine Surgery' },
    { code: '22630', description: 'Arthrodesis, posterior interbody technique, lumbar', category: 'Spine Surgery' },
    { code: '22633', description: 'Arthrodesis, combined posterior/interbody, lumbar', category: 'Spine Surgery' },
    { code: '63030', description: 'Laminotomy with decompression (discectomy), lumbar', category: 'Spine Surgery' },
    { code: '63047', description: 'Laminectomy for decompression, lumbar', category: 'Spine Surgery' },

    // Cardiology
    { code: '93451', description: 'Right heart catheterization', category: 'Cardiology' },
    { code: '93452', description: 'Left heart catheterization, retrograde', category: 'Cardiology' },
    { code: '93453', description: 'Combined right and left heart catheterization', category: 'Cardiology' },
    { code: '93454', description: 'Catheter placement in coronary artery(s) for coronary angiography', category: 'Cardiology' },
    { code: '93458', description: 'Left heart catheterization with coronary angiography and left ventriculography', category: 'Cardiology' },
    { code: '92920', description: 'Percutaneous coronary intervention, single vessel', category: 'Cardiology' },
    { code: '92928', description: 'Percutaneous coronary intervention with stent, single vessel', category: 'Cardiology' },
    { code: '93306', description: 'Echocardiography, transthoracic, complete', category: 'Cardiology' },
    { code: '93350', description: 'Stress echocardiography', category: 'Cardiology' },
    { code: '78452', description: 'Myocardial perfusion imaging (nuclear stress test)', category: 'Cardiology' },

    // General Surgery
    { code: '43644', description: 'Laparoscopic gastric bypass (Roux-en-Y)', category: 'Bariatric Surgery' },
    { code: '43775', description: 'Laparoscopic sleeve gastrectomy', category: 'Bariatric Surgery' },
    { code: '43770', description: 'Laparoscopic adjustable gastric band placement', category: 'Bariatric Surgery' },
    { code: '47562', description: 'Laparoscopic cholecystectomy', category: 'General Surgery' },
    { code: '49650', description: 'Laparoscopic inguinal hernia repair', category: 'General Surgery' },

    // Sleep Medicine
    { code: '95810', description: 'Polysomnography; sleep staging with 4+ channels', category: 'Sleep Medicine' },
    { code: '95811', description: 'Polysomnography; with CPAP titration', category: 'Sleep Medicine' },
    { code: '95800', description: 'Sleep study, unattended', category: 'Sleep Medicine' },

    // Infusion/Injection
    { code: '96365', description: 'Intravenous infusion, for therapy, initial up to 1 hour', category: 'Infusion' },
    { code: '96372', description: 'Therapeutic, prophylactic, or diagnostic injection, subcutaneous or intramuscular', category: 'Injection' },
    { code: 'J0135', description: 'Adalimumab injection', category: 'Drug Administration' },
    { code: 'J1745', description: 'Infliximab injection', category: 'Drug Administration' },
    { code: 'J3262', description: 'Tocilizumab injection', category: 'Drug Administration' },

    // DME
    { code: 'E0601', description: 'CPAP device', category: 'DME' },
    { code: 'E0470', description: 'RAD (Respiratory Assist Device), BiPAP without backup rate', category: 'DME' },
    { code: 'K0856', description: 'Power wheelchair, Group 3 standard, single power option', category: 'DME' },

    // Pathology
    { code: '88305', description: 'Level IV - Surgical pathology, gross and microscopic examination', category: 'Pathology' },
    { code: '81235', description: 'EGFR gene analysis', category: 'Molecular Pathology' },
    { code: '81401', description: 'Molecular pathology procedure, Level 2', category: 'Molecular Pathology' },
    { code: '81479', description: 'Unlisted molecular pathology procedure (NGS panel)', category: 'Molecular Pathology' },
];

export function searchICD10(query: string): MedicalCode[] {
    if (!query || query.length < 2) return [];
    const lower = query.toLowerCase();
    return ICD10_CODES.filter(
        c =>
            c.code.toLowerCase().includes(lower) ||
            c.description.toLowerCase().includes(lower) ||
            c.category.toLowerCase().includes(lower)
    ).slice(0, 15);
}

export function searchCPT(query: string): MedicalCode[] {
    if (!query || query.length < 2) return [];
    const lower = query.toLowerCase();
    return CPT_CODES.filter(
        c =>
            c.code.toLowerCase().includes(lower) ||
            c.description.toLowerCase().includes(lower) ||
            c.category.toLowerCase().includes(lower)
    ).slice(0, 15);
}
