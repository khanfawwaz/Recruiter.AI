import React, { useState } from 'react'
import s from './Screen3.module.css'

const ACTIONS = ['Interview', 'Hold', 'Reject']

export default function Screen3({ candidates, jobId, onProceed }) {
    // decisions map: candidateId → 'Interview' | 'Hold' | 'Reject'
    const [decisions, setDecisions] = useState(() => {
        const map = {}
        candidates.forEach(c => {
            // use AI verdict as default
            if (c.verdict === 'Strong Yes' || c.verdict === 'Yes') map[c.candidate_id] = 'Interview'
            else if (c.verdict === 'Maybe') map[c.candidate_id] = 'Hold'
            else map[c.candidate_id] = 'Reject'
        })
        return map
    })

    const setDecision = (id, action) =>
        setDecisions(prev => ({ ...prev, [id]: action }))

    const handleProceed = () => onProceed(decisions)

    return (
        <div className={s.wrapper}>
            <div className={s.card}>
                <p className={s.screenLabel}>SCREEN 3</p>
                <h2 className={s.screenTitle}>Analysis Results Dashboard</h2>
                <hr className={s.divider} />

                <div className={s.banner}>
                    <span><strong>{candidates.length}</strong> candidates analyzed against job requirements</span>
                </div>

                <div className={s.tableWrap}>
                    <table className={s.table}>
                        <thead>
                            <tr>
                                <th>CANDIDATE</th>
                                <th>EXPERIENCE</th>
                                <th>KEY SKILLS</th>
                                <th>SCORE</th>
                                <th>ACTION</th>
                            </tr>
                        </thead>
                        <tbody>
                            {candidates.map(c => {
                                const current = decisions[c.candidate_id]
                                return (
                                    <tr key={c.candidate_id}>
                                        <td>
                                            <div className={s.name}>{c.name || '—'}</div>
                                            {c.education && <div className={s.edu}>{c.education}</div>}
                                        </td>
                                        <td className={s.exp}>
                                            {c.experience_years != null ? `${c.experience_years} years` : '—'}
                                        </td>
                                        <td>
                                            <div className={s.tags}>
                                                {(c.skills || []).slice(0, 4).map((sk, i) => (
                                                    <span key={i} className={s.tag}>{sk}</span>
                                                ))}
                                            </div>
                                        </td>
                                        <td className={s.score}>{c.total_score}</td>
                                        <td>
                                            <div className={s.actions}>
                                                {ACTIONS.map(a => (
                                                    <button
                                                        key={a}
                                                        className={`${s.actionBtn} ${current === a ? s[`sel${a}`] : ''}`}
                                                        onClick={() => setDecision(c.candidate_id, a)}
                                                    >
                                                        {a}
                                                    </button>
                                                ))}
                                            </div>
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>

                <div className={s.footer}>
                    <p className={s.hint}>AI recommendations shown — review and confirm actions</p>
                    <button className={s.btnPrimary} onClick={handleProceed}>
                        Proceed with Selected Actions
                    </button>
                </div>
            </div>
        </div>
    )
}
