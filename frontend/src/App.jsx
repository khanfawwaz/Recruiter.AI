import React, { useState } from 'react'
import Screen1 from './components/Screen1'
import Screen2 from './components/Screen2'
import Screen3 from './components/Screen3'
import Screen4 from './components/Screen4'
import Screen5 from './components/Screen5'
import { analyze, overrideDecision, finalizeSession } from './api'
import s from './App.module.css'

export default function App() {
    const [screen, setScreen] = useState('upload')
    const [sessionId, setSessionId] = useState(null)
    const [jobTitle, setJobTitle] = useState('')
    const [resumeCount, setResumeCount] = useState(0)
    const [candidates, setCandidates] = useState([])
    const [decisions, setDecisions] = useState({})
    const [uploadError, setUploadError] = useState('')
    const [finalizing, setFinalizing] = useState(false)
    const [finalizeErr, setFinalizeErr] = useState('')
    const [emailPreviews, setEmailPreviews] = useState([])

    // Screen 1 → 2 → 3
    const handleAnalyze = async ({ jobTitle: title, jdFile, resumeFiles }) => {
        setUploadError('')
        setJobTitle(title)
        setResumeCount(resumeFiles.length)
        setScreen('processing')

        try {
            const result = await analyze(title, jdFile, resumeFiles)
            setSessionId(result.session_id)
            setCandidates(result.candidates || [])
            // Seed decisions from AI defaults
            const dec = {}
                ; (result.candidates || []).forEach(c => { dec[c.candidate_id] = c.decision })
            setDecisions(dec)
            setScreen('results')
        } catch (err) {
            setUploadError(err?.response?.data?.detail || err.message || 'Upload failed.')
            setScreen('upload')
        }
    }

    // Screen 3 → 4  (fire overrides to backend in background)
    const handleProceed = async (newDecisions) => {
        setDecisions(newDecisions)
        // Best-effort overrides – don't block UI on failures
        Object.entries(newDecisions).forEach(([cid, dec]) => {
            overrideDecision(sessionId, cid, dec).catch(() => { })
        })
        setScreen('confirm')
    }

    // Screen 4 → 5
    const handleConfirm = () => setScreen('preview')

    // Screen 5 → done
    const handleSend = async () => {
        setFinalizing(true)
        setFinalizeErr('')
        try {
            const result = await finalizeSession(sessionId)
            setEmailPreviews(result.email_previews || [])
            setScreen('done')
        } catch (err) {
            setFinalizeErr(err?.response?.data?.detail || err.message || 'Finalize failed.')
        } finally {
            setFinalizing(false)
        }
    }

    const reset = () => {
        setScreen('upload'); setSessionId(null); setJobTitle(''); setResumeCount(0)
        setCandidates([]); setDecisions({}); setUploadError(''); setFinalizeErr('')
        setEmailPreviews([])
    }

    return (
        <>
            {screen === 'upload' && <Screen1 onAnalyze={handleAnalyze} externalError={uploadError} />}
            {screen === 'processing' && <Screen2 count={resumeCount} />}
            {screen === 'results' && <Screen3 candidates={candidates} onProceed={handleProceed} />}
            {screen === 'confirm' && (
                <Screen4
                    candidates={candidates} decisions={decisions}
                    onConfirm={handleConfirm} onBack={() => setScreen('results')}
                />
            )}
            {screen === 'preview' && (
                <Screen5
                    candidates={candidates} decisions={decisions}
                    jobTitle={jobTitle}
                    onSend={handleSend} onBack={() => setScreen('confirm')}
                    loading={finalizing} error={finalizeErr}
                />
            )}
            {screen === 'done' && (
                <div className={s.doneWrap}>
                    <div className={s.doneCard}>
                        <div className={s.doneIcon}>✓</div>
                        <h2 className={s.doneTitle}>All Done!</h2>
                        <p className={s.doneSub}>
                            {emailPreviews.length} interview invitation{emailPreviews.length !== 1 ? 's' : ''} simulated.
                        </p>
                        <button className={s.btnPrimary} onClick={reset}>Start New Analysis</button>
                    </div>
                </div>
            )}
        </>
    )
}
