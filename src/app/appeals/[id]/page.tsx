'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import ReactMarkdown from 'react-markdown';
import {
    ArrowLeft,
    ClipboardCopy,
    Download,
    Check,
    Sparkles,
    Clock,
    User,
    Building2,
    FileText,
    AlertCircle,
} from 'lucide-react';

interface Appeal {
    id: string;
    status: string;
    patientName: string;
    patientDOB: string;
    memberId: string;
    insuranceCompany: string;
    claimNumber: string;
    denialDate: string;
    denialReason: string;
    deniedService: string;
    cptCodes: string;
    icd10Codes: string;
    physicianName: string;
    physicianNPI: string;
    practiceName: string;
    clinicalNotes: string;
    generatedLetter: string | null;
    citations: Array<{ index: number; guidelineId: string; title: string; source: string; text: string }> | null;
    ragSources: Array<{ guidelineId: string; title: string; source: string; relevanceScore: number }> | null;
    safetyReport: {
        verdict: 'PASS' | 'NEEDS_REVIEW' | 'FAIL';
        issues: Array<{ code: string; severity: 'error' | 'warning'; message: string; evidence?: string }>;
        structuredAnalysis?: {
            documentationGaps?: string[];
            policyMetadata?: Array<{ title: string; source: string; effectiveDate: string; freshnessStatus: string }>;
            criteria?: Array<{ status: 'met' | 'unclear' | 'not_met' }>;
        };
        repairAttempted?: boolean;
    } | null;
    createdAt: string;
}

