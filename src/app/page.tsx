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
        <div className="hero dashboard-hero">
          <div>
            <div className="hero-kicker">Clinical appeal workbench</div>
            <h1 className="hero-title">
              Prior Authorization<br />Appeal Generator
            </h1>
            <p className="hero-subtitle">
              Upload clinical notes and denial details. Generate a medically cited
              appeal letter with policy retrieval, PubMed context, and safety checks.
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
          <div className="hero-panel" aria-label="Appeal generation pipeline">
            <div className="hero-panel-title">Pipeline</div>
            <div className="pipeline-list">
              <div className="pipeline-item">
                <span className="pipeline-step">01</span>
                <div>
                  <div className="pipeline-name">Parse the record</div>
                  <div className="pipeline-copy">Clinical notes, denial details, codes, and provider fields stay separated.</div>
                </div>
              </div>
              <div className="pipeline-item">
                <span className="pipeline-step">02</span>
                <div>
                  <div className="pipeline-name">Retrieve policy evidence</div>
                  <div className="pipeline-copy">Exact CPT and ICD-10 matches are preferred before fallback search.</div>
                </div>
              </div>
              <div className="pipeline-item">
                <span className="pipeline-step">03</span>
                <div>
                  <div className="pipeline-name">Draft, check, export</div>
                  <div className="pipeline-copy">The generated letter is screened for placeholders, citations, quotes, and numeric claims.</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Appeals */}
        {recentAppeals.length > 0 && (
          <div style={{ marginBottom: 56 }}>
            <div className="section-head">
              <h2 className="section-title">Recent appeals</h2>
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
          <div className="section-head">
            <div>
              <h2 className="section-title">Try a sample case</h2>
              <p className="section-copy">
                Load a realistic clinical scenario to see the full pipeline before entering your own case.
              </p>
            </div>
          </div>
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
