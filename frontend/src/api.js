import axios from 'axios'

// In dev: Vite proxies /analyze, /override, /finalize, /session → localhost:8000
// In prod: set VITE_API_URL to your deployed backend
const BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({ baseURL: BASE })

/**
 * Upload JD + resumes in one shot.
 * Returns { session_id, candidates, errors }
 */
export async function analyze(jobTitle, jdFile, resumeFiles) {
    const fd = new FormData()
    fd.append('job_title', jobTitle)
    fd.append('jd_pdf', jdFile)
    resumeFiles.forEach(f => fd.append('resumes', f))
    const { data } = await api.post('/analyze', fd)
    return data
}

/**
 * Update a candidate's decision in the session.
 */
export async function overrideDecision(sessionId, candidateId, decision) {
    const { data } = await api.post('/override', {
        session_id: sessionId,
        candidate_id: candidateId,
        decision,
    })
    return data
}

/**
 * Simulate email finalization – returns email previews.
 */
export async function finalizeSession(sessionId) {
    const { data } = await api.post(`/finalize/${sessionId}`)
    return data
}