export default function AppealDetailPage() {
    const params = useParams();
    const router = useRouter();
    const [appeal, setAppeal] = useState<Appeal | null>(null);
    const [loading, setLoading] = useState(true);
    const [copied, setCopied] = useState(false);
    const [activeTab, setActiveTab] = useState<'letter' | 'notes' | 'denial'>('letter');

    useEffect(() => {
        fetch(`/api/appeals/${params.id}`)
            .then(r => {
                if (!r.ok) throw new Error('Not found');
                return r.json();
            })
            .then(data => {
                setAppeal(data);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, [params.id]);

    const handleCopy = () => {
        if (appeal?.generatedLetter) {
            navigator.clipboard.writeText(appeal.generatedLetter);
            setCopied(true);
            setTimeout(() => setCopied(false), 3000);
        }
    };

    const handleDownload = async () => {
        if (!appeal?.generatedLetter) return;
        if (appeal.safetyReport?.verdict === 'FAIL') return;
        const response = await fetch(`/api/appeals/${appeal.id}/download`);
        if (!response.ok) return;
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `appeal-letter-${appeal.patientName.replace(/\s+/g, '-').toLowerCase()}.docx`;
        a.click();
        URL.revokeObjectURL(url);
    };

    if (loading) {
        return (
            <div className="app-layout">
                <Sidebar />
                <main className="main-content">
                    <div className="loading-container">
                        <div className="loading-spinner" />
                        <div className="loading-text">Loading appeal...</div>
                    </div>
                </main>
            </div>
        );
    }

    if (!appeal) {
        return (
            <div className="app-layout">
                <Sidebar />
                <main className="main-content">
                    <div className="empty-state">
                        <AlertCircle size={48} className="empty-state-icon" />
                        <h3 className="empty-state-title">Appeal not found</h3>
                        <p className="empty-state-text">This appeal may have been deleted.</p>
                        <button className="btn btn-primary" onClick={() => router.push('/appeals')}>
                            Back to History
                        </button>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                {/* Header */}
                <div className="page-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                        <button onClick={() => router.push('/appeals')} className="btn btn-ghost btn-icon">
                            <ArrowLeft size={18} />
                        </button>
                        <div>
                            <h1 className="page-title" style={{ fontSize: 22 }}>
                                Appeal for {appeal.patientName}
                            </h1>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 4 }}>
                                <span className={`status-badge ${appeal.status}`}>{appeal.status}</span>
                                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                                    <Clock size={13} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
                                    {new Date(appeal.createdAt).toLocaleDateString()} at {new Date(appeal.createdAt).toLocaleTimeString()}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Quick Info Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, marginBottom: 24 }}>
                    <div className="card" style={{ padding: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                            <User size={14} color="var(--accent-primary)" />
                            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Patient</span>
                        </div>
                        <div style={{ fontSize: 14, fontWeight: 600 }}>{appeal.patientName}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>DOB: {appeal.patientDOB || 'N/A'}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>ID: {appeal.memberId || 'N/A'}</div>
                    </div>
                    <div className="card" style={{ padding: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                            <Building2 size={14} color="var(--accent-primary)" />
                            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Insurance</span>
                        </div>
                        <div style={{ fontSize: 14, fontWeight: 600 }}>{appeal.insuranceCompany || 'N/A'}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Claim: {appeal.claimNumber || 'N/A'}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Denied: {appeal.denialDate || 'N/A'}</div>
                    </div>
                    <div className="card" style={{ padding: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                            <FileText size={14} color="var(--accent-primary)" />
                            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Service</span>
                        </div>
                        <div style={{ fontSize: 14, fontWeight: 600 }}>{appeal.deniedService}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>CPT: {appeal.cptCodes || 'N/A'}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>ICD-10: {appeal.icd10Codes || 'N/A'}</div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="tabs">
                    <button className={`tab ${activeTab === 'letter' ? 'active' : ''}`} onClick={() => setActiveTab('letter')}>
                        Appeal Letter
                    </button>
                    <button className={`tab ${activeTab === 'notes' ? 'active' : ''}`} onClick={() => setActiveTab('notes')}>
                        Clinical Notes
                    </button>
                    <button className={`tab ${activeTab === 'denial' ? 'active' : ''}`} onClick={() => setActiveTab('denial')}>
                        Denial Details
                    </button>
                </div>

                {/* Tab Content */}
                {activeTab === 'letter' && appeal.generatedLetter && (
                    <>
                        <div className="result-actions">
                            <button className="btn btn-secondary btn-sm" onClick={handleCopy}>
                                {copied ? <Check size={14} /> : <ClipboardCopy size={14} />}
                                {copied ? 'Copied!' : 'Copy'}
                            </button>
                            <button className="btn btn-secondary btn-sm" onClick={handleDownload} disabled={appeal.safetyReport?.verdict === 'FAIL'}>
                                <Download size={14} /> Download
                            </button>
                        </div>
                        <div className="result-layout">
                            {appeal.safetyReport && (
                                <div style={{ gridColumn: '1 / -1', padding: '12px 14px', border: '1px solid var(--border)', borderRadius: 8, background: appeal.safetyReport.verdict === 'PASS' ? 'rgba(45,142,71,0.06)' : appeal.safetyReport.verdict === 'NEEDS_REVIEW' ? 'rgba(184,134,11,0.06)' : 'rgba(197,48,48,0.06)' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', marginBottom: 8 }}>
                                        <div style={{ fontSize: 13, fontWeight: 700, color: appeal.safetyReport.verdict === 'PASS' ? '#2d8e47' : appeal.safetyReport.verdict === 'NEEDS_REVIEW' ? '#a67c00' : '#c53030' }}>
                                            Safety: {appeal.safetyReport.verdict === 'PASS' ? 'Pass' : appeal.safetyReport.verdict === 'NEEDS_REVIEW' ? 'Needs Review' : 'Failed'}
                                            {appeal.safetyReport.repairAttempted ? ' after repair attempt' : ''}
                                        </div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                            {appeal.safetyReport.structuredAnalysis?.criteria?.filter(c => c.status === 'met').length || 0} criteria matched
                                        </div>
                                    </div>
                                    {appeal.safetyReport.issues?.slice(0, 5).map((issue, i) => (
                                        <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                                            <strong>{issue.severity.toUpperCase()}:</strong> {issue.message}{issue.evidence ? ` (${issue.evidence})` : ''}
                                        </div>
                                    ))}
                                    {appeal.safetyReport.structuredAnalysis?.documentationGaps?.slice(0, 4).map((gap, i) => (
                                        <div key={`gap-${i}`} style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                                            <strong>Gap:</strong> {gap}
                                        </div>
                                    ))}
                                </div>
                            )}
                            <div className="letter-container">
                                <ReactMarkdown>{appeal.generatedLetter}</ReactMarkdown>
                            </div>
                            {appeal.citations && appeal.citations.length > 0 && (
                                <div className="citation-sidebar">
                                    <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>
                                        <Sparkles size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 6 }} />
                                        Coverage Criteria Used
                                    </h3>
                                    {appeal.citations.map(c => (
                                        <div key={c.index} className="citation-item">
                                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                                                <span className="citation-index">{c.index}</span>
                                                <div>
                                                    <div className="citation-title">{c.title}</div>
                                                    <div className="citation-source">{c.source}</div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    {appeal.safetyReport?.structuredAnalysis?.policyMetadata && appeal.safetyReport.structuredAnalysis.policyMetadata.length > 0 && (
                                        <div style={{ marginTop: 16, padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                                            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                                                Policy Freshness
                                            </div>
                                            {appeal.safetyReport.structuredAnalysis.policyMetadata.map((p, i) => (
                                                <div key={i} style={{ fontSize: 12, padding: '4px 0', borderBottom: '1px solid var(--border)' }}>
                                                    <div style={{ fontWeight: 600 }}>{p.title}</div>
                                                    <div style={{ color: 'var(--text-muted)' }}>{p.source} · Effective {p.effectiveDate} · {p.freshnessStatus.replace('_', ' ')}</div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </>
                )}

                {activeTab === 'notes' && (
                    <div className="card" style={{ maxWidth: 800 }}>
                        <pre style={{ whiteSpace: 'pre-wrap', fontFamily: "'SF Mono', Menlo, monospace", fontSize: 13, lineHeight: 1.7, color: 'var(--text-secondary)' }}>
                            {appeal.clinicalNotes}
                        </pre>
                    </div>
                )}

                {activeTab === 'denial' && (
                    <div className="card" style={{ maxWidth: 600 }}>
                        <div style={{ marginBottom: 20 }}>
                            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Insurance Company</div>
                            <div style={{ fontSize: 15 }}>{appeal.insuranceCompany || 'N/A'}</div>
                        </div>
                        <div style={{ marginBottom: 20 }}>
                            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Denied Service</div>
                            <div style={{ fontSize: 15 }}>{appeal.deniedService}</div>
                        </div>
                        <div style={{ marginBottom: 20 }}>
                            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Reason for Denial</div>
                            <div style={{ fontSize: 15, lineHeight: 1.7, color: 'var(--text-secondary)' }}>{appeal.denialReason}</div>
                        </div>
                        <div className="form-grid-2">
                            <div>
                                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>CPT Code(s)</div>
                                <div style={{ fontFamily: 'monospace', fontSize: 15 }}>{appeal.cptCodes || 'N/A'}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>ICD-10 Code(s)</div>
                                <div style={{ fontFamily: 'monospace', fontSize: 15 }}>{appeal.icd10Codes || 'N/A'}</div>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
