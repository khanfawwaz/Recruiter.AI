import React, { useEffect, useState } from 'react'
import s from './Screen2.module.css'

const STEPS = [
    { key: 'parsing', label: 'Parsing Resumes' },
    { key: 'matching', label: 'Matching Skills' },
    { key: 'experience', label: 'Evaluating Experience' },
    { key: 'recs', label: 'Generating Recommendations' },
]

export default function Screen2({ count }) {
    const [activeStep, setActiveStep] = useState(0)
    const [progress, setProgress] = useState(0)

    useEffect(() => {
        // Animate steps while real API call is in flight
        let step = 0
        const stepInterval = setInterval(() => {
            step += 1
            if (step < STEPS.length) setActiveStep(step)
        }, 1800)

        const progInterval = setInterval(() => {
            setProgress(p => Math.min(p + 2, 95))
        }, 80)

        return () => { clearInterval(stepInterval); clearInterval(progInterval) }
    }, [])

    return (
        <div className={s.wrapper}>
            <div className={s.card}>
                <p className={s.screenLabel}>SCREEN 2</p>
                <h2 className={s.screenTitle}>Processing / Agent Running</h2>
                <hr className={s.divider} />

                <div className={s.spinnerWrap}><div className={s.spinner} /></div>

                <div className={s.stepsList}>
                    {STEPS.map((step, i) => {
                        const done = i < activeStep
                        const active = i === activeStep
                        return (
                            <div key={step.key} className={`${s.stepItem} ${done ? s.done : ''} ${active ? s.active : ''}`}>
                                <div className={s.stepIcon} />
                                <span>{step.label}</span>
                            </div>
                        )
                    })}
                </div>

                <div className={s.progressWrap}>
                    <div className={s.progressBar} style={{ width: `${progress}%` }} />
                </div>

                <p className={s.desc}>Recruit-AI is analyzing candidates against the job requirements</p>
                <p className={s.sub}>Processing {count} candidate{count !== 1 ? 's' : ''}...</p>
            </div>
        </div>
    )
}
