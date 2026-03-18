'use client';

import { useState, useCallback, useEffect, useRef, Suspense } from 'react';
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
    X,
    ClipboardCopy,
    Download,
    ArrowLeft,
} from 'lucide-react';
import { SAMPLE_CASES } from '@/lib/sample-data';

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

// Separate component that uses useSearchParams
function NewAppealContent() {
    const router = useRouter();
    const searchParams = useSearchParams();

    const [step, setStep] = useState(1);

    // Step 1: Clinical Notes
    const [clinicalNotes, setClinicalNotes] = useState('');
    const [fileName, setFileName] = useState('');

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
    const [copied, setCopied] = useState(false);
    const [loadingStep, setLoadingStep] = useState('');
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
    const handleFileDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file) readFile(file);
    }, []);

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) readFile(file);
    }, []);

    const readFile = (file: File) => {
        setFileName(file.name);
        const reader = new FileReader();
        reader.onload = (e) => {
            setClinicalNotes(e.target?.result as string || '');
        };
        reader.readAsText(file);
    };

    // Generate appeal
    const handleGenerate = async () => {
        setIsGenerating(true);
        setError('');
        setStep(3);
        setLoadingStep('Searching medical guidelines...');

        try {
            setTimeout(() => setLoadingStep('Retrieving PubMed evidence...'), 3000);
            setTimeout(() => setLoadingStep('Generating appeal letter...'), 7000);

            const response = await fetch('/api/generate-appeal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    clinicalNotes,
                    denialReason,
                    deniedService,
                    cptCodes,
                    icd10Codes,
                    insuranceCompany,
                    patientName,
                    patientDOB,
                    memberId,
                    claimNumber,
                    denialDate,
                    physicianName,
                    physicianNPI,
                    practiceName,
                }),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Failed to generate appeal');
            }

            const data = await response.json();
            setGeneratedLetter(data.letter);
            setCitations(data.citations || []);
            setRagSources(data.ragSources || []);
            setAppealId(data.appealId);
            setWebEvidence(data.webEvidence || []);
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

    const handleDownload = () => {
        const blob = new Blob([generatedLetter], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `appeal-letter-${patientName.replace(/\s+/g, '-').toLowerCase()}.md`;
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
                    ragContext: ragSources.map(s => s.title).join('\n'),
                    denialReason,
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
    const canProceedStep2 = denialReason.trim() && deniedService.trim() && patientName.trim();

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
                                accept=".txt,.md,.doc,.docx,.pdf"
                                onChange={handleFileSelect}
                                style={{ display: 'none' }}
                            />
                            {fileName ? (
                                <>
                                    <FileText size={36} color="#2d8e47" className="file-upload-icon" />
                                    <div className="file-upload-text">
                                        <strong>{fileName}</strong> uploaded
                                    </div>
                                    <div className="file-upload-hint">Click to upload a different file</div>
                                </>
                            ) : (
                                <>
                                    <Upload size={36} className="file-upload-icon" />
                                    <div className="file-upload-text">
                                        <strong>Click to upload</strong> or drag and drop
                                    </div>
                                    <div className="file-upload-hint">TXT, MD, DOC files supported</div>
                                </>
                            )}
                        </div>

                        <div className="divider">or paste clinical notes below</div>

                        {/* Text area */}
                        <div className="form-group">
                            <textarea
                                className="form-textarea"
                                placeholder="Paste the clinical note, discharge summary, or consultation report here..."
                                value={clinicalNotes}
                                onChange={(e) => setClinicalNotes(e.target.value)}
                                style={{ minHeight: 300, fontFamily: "'SF Mono', Menlo, monospace", fontSize: 13, lineHeight: 1.7 }}
                            />
                            <div className="form-helper">
                                {clinicalNotes.length > 0 ? `${clinicalNotes.length.toLocaleString()} characters` : 'Minimum 50 characters required'}
                            </div>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                            <button
                                className="btn btn-primary"
                                disabled={!canProceedStep1}
                                onClick={() => setStep(2)}
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
                            Enter the insurance denial information and patient details.
                        </p>

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
                            <label className="form-label">Reason for Denial *</label>
                            <textarea
                                className="form-textarea"
                                value={denialReason}
                                onChange={e => setDenialReason(e.target.value)}
                                placeholder="Paste the exact denial reason from the insurance company's letter..."
                                style={{ minHeight: 100 }}
                            />
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
                            </div>
                        ) : error ? (
                            <div className="card" style={{ maxWidth: 600, textAlign: 'center', padding: 48 }}>
                                <AlertCircle size={48} color="#c53030" style={{ marginBottom: 16 }} />
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
                                    <button className="btn btn-secondary" onClick={handleDownload}>
                                        <Download size={16} /> Download Markdown
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
                                    {/* Letter */}
                                    <div className="letter-container">
                                        <ReactMarkdown>{generatedLetter}</ReactMarkdown>
                                    </div>

                                    {/* Citations Sidebar */}
                                    <div className="citation-sidebar">
                                        <h3 style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>
                                            RAG Sources
                                        </h3>
                                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
                                            Medical guidelines retrieved and cited in this letter.
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
                                                    Peer-reviewed studies retrieved from PubMed.
                                                </p>
                                                {webEvidence.map((e, i) => (
                                                    <div key={i} className="citation-item">
                                                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                                                            <span className="citation-index" style={{ background: 'rgba(59,130,246,0.1)', color: '#3b82f6' }}>P{i + 1}</span>
                                                            <div>
                                                                <div className="citation-title">{e.title}</div>
                                                                <div className="citation-source">{e.citation}</div>
                                                                <a
                                                                    href={e.url}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    style={{ fontSize: 11, color: '#3b82f6', textDecoration: 'none' }}
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
                                                        <span style={{ fontWeight: 700, color: s.relevanceScore > 0.7 ? '#2d8e47' : s.relevanceScore > 0.4 ? '#b8860b' : 'var(--text-muted)' }}>
                                                            {(s.relevanceScore * 100).toFixed(0)}%
                                                        </span>
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
                                                background: verification.overallVerdict === 'PASS' ? 'rgba(45,142,71,0.08)'
                                                    : verification.overallVerdict === 'NEEDS_REVIEW' ? 'rgba(184,134,11,0.08)'
                                                        : 'rgba(197,48,48,0.08)',
                                            }}>
                                                <span style={{
                                                    fontSize: 13, fontWeight: 600,
                                                    color: verification.overallVerdict === 'PASS' ? '#2d8e47'
                                                        : verification.overallVerdict === 'NEEDS_REVIEW' ? '#a67c00'
                                                            : '#c53030',
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
                                                            background: c.status === 'PASS' ? 'rgba(45,142,71,0.1)'
                                                                : c.status === 'WARNING' ? 'rgba(184,134,11,0.1)'
                                                                    : 'rgba(197,48,48,0.1)',
                                                            color: c.status === 'PASS' ? '#2d8e47'
                                                                : c.status === 'WARNING' ? '#a67c00'
                                                                    : '#c53030',
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
                                                <div style={{ marginTop: 12, padding: '10px 12px', background: 'rgba(197,48,48,0.05)', borderRadius: 6 }}>
                                                    <div style={{ fontSize: 11, fontWeight: 600, color: '#c53030', textTransform: 'uppercase', marginBottom: 6 }}>Flagged Issues</div>
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
