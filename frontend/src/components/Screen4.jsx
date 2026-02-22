import React, { useState } from 'react'
import s from './Screen4.module.css'

const PersonIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
    </svg>
)

export default function Screen4({ candidates, decisions, onConfirm, onBack }) {
    const [reviewEmails, setReviewEmails] = useState(true)
    const [holdEmails, setHoldEmails] = useState(false)

    const interviewCount = Object.values(decisions).filter(d => d === 'Interview').length
    const holdCount = Object.values(decisions).filter(d => d === 'Hold').length
    const rejectCount = Object.values(decisions).filter(d => d === 'Reject').length

    // Build ordered list: sorted by score desc
    const items = candidates
        .map(c => ({ ...c, decision: decisions[c.candidate_id] }))
        .sort((a, b) => b.total_score - a.total_score)

    const badgeClass = { Interview: s.badgeInterview, Hold: s.badgeHold, Reject: s.badgeReject }

    return (
        <div className={s.wrapper}>
            <div className={s.card}>
                <p className={s.screenLabel}>SCREEN 4</p>
                <h2 className={s.screenTitle}>Action Confirmation</h2>
                <hr className={s.divider} />

                <div className={s.summaryBox}>
                    <div className={s.clockIcon}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                        </svg>
                    </div>
                    <div>
                        <div className={s.summaryTitle}>Review Actions for {candidates.length} Candidates</div>
                        <div className={s.summarySub}>{interviewCount} to interview • {holdCount} on hold • {rejectCount} rejected</div>
                    </div>
                </div>

                <div className={s.hitlBox}>
                    <strong>Human-in-the-loop:</strong> Review AI recommendations and confirm your decisions before proceeding.
                </div>

                <p className={s.pendingLabel}>PENDING ACTIONS</p>
                <div className={s.pendingList}>
                    {items.map(c => (
                        <div key={c.candidate_id} className={s.pendingItem}>
                            <div className={s.pendingLeft}>
                                <div className={s.avatar}><PersonIcon /></div>
                                <div>
                                    <div className={s.pendingName}>{c.name || '—'}</div>
                                    <div className={s.pendingScore}>Match: {c.total_score}/100</div>
                                </div>
                            </div>
                            <span className={`${s.badge} ${badgeClass[c.decision]}`}>{c.decision}</span>
                        </div>
                    ))}
                </div>

                <div className={s.options}>
                    <p className={s.optionsLabel}>Options</p>
                    <label className={s.checkRow}>
                        <input type="checkbox" checked={reviewEmails} onChange={e => setReviewEmails(e.target.checked)} />
                        <span>Review emails before sending to interview candidates</span>
                    </label>
                    <label className={s.checkRow}>
                        <input type="checkbox" checked={holdEmails} onChange={e => setHoldEmails(e.target.checked)} />
                        <span>Send automated status update to candidates on hold</span>
                    </label>
                </div>

                <button className={s.btnPrimary} onClick={() => onConfirm({ reviewEmails, holdEmails })}>
                    Confirm All Actions
                </button>
                <button className={s.btnOutline} onClick={onBack}>Go Back to Edit</button>
            </div>
        </div>
    )
}
