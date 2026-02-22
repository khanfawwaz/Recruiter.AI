import React, { useState, useCallback } from 'react'
import s from './Screen1.module.css'

const UploadIcon = () => (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" />
        <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
    </svg>
)

export default function Screen1({ onAnalyze, externalError }) {
    const [jobTitle, setJobTitle] = useState('')
    const [jdFile, setJdFile] = useState(null)
    const [resumeFiles, setResumeFiles] = useState([])
    const [jdDrag, setJdDrag] = useState(false)
    const [resDrag, setResDrag] = useState(false)
    const [error, setError] = useState('')

    const addResumes = (files) => {
        const arr = Array.from(files).filter(f => f.type === 'application/pdf' || f.name.endsWith('.txt'))
        setResumeFiles(prev => {
            const names = new Set(prev.map(f => f.name))
            return [...prev, ...arr.filter(f => !names.has(f.name))]
        })
    }

    const removeResume = (idx) => setResumeFiles(prev => prev.filter((_, i) => i !== idx))

    const handleAnalyze = () => {
        if (!jobTitle.trim()) { setError('Please enter a job title.'); return }
        if (!jdFile) { setError('Please upload a Job Description file.'); return }
        if (resumeFiles.length === 0) { setError('Please upload at least one resume.'); return }
        setError('')
        onAnalyze({ jobTitle, jdFile, resumeFiles })
    }

    const canAnalyze = jobTitle.trim() && jdFile && resumeFiles.length > 0

    return (
        <div className={s.wrapper}>
            <div className={s.card}>
                <p className={s.screenLabel}>SCREEN 1</p>
                <h2 className={s.screenTitle}>Landing / Upload</h2>
                <hr className={s.divider} />

                <div className={s.brand}>
                    <h1 className={s.brandTitle}>Recruit-AI</h1>
                    <p className={s.brandSub}>AI-powered resume screening and interview recommendations</p>
                </div>
                <hr className={s.divider} />

                {/* Job Title */}
                <div className={s.fieldGroup}>
                    <label className={s.fieldLabel}>Job Title</label>
                    <input
                        className={s.input}
                        type="text"
                        placeholder="e.g. Senior Full-Stack Developer"
                        value={jobTitle}
                        onChange={e => setJobTitle(e.target.value)}
                    />
                </div>

                {/* JD Upload */}
                <div className={s.uploadSection}>
                    <span className={s.sectionLabel}>Job Description Upload</span>
                    <div
                        className={`${s.dropZone} ${jdDrag ? s.dragOver : ''} ${jdFile ? s.hasFile : ''}`}
                        onClick={() => document.getElementById('jd-input').click()}
                        onDragOver={e => { e.preventDefault(); setJdDrag(true) }}
                        onDragLeave={() => setJdDrag(false)}
                        onDrop={e => {
                            e.preventDefault(); setJdDrag(false)
                            const f = e.dataTransfer.files[0]
                            if (f) setJdFile(f)
                        }}
                    >
                        <div className={s.uploadIcon}><UploadIcon /></div>
                        <p className={s.dropLabel}>{jdFile ? jdFile.name : 'Upload JD (PDF or Text)'}</p>
                    </div>
                    <input id="jd-input" type="file" accept=".pdf,.txt" className={s.hidden}
                        onChange={e => e.target.files[0] && setJdFile(e.target.files[0])} />
                </div>

                {/* Resume Upload */}
                <div className={s.uploadSection}>
                    <span className={s.sectionLabel}>Resume Upload (Multiple)</span>
                    <div
                        className={`${s.dropZone} ${resDrag ? s.dragOver : ''}`}
                        onClick={() => document.getElementById('res-input').click()}
                        onDragOver={e => { e.preventDefault(); setResDrag(true) }}
                        onDragLeave={() => setResDrag(false)}
                        onDrop={e => { e.preventDefault(); setResDrag(false); addResumes(e.dataTransfer.files) }}
                    >
                        <div className={s.uploadIcon}><UploadIcon /></div>
                        <p className={s.dropLabel}>Upload Resumes (PDF or Text)</p>
                        <p className={s.dropHint}>Select multiple files</p>
                    </div>
                    <input id="res-input" type="file" accept=".pdf,.txt" multiple className={s.hidden}
                        onChange={e => addResumes(e.target.files)} />
                </div>

                {/* File list */}
                {resumeFiles.length > 0 && (
                    <div className={s.fileList}>
                        <p className={s.fileCount}>{resumeFiles.length} file(s) uploaded</p>
                        {resumeFiles.map((f, i) => (
                            <div key={i} className={s.fileItem}>
                                <span className={s.fileName}>{f.name}</span>
                                <button className={s.fileRemove} onClick={() => removeResume(i)} title="Remove">×</button>
                            </div>
                        ))}
                    </div>
                )}

                {(error || externalError) && (() => {
                    const msg = error || externalError
                    const isQuota = msg.includes('quota') || msg.includes('⚠️')
                    return (
                        <div className={isQuota ? s.quotaError : s.error}>
                            {isQuota
                                ? <><strong>⚠️ API Quota Exceeded</strong><br />Your Gemini free-tier quota has been used up. Please wait for it to reset (resets daily at midnight Pacific Time), or enable Demo Mode by setting <code>DEMO_MODE=true</code> in your <code>.env</code> file and restarting the server.</>
                                : msg
                            }
                        </div>
                    )
                })()}

                <button
                    className={`${s.btnPrimary} ${!canAnalyze ? s.disabled : ''}`}
                    onClick={handleAnalyze}
                    disabled={!canAnalyze}
                >
                    Analyze Candidates ({resumeFiles.length})
                </button>
                <p className={s.powered}>Powered by agentic AI</p>
            </div>
        </div>
    )
}
