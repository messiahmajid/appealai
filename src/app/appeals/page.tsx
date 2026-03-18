'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import { FileText, ArrowRight, Search, FilePlus } from 'lucide-react';

interface Appeal {
    id: string;
    patientName: string;
    deniedService: string;
    insuranceCompany: string;
    status: string;
    createdAt: string;
    cptCodes: string;
    icd10Codes: string;
}

export default function AppealsPage() {
    const [appeals, setAppeals] = useState<Appeal[]>([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/appeals')
            .then(r => r.json())
            .then(data => {
                setAppeals(data.appeals || []);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, []);

    const filtered = appeals.filter(a => {
        if (!search) return true;
        const q = search.toLowerCase();
        return (
            a.patientName.toLowerCase().includes(q) ||
            a.deniedService.toLowerCase().includes(q) ||
            a.insuranceCompany.toLowerCase().includes(q) ||
            a.cptCodes.toLowerCase().includes(q) ||
            a.icd10Codes.toLowerCase().includes(q)
        );
    });

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="main-content">
                <div className="page-header">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <h1 className="page-title">
                                Appeal History
                            </h1>
                            <p className="page-subtitle">View and manage all generated appeal letters.</p>
                        </div>
                        <Link href="/new-appeal" className="btn btn-primary">
                            <FilePlus size={16} /> New Appeal
                        </Link>
                    </div>
                </div>

                {/* Search */}
                <div style={{ position: 'relative', marginBottom: 24, maxWidth: 400 }}>
                    <Search size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-muted)' }} />
                    <input
                        className="form-input"
                        style={{ paddingLeft: 36 }}
                        placeholder="Search appeals..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                </div>

                {loading ? (
                    <div className="loading-container">
                        <div className="loading-spinner" />
                        <div className="loading-text">Loading appeals...</div>
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="empty-state">
                        <FileText size={48} className="empty-state-icon" />
                        <h3 className="empty-state-title">
                            {appeals.length === 0 ? 'No appeals yet' : 'No matching appeals'}
                        </h3>
                        <p className="empty-state-text">
                            {appeals.length === 0
                                ? 'Generate your first appeal letter to get started.'
                                : 'Try a different search term.'}
                        </p>
                        {appeals.length === 0 && (
                            <Link href="/new-appeal" className="btn btn-primary">
                                <FilePlus size={16} /> Create First Appeal
                            </Link>
                        )}
                    </div>
                ) : (
                    <div className="appeals-list">
                        {/* Header */}
                        <div className="appeal-row" style={{ background: 'transparent', border: 'none', cursor: 'default', padding: '8px 20px' }}>
                            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Patient / Service</div>
                            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Insurance</div>
                            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Date</div>
                            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status</div>
                            <div></div>
                        </div>
                        {filtered.map(appeal => (
                            <Link key={appeal.id} href={`/appeals/${appeal.id}`} className="appeal-row">
                                <div>
                                    <div className="appeal-row-patient">{appeal.patientName}</div>
                                    <div className="appeal-row-service">{appeal.deniedService}</div>
                                </div>
                                <div className="appeal-row-service">{appeal.insuranceCompany}</div>
                                <div className="appeal-row-date">
                                    {new Date(appeal.createdAt).toLocaleDateString()}
                                </div>
                                <div>
                                    <span className={`status-badge ${appeal.status}`}>{appeal.status}</span>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <ArrowRight size={16} color="var(--text-muted)" />
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
