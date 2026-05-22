'use client';

import { useState, useEffect, useRef, Suspense, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import ReactMarkdown from 'react-markdown';
import {
    Upload,
    FileText,
    AlertCircle,
    ChevronRight,
    ChevronLeft,
    Check,
    Search,
    ClipboardCopy,
    Download,
    ArrowLeft,
} from 'lucide-react';
import { SAMPLE_CASES } from '@/lib/sample-data';
import { mergeDetails, parseClinicalNoteDetails, parseDenialDetails, type ParsedDetails } from '@/lib/detail-parser';

interface MedicalCode {
    code: string;
    description: string;
    category: string;
}

interface Citation {
    index: number;
    guidelineId: string;
    title: string;
    source: string;
    text: string;
}

interface RAGSource {
    guidelineId: string;
    title: string;
    source: string;
    relevanceScore: number;
}

interface VerificationCheck {
    check: string;
    status: 'PASS' | 'FAIL' | 'WARNING';
    details: string;
}

interface VerificationResult {
    overallVerdict: 'PASS' | 'NEEDS_REVIEW' | 'FAIL';
    confidenceScore: number;
    checks: VerificationCheck[];
    flaggedIssues: string[];
    summary: string;
}

interface SafetyReport {
    verdict: 'PASS' | 'NEEDS_REVIEW' | 'FAIL';
    issues: Array<{ code: string; severity: 'error' | 'warning'; message: string; evidence?: string }>;
    structuredAnalysis?: {
        criteria?: Array<{ criterion: string; status: 'met' | 'unclear' | 'not_met'; evidenceSpanIds: string[]; missingElements: string[]; guidelineTitle: string }>;
        documentationGaps?: string[];
        contraindicationWarnings?: string[];
        policyMetadata?: Array<{ title: string; source: string; effectiveDate: string; freshnessStatus: string }>;
    };
    repairAttempted?: boolean;
}

interface ClinicalSufficiencyReport {
    status: 'pass' | 'needs_review' | 'block';
    score: number;
    summary: string;
    presentElements: string[];
    missingElements: string[];
    blockingReasons: string[];
    suggestions: string[];
    warnings: string[];
}

type GenerationStageStatus = 'pending' | 'active' | 'done' | 'error';

interface GenerationStage {
    id: string;
    label: string;
    status: GenerationStageStatus;
    detail?: string;
}

interface ProgressEventPayload {
    stage: string;
    message: string;
    data?: Record<string, unknown>;
}

const DEFAULT_GENERATION_STAGES: GenerationStage[] = [
    { id: 'guidelines', label: 'Retrieve policies', status: 'pending' },
    { id: 'sufficiency', label: 'Check notes', status: 'pending' },
    { id: 'pubmed', label: 'Search PubMed', status: 'pending' },
    { id: 'generation', label: 'Generate draft', status: 'pending' },
    { id: 'safety', label: 'Run safety checks', status: 'pending' },
    { id: 'save', label: 'Save result', status: 'pending' },
];

// Separate component that uses useSearchParams
function NewAppealContent() {
    const router = useRouter();
    const searchParams = useSearchParams();

    const [step, setStep] = useState(1);

    // Step 1: Clinical Notes
    const [clinicalNotes, setClinicalNotes] = useState('');
    const [fileName, setFileName] = useState('');
    const [isExtractingFile, setIsExtractingFile] = useState(false);
    const [fileError, setFileError] = useState('');

    // Step 2: Denial Details
    const [patientName, setPatientName] = useState('');
    const [patientDOB, setPatientDOB] = useState('');
    const [memberId, setMemberId] = useState('');
    const [insuranceCompany, setInsuranceCompany] = useState('');
    const [claimNumber, setClaimNumber] = useState('');
    const [denialDate, setDenialDate] = useState('');
    const [denialReason, setDenialReason] = useState('');
    const [deniedService, setDeniedService] = useState('');
    const [cptCodes, setCptCodes] = useState('');
    const [icd10Codes, setIcd10Codes] = useState('');
    const [physicianName, setPhysicianName] = useState('');
    const [physicianNPI, setPhysicianNPI] = useState('');
    const [practiceName, setPracticeName] = useState('');
    const [parsedDetailNotice, setParsedDetailNotice] = useState('');

    // CPT/ICD Autocomplete
    const [cptSearch, setCptSearch] = useState('');
    const [cptResults, setCptResults] = useState<MedicalCode[]>([]);
    const [showCptResults, setShowCptResults] = useState(false);
    const [icd10Search, setIcd10Search] = useState('');
    const [icd10Results, setIcd10Results] = useState<MedicalCode[]>([]);
    const [showIcd10Results, setShowIcd10Results] = useState(false);
    const cptRef = useRef<HTMLDivElement>(null);
    const icd10Ref = useRef<HTMLDivElement>(null);

    // Step 3: Results
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedLetter, setGeneratedLetter] = useState('');
    const [citations, setCitations] = useState<Citation[]>([]);
    const [ragSources, setRagSources] = useState<RAGSource[]>([]);
    const [error, setError] = useState('');
    const [appealId, setAppealId] = useState('');
    const [webEvidence, setWebEvidence] = useState<{ source: string; title: string; citation: string; url: string }[]>([]);
    const [safetyReport, setSafetyReport] = useState<SafetyReport | null>(null);
    const [clinicalSufficiencyReport, setClinicalSufficiencyReport] = useState<ClinicalSufficiencyReport | null>(null);
    const [copied, setCopied] = useState(false);
    const [loadingStep, setLoadingStep] = useState('');
    const [generationStages, setGenerationStages] = useState<GenerationStage[]>(DEFAULT_GENERATION_STAGES);
    const [verification, setVerification] = useState<VerificationResult | null>(null);
    const [isVerifying, setIsVerifying] = useState(false);

    // Load sample case
    useEffect(() => {
        const sampleId = searchParams.get('sample');
        if (sampleId) {
            const sc = SAMPLE_CASES.find(c => c.id === sampleId);
            if (sc) {
                setClinicalNotes(sc.clinicalNotes);
                setFileName(`${sc.specialty}_clinical_note.txt`);
                setPatientName(sc.patientName);
                setPatientDOB(sc.patientDOB);
                setMemberId(sc.memberId);
                setInsuranceCompany(sc.insuranceCompany);
                setClaimNumber(sc.claimNumber);
                setDenialDate(sc.denialDate);
                setDenialReason(sc.denialReason);
                setDeniedService(sc.deniedService);
                setCptCodes(sc.cptCodes);
                setIcd10Codes(sc.icd10Codes);
                setPhysicianName(sc.physicianName);
                setPhysicianNPI(sc.physicianNPI);
                setPracticeName(sc.practiceName);
            }
        }
    }, [searchParams]);

    // Click outside to close autocomplete
    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (cptRef.current && !cptRef.current.contains(e.target as Node)) setShowCptResults(false);
            if (icd10Ref.current && !icd10Ref.current.contains(e.target as Node)) setShowIcd10Results(false);
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // CPT search
    useEffect(() => {
        if (cptSearch.length < 2) { setCptResults([]); return; }
        const timer = setTimeout(() => {
            fetch(`/api/codes/cpt?q=${encodeURIComponent(cptSearch)}`)
                .then(r => r.json())
                .then(d => { setCptResults(d.results || []); setShowCptResults(true); })
                .catch(() => { });
        }, 200);
        return () => clearTimeout(timer);
    }, [cptSearch]);

    // ICD-10 search
    useEffect(() => {
        if (icd10Search.length < 2) { setIcd10Results([]); return; }
        const timer = setTimeout(() => {
            fetch(`/api/codes/icd10?q=${encodeURIComponent(icd10Search)}`)
                .then(r => r.json())
                .then(d => { setIcd10Results(d.results || []); setShowIcd10Results(true); })
                .catch(() => { });
        }, 200);
        return () => clearTimeout(timer);
    }, [icd10Search]);

    // File handling
    const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file) readFile(file);
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) readFile(file);
    };

    function applyClinicalNoteParsedDetails(text: string) {
        const details = parseClinicalNoteDetails(text);
        let applied = 0;
        const setIfEmpty = (value: string | undefined, current: string, setter: (value: string) => void) => {
            if (value && !current.trim()) {
                setter(value);
                applied += 1;
            }
        };

        setIfEmpty(details.patientName, patientName, setPatientName);
        setIfEmpty(details.patientDOB, patientDOB, setPatientDOB);
        setIfEmpty(details.memberId, memberId, setMemberId);
        setIfEmpty(details.insuranceCompany, insuranceCompany, setInsuranceCompany);
        setIfEmpty(details.deniedService, deniedService, setDeniedService);
        setIfEmpty(details.icd10Codes, icd10Codes, setIcd10Codes);
        setIfEmpty(details.physicianName, physicianName, setPhysicianName);
        setIfEmpty(details.practiceName, practiceName, setPracticeName);

        if (applied > 0) {
            setParsedDetailNotice(`Filled ${applied} detail${applied === 1 ? '' : 's'} from the clinical notes.`);
        }
    }

    const readFile = async (file: File) => {
        setFileName(file.name);
        setFileError('');
        setIsExtractingFile(true);
        try {
            if (/\.(txt|md|csv)$/i.test(file.name) || file.type.startsWith('text/')) {
                const text = await file.text();
                setClinicalNotes(text);
                setClinicalSufficiencyReport(null);
                applyClinicalNoteParsedDetails(text);
                return;
            }

            const response = await fetch('/api/clinical-notes/extract', {
                method: 'POST',
                headers: {
                    'content-type': file.type || 'application/octet-stream',
                    'x-file-name': file.name,
                },
                body: await file.arrayBuffer(),
            });
            const rawBody = await response.text();
            let data: { text?: string; error?: string } = {};
            try {
                data = rawBody ? JSON.parse(rawBody) : {};
            } catch {
                data = { error: rawBody || 'Unable to extract text from file.' };
            }
            if (!response.ok) throw new Error(data.error || 'Unable to extract text from file.');
            setClinicalNotes(data.text || '');
            setClinicalSufficiencyReport(null);
            applyClinicalNoteParsedDetails(data.text || '');
        } catch (err) {
            setClinicalNotes('');
            setFileError(err instanceof Error ? err.message : 'Unable to extract text from file.');
        } finally {
            setIsExtractingFile(false);
        }
    };

    const inferredDetails = useMemo(
        () => mergeDetails(parseDenialDetails(denialReason), parseClinicalNoteDetails(clinicalNotes)),
        [clinicalNotes, denialReason],
    );

    const applyParsedDetails = (details: ParsedDetails, overwrite = false) => {
        let applied = 0;
        const shouldApply = (value: string | undefined, current: string) => !!value && (overwrite || !current.trim());

        if (shouldApply(details.patientName, patientName)) { setPatientName(details.patientName!); applied += 1; }
        if (shouldApply(details.patientDOB, patientDOB)) { setPatientDOB(details.patientDOB!); applied += 1; }
        if (shouldApply(details.memberId, memberId)) { setMemberId(details.memberId!); applied += 1; }
        if (shouldApply(details.insuranceCompany, insuranceCompany)) { setInsuranceCompany(details.insuranceCompany!); applied += 1; }
        if (shouldApply(details.claimNumber, claimNumber)) { setClaimNumber(details.claimNumber!); applied += 1; }
        if (shouldApply(details.denialDate, denialDate)) { setDenialDate(details.denialDate!); applied += 1; }
        if (shouldApply(details.deniedService, deniedService)) { setDeniedService(details.deniedService!); applied += 1; }
        if (shouldApply(details.cptCodes, cptCodes)) { setCptCodes(details.cptCodes!); applied += 1; }
        if (shouldApply(details.icd10Codes, icd10Codes)) { setIcd10Codes(details.icd10Codes!); applied += 1; }
        if (shouldApply(details.physicianName, physicianName)) { setPhysicianName(details.physicianName!); applied += 1; }
        if (shouldApply(details.practiceName, practiceName)) { setPracticeName(details.practiceName!); applied += 1; }

        return applied;
    };

    useEffect(() => {
        if (!denialReason.trim()) return;
        const details = parseDenialDetails(denialReason);
        const found = Object.entries(details).filter(([key, value]) => key !== 'denialReason' && !!value).length;
        if (found === 0) return;
        const applied = applyParsedDetails(details, true);
        if (applied > 0) {
            setParsedDetailNotice(`Auto-filled ${applied} detail${applied === 1 ? '' : 's'} from the pasted denial.`);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [denialReason]);

    const buildAppealPayload = () => {
        const denialDetails = parseDenialDetails(denialReason);
        return {
            clinicalNotes,
            denialReason,
            deniedService: deniedService || inferredDetails.deniedService || '',
            cptCodes: denialDetails.cptCodes || cptCodes || inferredDetails.cptCodes || '',
            icd10Codes: denialDetails.icd10Codes || icd10Codes || inferredDetails.icd10Codes || '',
            insuranceCompany: insuranceCompany || inferredDetails.insuranceCompany || '',
            patientName: patientName || inferredDetails.patientName || '',
            patientDOB: patientDOB || inferredDetails.patientDOB || '',
            memberId: memberId || inferredDetails.memberId || '',
            claimNumber: claimNumber || inferredDetails.claimNumber || '',
            denialDate: denialDate || inferredDetails.denialDate || '',
            physicianName: physicianName || inferredDetails.physicianName || '',
            physicianNPI,
            practiceName: practiceName || inferredDetails.practiceName || '',
        };
    };

    const stageIdForEvent = (stage: string): string | null => {
        if (stage.startsWith('guidelines')) return 'guidelines';
        if (stage.startsWith('sufficiency')) return 'sufficiency';
        if (stage.startsWith('pubmed')) return 'pubmed';
        if (stage.startsWith('generation')) return 'generation';
        if (stage.startsWith('safety') || stage.startsWith('repair')) return 'safety';
        if (stage.startsWith('save') || stage === 'complete') return 'save';
        return null;
    };

    const updateGenerationStage = (stage: string, message: string, status?: GenerationStageStatus) => {
        const activeId = stageIdForEvent(stage);
        if (!activeId) return;
        const nextStatus = status || (stage.endsWith('_started') ? 'active' : stage === 'error' ? 'error' : 'done');
        setGenerationStages(prev => prev.map(item => {
            if (item.id === activeId) return { ...item, status: nextStatus, detail: message };
            if (nextStatus === 'active' && item.status === 'active') return { ...item, status: 'done' };
            return item;
        }));
        setLoadingStep(message);
    };

    const applyGeneratedAppealData = (data: {
        letter?: string;
        citations?: Citation[];
        ragSources?: RAGSource[];
        appealId?: string;
        webEvidence?: { source: string; title: string; citation: string; url: string }[];
        safetyReport?: SafetyReport;
        clinicalSufficiencyReport?: ClinicalSufficiencyReport;
    }) => {
        setGeneratedLetter(data.letter || '');
        setCitations(data.citations || []);
        setRagSources(data.ragSources || []);
        setAppealId(data.appealId || '');
        setWebEvidence(data.webEvidence || []);
        setSafetyReport(data.safetyReport || null);
        setClinicalSufficiencyReport(data.clinicalSufficiencyReport || null);
    };

    // Generate appeal
    const handleGenerate = async () => {
        setIsGenerating(true);
        setError('');
        setClinicalSufficiencyReport(null);
        setGenerationStages(DEFAULT_GENERATION_STAGES.map(stage => ({ ...stage })));
        setStep(3);
        setLoadingStep('Starting appeal generation...');

        try {
            const response = await fetch('/api/generate-appeal/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(buildAppealPayload()),
            });

            if (!response.ok || !response.body || !response.headers.get('content-type')?.includes('text/event-stream')) {
                const errData = await response.json().catch(() => ({ error: 'Failed to start appeal generation stream' }));
                if (errData.sufficiencyReport) {
                    setClinicalSufficiencyReport(errData.sufficiencyReport);
                    setStep(2);
                    return;
                }
                throw new Error(errData.error || 'Failed to generate appeal');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let completed = false;
            let streamAppealId = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                let separatorIndex = buffer.indexOf('\n\n');
                while (separatorIndex !== -1) {
                    const rawEvent = buffer.slice(0, separatorIndex).trim();
                    buffer = buffer.slice(separatorIndex + 2);
                    const dataLine = rawEvent.split('\n').find(line => line.startsWith('data: '));
                    if (dataLine) {
                        const event = JSON.parse(dataLine.slice(6)) as ProgressEventPayload;
                        updateGenerationStage(event.stage, event.message, event.stage === 'error' ? 'error' : undefined);

                        if (event.data?.appealId) {
                            streamAppealId = event.data.appealId as string;
                        }

                        if (event.stage === 'error') {
                            const report = event.data?.sufficiencyReport as ClinicalSufficiencyReport | undefined;
                            if (report) {
                                setClinicalSufficiencyReport(report);
                                setStep(2);
                                return;
                            }
                            throw new Error(event.message || 'Failed to generate appeal');
                        }

                        if (event.stage === 'complete') {
                            applyGeneratedAppealData(event.data || {});
                            updateGenerationStage('complete', event.message, 'done');
                            completed = true;
                        }
                    }
                    separatorIndex = buffer.indexOf('\n\n');
                }
            }

            if (!completed && streamAppealId) {
                updateGenerationStage('save_started', 'Stream interrupted — recovering result...', 'active');
                for (let attempt = 0; attempt < 10; attempt++) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    try {
                        const pollResp = await fetch(`/api/appeals/${streamAppealId}`);
                        if (!pollResp.ok) continue;
                        const appeal = await pollResp.json();
                        if (appeal.status === 'completed' || appeal.status === 'failed') {
                            applyGeneratedAppealData({
                                letter: appeal.generatedLetter,
                                citations: appeal.citations,
                                ragSources: appeal.ragSources,
                                appealId: appeal.id,
                                safetyReport: appeal.safetyReport,
                            });
                            updateGenerationStage('complete', 'Appeal recovered.', 'done');
                            completed = true;
                            break;
                        }
                    } catch { /* retry */ }
                }
            }

            if (!completed) {
                throw new Error('Generation stream ended before the appeal was completed.');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setIsGenerating(false);
            setLoadingStep('');
        }
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(generatedLetter);
        setCopied(true);
        setTimeout(() => setCopied(false), 3000);
    };

    const handleDownloadWord = async () => {
        if (!appealId) return;
        if (safetyReport?.verdict === 'FAIL') return;
        const response = await fetch(`/api/appeals/${appealId}/download`);
        if (!response.ok) return;
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `appeal-letter-${patientName.replace(/\s+/g, '-').toLowerCase()}.docx`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleVerify = async () => {
        setIsVerifying(true);
        try {
            const response = await fetch('/api/verify-appeal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    letter: generatedLetter,
                    clinicalNotes,
                    ragContext: '',
                    denialReason,
                    deniedService: deniedService || inferredDetails.deniedService || '',
                    cptCodes: cptCodes || inferredDetails.cptCodes || '',
                    icd10Codes: icd10Codes || inferredDetails.icd10Codes || '',
                }),
            });

            if (response.ok) {
                const data = await response.json();
                if (data.verification) {
                    setVerification(data.verification);
                }
            }
        } catch (err) {
            console.error('Verification failed:', err);
        } finally {
            setIsVerifying(false);
        }
    };

    const addCptCode = (code: MedicalCode) => {
        const existing = cptCodes ? cptCodes.split(',').map(c => c.trim()) : [];
        if (!existing.includes(code.code)) {
            setCptCodes(existing.length > 0 ? `${cptCodes}, ${code.code}` : code.code);
        }
        setCptSearch('');
        setShowCptResults(false);
    };

    const addIcd10Code = (code: MedicalCode) => {
        const existing = icd10Codes ? icd10Codes.split(',').map(c => c.trim()) : [];
        if (!existing.includes(code.code)) {
            setIcd10Codes(existing.length > 0 ? `${icd10Codes}, ${code.code}` : code.code);
        }
        setIcd10Search('');
        setShowIcd10Results(false);
    };

    const canProceedStep1 = clinicalNotes.trim().length > 50;
    const canProceedStep2 = Boolean(denialReason.trim()
        && (deniedService.trim() || inferredDetails.deniedService)
        && (patientName.trim() || inferredDetails.patientName));

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                {/* Header */}
                <div className="page-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                        <button
                            onClick={() => router.push('/')}
                            className="btn btn-ghost btn-icon"
                        >
                            <ArrowLeft size={18} />
                        </button>
                        <h1 className="page-title">
                            New Appeal Letter
                        </h1>
                    </div>
                    <p className="page-subtitle">
                        Upload clinical documentation, enter denial details, and generate a medically-cited appeal.
                    </p>
                </div>

                {/* Step Wizard Indicator */}
                <div className="wizard-steps">
                    <div className={`wizard-step ${step === 1 ? 'active' : step > 1 ? 'completed' : ''}`} onClick={() => step > 1 && !isGenerating && setStep(1)}>
                        <div className="wizard-step-number">{step > 1 ? <Check size={16} /> : '1'}</div>
                        <span className="wizard-step-label">Clinical Notes</span>
                    </div>
                    <div className={`wizard-step ${step === 2 ? 'active' : step > 2 ? 'completed' : ''}`} onClick={() => step > 2 && !isGenerating && setStep(2)}>
                        <div className="wizard-step-number">{step > 2 ? <Check size={16} /> : '2'}</div>
                        <span className="wizard-step-label">Denial Details</span>
                    </div>
                    <div className={`wizard-step ${step === 3 ? 'active' : ''}`}>
                        <div className="wizard-step-number">3</div>
                        <span className="wizard-step-label">Appeal Letter</span>
                    </div>
                </div>

                {/* ===== STEP 1: CLINICAL NOTES ===== */}
                {step === 1 && (
                    <div className="card" style={{ maxWidth: 800 }}>
                        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>Upload Clinical Notes</h2>
                        <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 24 }}>
                            Paste or upload the clinical documentation (physician notes, discharge summary, consultation report).
                        </p>

                        {/* File Upload Zone */}
                        <div
                            className={`file-upload-zone ${fileName ? 'has-file' : ''}`}
                            onDrop={handleFileDrop}
                            onDragOver={(e) => e.preventDefault()}
                            onClick={() => document.getElementById('file-input')?.click()}
                        >
                            <input
                                id="file-input"
                                type="file"
                                accept=".txt,.md,.csv,.docx,.pdf,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                onChange={handleFileSelect}
                                style={{ display: 'none' }}
                            />
                            {fileName ? (
                                <>
                                    <FileText size={36} color="var(--evidence-green)" className="file-upload-icon" />
                                    <div className="file-upload-text">
                                        <strong>{fileName}</strong> uploaded
                                    </div>
                                    <div className="file-upload-hint">{isExtractingFile ? 'Extracting text...' : 'Click to upload a different file'}</div>
                                </>
                            ) : (
                                <>
                                    <Upload size={36} className="file-upload-icon" />
                                    <div className="file-upload-text">
                                        <strong>Click to upload</strong> or drag and drop
                                    </div>
                                    <div className="file-upload-hint">TXT, MD, CSV, DOCX, and text-based PDF files supported</div>
                                </>
                            )}
                        </div>
                        <div style={{ fontSize: 12, color: fileError ? 'var(--evidence-red)' : 'var(--text-muted)', marginTop: 8 }}>
                            {fileError || 'Supported uploads: TXT, MD, CSV, DOCX, and text-based PDF. Scanned PDFs need OCR first.'}
                        </div>

                        <div className="divider">or paste clinical notes below</div>

                        {/* Text area */}
                        <div className="form-group">
                            <textarea
                                className="form-textarea"
                                placeholder="Paste the clinical note, discharge summary, or consultation report here..."
                                value={clinicalNotes}
                                onChange={(e) => {
                                    setClinicalNotes(e.target.value);
                                    setClinicalSufficiencyReport(null);
                                }}
                                style={{ minHeight: 300, fontFamily: 'var(--font-mono)', fontSize: 13, lineHeight: 1.7 }}
                            />
                            <div className="form-helper">
                                {clinicalNotes.length > 0 ? `${clinicalNotes.length.toLocaleString()} characters` : 'Minimum 50 characters required'}
                            </div>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                            <button
                                className="btn btn-primary"
                                disabled={!canProceedStep1 || isExtractingFile}
                                onClick={() => {
                                    applyClinicalNoteParsedDetails(clinicalNotes);
                                    setStep(2);
                                }}
                            >
                                Continue <ChevronRight size={16} />
                            </button>
                        </div>
                    </div>
                )}

                {/* ===== STEP 2: DENIAL DETAILS ===== */}
                {step === 2 && (
                    <div className="card" style={{ maxWidth: 800 }}>
                        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>Denial Details</h2>
                        <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 24 }}>
                            Enter fields manually, or paste a full payer denial block and parse the details.
                        </p>

                        {clinicalSufficiencyReport && (
                            <div style={{
                                border: '1px solid var(--evidence-amber)',
                                background: 'var(--evidence-amber-soft)',
                                borderRadius: 8,
                                padding: 14,
                                marginBottom: 20,
                            }}>
                                <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                                    <AlertCircle size={18} color="var(--evidence-amber)" style={{ marginTop: 1, flexShrink: 0 }} />
                                    <div>
                                        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--evidence-amber)', marginBottom: 4 }}>
                                            Clinical notes need more support before generation
                                        </div>
                                        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>
                                            {clinicalSufficiencyReport.summary} Score: {clinicalSufficiencyReport.score}/100.
                                        </div>
                                        {clinicalSufficiencyReport.blockingReasons.length > 0 && (
                                            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8 }}>
                                                <strong>Blocking issue:</strong> {clinicalSufficiencyReport.blockingReasons.join(' ')}
                                            </div>
                                        )}
                                        {clinicalSufficiencyReport.suggestions.length > 0 && (
                                            <ul style={{ margin: '8px 0 0 18px', padding: 0, fontSize: 12, color: 'var(--text-secondary)' }}>
                                                {clinicalSufficiencyReport.suggestions.slice(0, 5).map((suggestion, i) => (
                                                    <li key={i} style={{ marginBottom: 4 }}>{suggestion}</li>
                                                ))}
                                            </ul>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Patient Info */}
                        <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Patient Information
                        </h3>
                        <div className="form-grid-2">
                            <div className="form-group">
                                <label className="form-label">Patient Name *</label>
                                <input className="form-input" value={patientName} onChange={e => setPatientName(e.target.value)} placeholder="Full Name" />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Date of Birth</label>
                                <input className="form-input" value={patientDOB} onChange={e => setPatientDOB(e.target.value)} placeholder="MM/DD/YYYY" />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Member ID</label>
                                <input className="form-input" value={memberId} onChange={e => setMemberId(e.target.value)} placeholder="Insurance Member ID" />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Insurance Company</label>
                                <input className="form-input" value={insuranceCompany} onChange={e => setInsuranceCompany(e.target.value)} placeholder="e.g. UnitedHealthcare, Aetna" />
                            </div>
                        </div>

                        {/* Denial Info */}
                        <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)', marginBottom: 12, marginTop: 24, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Denial Information
                        </h3>
                        <div className="form-grid-2">
                            <div className="form-group">
                                <label className="form-label">Claim/Reference Number</label>
                                <input className="form-input" value={claimNumber} onChange={e => setClaimNumber(e.target.value)} placeholder="Claim or PA Reference Number" />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Denial Date</label>
                                <input className="form-input" value={denialDate} onChange={e => setDenialDate(e.target.value)} placeholder="MM/DD/YYYY" />
                            </div>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Denied Service *</label>
                            <input className="form-input" value={deniedService} onChange={e => setDeniedService(e.target.value)} placeholder="e.g. Total Knee Arthroplasty, Right" />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Denial Reason / Full Denial Details *</label>
                            <textarea
                                className="form-textarea"
                                value={denialReason}
                                onChange={e => {
                                    setDenialReason(e.target.value);
                                    setParsedDetailNotice('');
                                    setClinicalSufficiencyReport(null);
                                }}
                                placeholder="Paste the exact denial reason or the full payer denial details block, including plan criteria, missing documentation, appeal deadline, and recommended appeal focus..."
                                style={{ minHeight: 160 }}
                            />
                            {parsedDetailNotice && (
                                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
                                    {parsedDetailNotice}
                                </div>
                            )}
                        </div>

                        {/* Medical Codes */}
                        <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)', marginBottom: 12, marginTop: 24, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Medical Codes
                        </h3>
                        <div className="form-grid-2">
                            {/* CPT Code Autocomplete */}
                            <div className="form-group">
                                <label className="form-label">CPT Code(s)</label>
                                <input className="form-input" value={cptCodes} onChange={e => setCptCodes(e.target.value)} placeholder="e.g. 27447" />
                                <div className="code-autocomplete" ref={cptRef}>
                                    <div style={{ position: 'relative', marginTop: 6 }}>
                                        <Search size={14} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--text-muted)' }} />
                                        <input
                                            className="form-input"
                                            style={{ paddingLeft: 30, fontSize: 13 }}
                                            value={cptSearch}
                                            onChange={e => setCptSearch(e.target.value)}
                                            placeholder="Search CPT codes..."
                                            onFocus={() => cptResults.length > 0 && setShowCptResults(true)}
                                        />
                                    </div>
                                    {showCptResults && cptResults.length > 0 && (
                                        <div className="code-results">
                                            {cptResults.map(c => (
                                                <div key={c.code} className="code-result-item" onClick={() => addCptCode(c)}>
                                                    <span className="code-result-code">{c.code}</span>
                                                    <span className="code-result-desc">{c.description}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* ICD-10 Code Autocomplete */}
                            <div className="form-group">
                                <label className="form-label">ICD-10 Diagnosis Code(s)</label>
                                <input className="form-input" value={icd10Codes} onChange={e => setIcd10Codes(e.target.value)} placeholder="e.g. M17.11" />
                                <div className="code-autocomplete" ref={icd10Ref}>
                                    <div style={{ position: 'relative', marginTop: 6 }}>
                                        <Search size={14} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--text-muted)' }} />
                                        <input
                                            className="form-input"
                                            style={{ paddingLeft: 30, fontSize: 13 }}
                                            value={icd10Search}
                                            onChange={e => setIcd10Search(e.target.value)}
                                            placeholder="Search ICD-10 codes..."
                                            onFocus={() => icd10Results.length > 0 && setShowIcd10Results(true)}
                                        />
                                    </div>
                                    {showIcd10Results && icd10Results.length > 0 && (
                                        <div className="code-results">
                                            {icd10Results.map(c => (
                                                <div key={c.code} className="code-result-item" onClick={() => addIcd10Code(c)}>
                                                    <span className="code-result-code">{c.code}</span>
                                                    <span className="code-result-desc">{c.description}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Physician Info */}
                        <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)', marginBottom: 12, marginTop: 24, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Physician Information
                        </h3>
                        <div className="form-grid-2">
                            <div className="form-group">
                                <label className="form-label">Physician Name</label>
                                <input className="form-input" value={physicianName} onChange={e => setPhysicianName(e.target.value)} placeholder="Dr. Name, MD" />
                            </div>
                            <div className="form-group">
                                <label className="form-label">NPI</label>
                                <input className="form-input" value={physicianNPI} onChange={e => setPhysicianNPI(e.target.value)} placeholder="10-digit NPI" />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Practice Name</label>
                                <input className="form-input" value={practiceName} onChange={e => setPracticeName(e.target.value)} placeholder="Your Practice Name" />
                            </div>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginTop: 8 }}>
                            <button className="btn btn-secondary" onClick={() => setStep(1)}>
                                <ChevronLeft size={16} /> Back
                            </button>
                            <button
                                className="btn btn-primary btn-lg"
                                disabled={!canProceedStep2}
                                onClick={handleGenerate}
                            >
                                Generate Appeal Letter
                            </button>
                        </div>
                    </div>
                )}

                {/* ===== STEP 3: RESULT ===== */}
                {step === 3 && (
                    <>
                        {isGenerating ? (
                            <div className="loading-container">
                                <div className="loading-pulse">
                                    <div className="loading-pulse-dot" />
                                    <div className="loading-pulse-dot" />
                                    <div className="loading-pulse-dot" />
                                </div>
                                <div className="loading-text">{loadingStep || 'Generating appeal letter...'}</div>
                                <div className="loading-subtext">
                                    Analyzing clinical notes, retrieving medical guidelines, and drafting your appeal.
                                    <br />This may take 15-30 seconds.
                                </div>
                                <div className="generation-track">
                                    {generationStages.map(stageItem => (
                                        <div
                                            key={stageItem.id}
                                            style={{
                                                display: 'grid',
                                                gridTemplateColumns: '24px 1fr',
                                                gap: 10,
                                                alignItems: 'start',
                                                padding: '8px 0',
                                                borderBottom: '1px solid var(--border)',
                                            }}
                                        >
                                            <div style={{
                                                width: 20,
                                                height: 20,
                                                borderRadius: '50%',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                border: `1px solid ${stageItem.status === 'done' ? 'var(--color-success)' : stageItem.status === 'error' ? 'var(--color-danger)' : 'var(--border)'}`,
                                                color: stageItem.status === 'done' ? 'var(--color-success)' : stageItem.status === 'error' ? 'var(--color-danger)' : 'var(--text-muted)',
                                                fontSize: 11,
                                            }}>
                                                {stageItem.status === 'done' ? <Check size={13} /> : stageItem.status === 'error' ? '!' : stageItem.status === 'active' ? '...' : ''}
                                            </div>
                                            <div>
                                                <div style={{ fontSize: 13, fontWeight: 700, color: stageItem.status === 'active' ? 'var(--accent)' : 'var(--text-primary)' }}>
                                                    {stageItem.label}
                                                </div>
                                                {stageItem.detail && (
                                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                                                        {stageItem.detail}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : error ? (
                            <div className="card" style={{ maxWidth: 600, textAlign: 'center', padding: 48 }}>
                                <AlertCircle size={48} color="var(--color-danger)" style={{ marginBottom: 16 }} />
                                <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Generation Failed</h2>
                                <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>{error}</p>
                                <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
                                    <button className="btn btn-secondary" onClick={() => setStep(2)}>
                                        <ChevronLeft size={16} /> Edit Details
                                    </button>
                                    <button className="btn btn-primary" onClick={handleGenerate}>
                                        Try Again
                                    </button>
                                </div>
                            </div>
                        ) : generatedLetter ? (
                            <>
                                <div className="result-actions">
                                    <button className="btn btn-secondary" onClick={() => setStep(2)}>
                                        <ChevronLeft size={16} /> Edit & Regenerate
                                    </button>
                                    <button className="btn btn-secondary" onClick={handleCopy}>
                                        {copied ? <Check size={16} /> : <ClipboardCopy size={16} />}
                                        {copied ? 'Copied!' : 'Copy Letter'}
                                    </button>
                                    <button className="btn btn-secondary" onClick={handleDownloadWord} disabled={safetyReport?.verdict === 'FAIL'}>
                                        <Download size={16} /> Download Word
                                    </button>
                                    {!verification && (
                                        <button
                                            className="btn btn-secondary"
                                            onClick={handleVerify}
                                            disabled={isVerifying}
                                        >
                                            {isVerifying ? 'Verifying...' : 'Verify Accuracy'}
                                        </button>
                                    )}
                                    <button className="btn btn-primary" onClick={() => router.push('/')}>
                                        <Check size={16} /> Done
                                    </button>
                                </div>

                                <div className="result-layout">
                                    {safetyReport && (
                                        <div style={{ gridColumn: '1 / -1', padding: '12px 14px', border: '1px solid var(--border)', borderRadius: 8, background: safetyReport.verdict === 'PASS' ? 'var(--evidence-green-soft)' : safetyReport.verdict === 'NEEDS_REVIEW' ? 'var(--evidence-amber-soft)' : 'var(--evidence-red-soft)' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', marginBottom: safetyReport.issues.length ? 8 : 0 }}>
                                                <div style={{ fontSize: 13, fontWeight: 700, color: safetyReport.verdict === 'PASS' ? 'var(--evidence-green)' : safetyReport.verdict === 'NEEDS_REVIEW' ? 'var(--evidence-amber)' : 'var(--evidence-red)' }}>
                                                    Safety: {safetyReport.verdict === 'PASS' ? 'Pass' : safetyReport.verdict === 'NEEDS_REVIEW' ? 'Needs Review' : 'Failed'}
                                                    {safetyReport.repairAttempted ? ' after repair attempt' : ''}
                                                </div>
                                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                                    {safetyReport.structuredAnalysis?.criteria?.filter(c => c.status === 'met').length || 0} criteria matched
                                                </div>
                                            </div>
                                            {safetyReport.issues.slice(0, 5).map((issue, i) => (
                                                <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                                                    <strong>{issue.severity.toUpperCase()}:</strong> {issue.message}{issue.evidence ? ` (${issue.evidence})` : ''}
                                                </div>
                                            ))}
                                            {safetyReport.structuredAnalysis?.documentationGaps?.slice(0, 4).map((gap, i) => (
                                                <div key={`gap-${i}`} style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                                                    <strong>Gap:</strong> {gap}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    {/* Letter */}
                                    <div className="letter-container">
                                        <ReactMarkdown>{generatedLetter}</ReactMarkdown>
                                    </div>

                                    {/* Citations Sidebar */}
                                    <div className="citation-sidebar">
                                        <h3 style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>
                                            Coverage Criteria Used
                                        </h3>
                                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
                                            Medical necessity policies and guideline criteria used in this letter.
                                        </p>

                                        {citations.map(c => (
                                            <div key={c.index} className="citation-item">
                                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                                                    <span className="citation-index">{c.index}</span>
                                                    <div>
                                                        <div className="citation-title">{c.title}</div>
                                                        <div className="citation-source">{c.source}</div>
                                                    </div>
                                                </div>
                                                <p className="citation-text">{c.text}</p>
                                            </div>
                                        ))}

                                        {webEvidence.length > 0 && (
                                            <>
                                                <h3 style={{ fontSize: 14, fontWeight: 500, marginTop: 20, marginBottom: 4 }}>
                                                    PubMed Literature
                                                </h3>
                                                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
                                                    Peer-reviewed studies retrieved from PubMed. Items marked retrieved only were not cited in the letter.
                                                </p>
                                                {webEvidence.map((e, i) => (
                                                    <div key={i} className="citation-item">
                                                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                                                            <span className="citation-index">P{i + 1}</span>
                                                            <div>
                                                                <div className="citation-title">{e.title}</div>
                                                                <div style={{ fontSize: 11, fontWeight: 700, color: generatedLetter.includes(`[PubMed ${i + 1}]`) ? 'var(--evidence-green)' : 'var(--text-muted)', marginTop: 2 }}>
                                                                    {generatedLetter.includes(`[PubMed ${i + 1}]`) ? 'Cited in letter' : 'Retrieved only'}
                                                                </div>
                                                                <div className="citation-source">{e.citation}</div>
                                                                <a
                                                                    href={e.url}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    style={{ fontSize: 11, color: 'var(--evidence-blue)', textDecoration: 'none' }}
                                                                >
                                                                    View on PubMed
                                                                </a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </>
                                        )}

                                        {ragSources.length > 0 && (
                                            <div style={{ marginTop: 16, padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                                                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                                                    Relevance Scores
                                                </div>
                                                {ragSources.map((s, i) => (
                                                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, padding: '4px 0', borderBottom: '1px solid var(--border)' }}>
                                                        <span style={{ color: 'var(--text-secondary)', maxWidth: '70%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                            {s.title.split('—')[1]?.trim() || s.title}
                                                        </span>
                                                        <span style={{ fontWeight: 700, color: s.relevanceScore > 0.7 ? 'var(--evidence-green)' : s.relevanceScore > 0.4 ? 'var(--evidence-amber)' : 'var(--text-muted)' }}>
                                                            {(s.relevanceScore * 100).toFixed(0)}%
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {safetyReport?.structuredAnalysis?.policyMetadata && safetyReport.structuredAnalysis.policyMetadata.length > 0 && (
                                            <div style={{ marginTop: 16, padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                                                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                                                    Policy Freshness
                                                </div>
                                                {safetyReport.structuredAnalysis.policyMetadata.map((p, i) => (
                                                    <div key={i} style={{ fontSize: 12, padding: '4px 0', borderBottom: '1px solid var(--border)' }}>
                                                        <div style={{ fontWeight: 600 }}>{p.title}</div>
                                                        <div style={{ color: 'var(--text-muted)' }}>
                                                            {p.source} · Effective {p.effectiveDate} · <span style={{ fontWeight: 700, color: p.freshnessStatus === 'current' ? 'var(--evidence-green)' : p.freshnessStatus === 'review_due' ? 'var(--evidence-amber)' : 'var(--evidence-red)' }}>{p.freshnessStatus.replace('_', ' ')}</span>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Verification Panel */}
                                    {verification && (
                                        <div style={{ gridColumn: '1 / -1', marginTop: 24 }}>
                                            <h3 style={{ fontSize: 14, fontWeight: 500, marginBottom: 12, fontFamily: 'var(--font-display)' }}>
                                                Accuracy Verification
                                            </h3>
                                            <div style={{
                                                display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16,
                                                padding: '8px 12px', borderRadius: 6,
                                                background: verification.overallVerdict === 'PASS' ? 'var(--evidence-green-soft)' : verification.overallVerdict === 'NEEDS_REVIEW' ? 'var(--evidence-amber-soft)' : 'var(--evidence-red-soft)',
                                            }}>
                                                <span style={{
                                                    fontSize: 13, fontWeight: 600,
                                                    color: verification.overallVerdict === 'PASS' ? 'var(--evidence-green)'
                                                        : verification.overallVerdict === 'NEEDS_REVIEW' ? 'var(--evidence-amber)'
                                                            : 'var(--evidence-red)',
                                                }}>
                                                    {verification.overallVerdict === 'PASS' ? '✓ Verified'
                                                        : verification.overallVerdict === 'NEEDS_REVIEW' ? '⚠ Needs Review'
                                                            : '✗ Issues Found'}
                                                </span>
                                                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                                                    — Confidence: {(verification.confidenceScore * 100).toFixed(0)}%
                                                </span>
                                            </div>

                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                                {verification.checks?.map((c, i) => (
                                                    <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 13 }}>
                                                        <span style={{
                                                            flexShrink: 0, width: 18, height: 18, borderRadius: '50%',
                                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                            fontSize: 10, marginTop: 1,
                                                            background: c.status === 'PASS' ? 'var(--evidence-green-soft)' : c.status === 'WARNING' ? 'var(--evidence-amber-soft)' : 'var(--evidence-red-soft)',
                                                            color: c.status === 'PASS' ? 'var(--evidence-green)'
                                                                : c.status === 'WARNING' ? 'var(--evidence-amber)'
                                                                    : 'var(--evidence-red)',
                                                        }}>
                                                            {c.status === 'PASS' ? '✓' : c.status === 'WARNING' ? '!' : '✗'}
                                                        </span>
                                                        <div>
                                                            <span style={{ fontWeight: 500 }}>{c.check}</span>
                                                            <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{c.details}</p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>

                                            {verification.flaggedIssues?.length > 0 && (
                                                <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--evidence-red-soft)', borderRadius: 6 }}>
                                                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--evidence-red)', textTransform: 'uppercase', marginBottom: 6 }}>Flagged Issues</div>
                                                    {verification.flaggedIssues.map((issue, i) => (
                                                        <p key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4 }}>• {issue}</p>
                                                    ))}
                                                </div>
                                            )}

                                            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 10, fontStyle: 'italic' }}>
                                                {verification.summary}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </>
                        ) : null}
                    </>
                )}
            </main>
        </div>
    );
}

export default function NewAppealPage() {
    return (
        <Suspense fallback={
            <div className="app-layout">
                <Sidebar />
                <main className="main-content">
                    <div className="loading-container">
                        <div className="loading-spinner" />
                        <div className="loading-text">Loading...</div>
                    </div>
                </main>
            </div>
        }>
            <NewAppealContent />
        </Suspense>
    );
}
