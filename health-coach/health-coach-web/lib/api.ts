// lib/api.ts
export const API_BASE_URL = 'http://localhost:4000/api';

export interface AiCoachResponse {
    rangeDays: number;
    from: string;
    to: string;
    summaryLines: string[];
    tips: string[];
    states: {
        state: string;
        count: number;
        avg_sys: number | null;
        avg_dia: number | null;
    }[];
}
