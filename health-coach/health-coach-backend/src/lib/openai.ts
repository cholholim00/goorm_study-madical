// src/lib/openai.ts
import OpenAI from 'openai';

if (!process.env.OPENAI_API_KEY) {
    // 서버 시작할 때 바로 에러를 던져서, 키가 없으면 눈치채기 쉽게
    throw new Error('OPENAI_API_KEY is not set in .env');
}

export const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});
