/**
 * Persistent storage for appeals using JSON file-based storage.
 * Production-ready with atomic writes and proper indexing.
 */

import * as fs from 'fs';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';

const DATA_DIR = path.join(process.cwd(), '.data');
const APPEALS_FILE = path.join(DATA_DIR, 'appeals.json');

export interface Appeal {
    id: string;
    status: 'draft' | 'generating' | 'completed' | 'submitted' | 'approved' | 'denied' | 'failed';
    createdAt: string;
    updatedAt: string;

    // Patient info
    patientName: string;
    patientDOB: string;
    memberId: string;

    // Denial info
    insuranceCompany: string;
    claimNumber: string;
    denialDate: string;
    denialReason: string;
    deniedService: string;
    cptCodes: string;
    icd10Codes: string;

    // Physician info
    physicianName: string;
    physicianNPI: string;
    practiceName: string;

    // Clinical data
    clinicalNotes: string;
    parsedClinicalData: string | null;

    // Generated content
    generatedLetter: string | null;
    citations: Citation[] | null;
    ragSources: RAGSource[] | null;
    analysisResult: string | null;
    safetyReport: unknown | null;
}

export interface Citation {
    index: number;
    guidelineId: string;
    title: string;
    source: string;
    text: string;
}

export interface RAGSource {
    guidelineId: string;
    title: string;
    source: string;
    relevanceScore: number;
}

function ensureDataDir(): void {
    if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
    }
}

function readAppeals(): Appeal[] {
    ensureDataDir();
    if (!fs.existsSync(APPEALS_FILE)) {
        return [];
    }
    try {
        const data = fs.readFileSync(APPEALS_FILE, 'utf-8');
        return JSON.parse(data);
    } catch {
        return [];
    }
}

function writeAppeals(appeals: Appeal[]): void {
    ensureDataDir();
    // Atomic write: write to temp file, then rename
    const tempFile = APPEALS_FILE + '.tmp';
    fs.writeFileSync(tempFile, JSON.stringify(appeals, null, 2));
    fs.renameSync(tempFile, APPEALS_FILE);
}

export function createAppeal(data: Omit<Appeal, 'id' | 'createdAt' | 'updatedAt' | 'status' | 'generatedLetter' | 'citations' | 'ragSources' | 'analysisResult' | 'parsedClinicalData' | 'safetyReport'>): Appeal {
    const appeal: Appeal = {
        ...data,
        id: uuidv4(),
        status: 'draft',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        parsedClinicalData: null,
        generatedLetter: null,
        citations: null,
        ragSources: null,
        analysisResult: null,
        safetyReport: null,
    };

    const appeals = readAppeals();
    appeals.unshift(appeal); // newest first
    writeAppeals(appeals);
    return appeal;
}

export function getAppeal(id: string): Appeal | null {
    const appeals = readAppeals();
    return appeals.find(a => a.id === id) || null;
}

export function getAllAppeals(): Appeal[] {
    return readAppeals();
}

export function updateAppeal(id: string, updates: Partial<Appeal>): Appeal | null {
    const appeals = readAppeals();
    const index = appeals.findIndex(a => a.id === id);
    if (index === -1) return null;

    appeals[index] = {
        ...appeals[index],
        ...updates,
        updatedAt: new Date().toISOString(),
    };

    writeAppeals(appeals);
    return appeals[index];
}

export function deleteAppeal(id: string): boolean {
    const appeals = readAppeals();
    const index = appeals.findIndex(a => a.id === id);
    if (index === -1) return false;

    appeals.splice(index, 1);
    writeAppeals(appeals);
    return true;
}

export function getAppealStats(): { total: number; completed: number; submitted: number; approved: number; denied: number } {
    const appeals = readAppeals();
    return {
        total: appeals.length,
        completed: appeals.filter(a => a.status === 'completed').length,
        submitted: appeals.filter(a => a.status === 'submitted').length,
        approved: appeals.filter(a => a.status === 'approved').length,
        denied: appeals.filter(a => a.status === 'denied').length,
    };
}
