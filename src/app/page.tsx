'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { ArrowRight } from 'lucide-react';
import { SAMPLE_CASES } from '@/lib/sample-data';

interface Appeal {
  id: string;
  patientName: string;
  deniedService: string;
  insuranceCompany: string;
  status: string;
  createdAt: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [recentAppeals, setRecentAppeals] = useState<Appeal[]>([]);

  useEffect(() => {
    fetch('/api/appeals')
      .then(r => r.json())
      .then(data => {
        setRecentAppeals((data.appeals || []).slice(0, 5));
      })
      .catch(() => { });
  }, []);

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="hero">
          <h1 className="hero-title">
            Prior Authorization<br />Appeal Generator
          </h1>
          <p className="hero-subtitle">
            Upload clinical notes and denial details. Get a medically-cited
            appeal letter grounded in CMS guidelines and NCCN recommendations.
          </p>
          <div className="hero-actions">
            <Link href="/new-appeal" className="btn btn-primary btn-lg">
              New Appeal
            </Link>
            <Link href="/appeals" className="btn btn-secondary btn-lg">
              History
            </Link>
          </div>
        </div>

        {/* Recent Appeals */}
        {recentAppeals.length > 0 && (
          <div style={{ marginBottom: 48 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 16 }}>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 400 }}>Recent</h2>
              <Link href="/appeals" className="btn btn-ghost btn-sm">
                View all <ArrowRight size={13} />
              </Link>
            </div>
            <div className="appeals-list">
              {recentAppeals.map(appeal => (
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
                  <div>
                    <ArrowRight size={14} color="var(--text-muted)" />
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Sample Cases */}
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 400, marginBottom: 4 }}>
            Try a sample case
          </h2>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 0 }}>
            Load a realistic clinical scenario to see the pipeline in action.
          </p>
          <div className="sample-cases-grid">
            {SAMPLE_CASES.map(sc => (
              <div key={sc.id} className="sample-case-card" onClick={() => router.push(`/new-appeal?sample=${sc.id}`)}>
                <div className="sample-case-specialty">{sc.specialty}</div>
                <div className="sample-case-title">{sc.title}</div>
                <div className="sample-case-summary">{sc.summary}</div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
