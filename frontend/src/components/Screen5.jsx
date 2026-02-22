import React, { useState } from 'react'
import s from './Screen5.module.css'

const MailIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
        <polyline points="22,6 12,13 2,6" />
    </svg>
)

const CalIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
    </svg>
)

// Simulate a proposed interview date (Wed 2 weeks from now, 2pm)
function getProposedTime() {
    const d = new Date()
    d.setDate(d.getDate() + ((3 - d.getDay() + 7) % 7) + 7)
    return d.toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' }) + ' • 2:00 PM'
}

function EmailCard({ candidate }) {
    const [open, setOpen] = useState(false)
    const proposedTime = getProposedTime()

    return (
        <div className={s.emailCard}>
            <div className={s.emailHeader} onClick={() => setOpen(o => !o)}>
                <div className={s.emailLeft}>
                    <span className={s.mailIcon}><MailIcon /></span>
                    <div>
                        <div className={s.emailName}>{candidate.name || '—'}</div>
                        <div className={s.emailAddr}>{candidate.email || 'no email on file'}</div>
                    </div>
                </div>
                <span className={`${s.chevron} ${open ? s.open : ''}`}>›</span>
            </div>

            {open && (
                <div className={s.emailBody}>
                    <div className={s.subject}>Subject: Interview Invitation — {candidate.job_title}</div>
                    <div className={s.bodyText}>
                        <p>Dear {candidate.name},</p>
                        <br />
                        <p>Thank you for your interest in the {candidate.job_title} position. We were impressed with your background and would like to invite you for an interview.</p>
                        <br />
                        <p>Please confirm your availability for the proposed time below.</p>
                        <br />
                        <p>Best regards,<br />Hiring Team</p>
                    </div>
                    <div className={s.timeProp}>
                        <span className={s.calIcon}><CalIcon /></span>
                        <div>
                            <div className={s.propLabel}>Proposed Time</div>
                            <div className={s.propVal}>{proposedTime}</div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default function Screen5({ candidates, decisions, jobTitle, onSend, onBack, loading, error }) {
    const interviewCandidates = candidates.filter(c => decisions[c.candidate_id] === 'Interview')

    return (
        <div className={s.wrapper}>
            <div className={s.card}>
                <p className={s.screenLabel}>SCREEN 5</p>
                <h2 className={s.screenTitle}>Email / Scheduling Preview</h2>
                <hr className={s.divider} />

                <div className={s.mvpBanner}>
                    <strong>MVP Simulation:</strong> No real integrations — preview only
                </div>

                <p className={s.intro}>Interview invitations for {interviewCandidates.length} candidate(s)</p>

                <div>
                    {interviewCandidates.map(c => (
                        <EmailCard key={c.candidate_id} candidate={{ ...c, job_title: jobTitle }} />
                    ))}
                </div>

                <div className={s.note}>
                    <strong>Scheduling Note:</strong> Interview times will be automatically scheduled based on team availability. Candidates can reschedule if needed.
                </div>

                {error && <div className={s.error}>{error}</div>}

                <div className={s.actions}>
                    <button className={`${s.btnPrimary} ${loading ? s.loading : ''}`} onClick={onSend} disabled={loading}>
                        {loading ? 'Sending...' : 'Send All Invitations'}
                    </button>
                    <button className={s.btnOutline} onClick={onBack} disabled={loading}>Go Back</button>
                </div>
            </div>
        </div>
    )
}
