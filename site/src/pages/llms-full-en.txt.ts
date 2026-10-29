import type { APIRoute } from 'astro';
import { testoIntegrale } from './llms-full.txt';

export const GET: APIRoute = () => testoIntegrale('en');
