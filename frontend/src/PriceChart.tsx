import { useEffect, useRef } from 'react'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Filler,
} from 'chart.js'
import type { Report } from './contracts'

Chart.register(
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Filler,
)

export function PriceChart({ history, range }: { history: Report['history']; range: number }) {
  const canvas = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    if (!canvas.current || !history.length) return
    const selected = history.slice(-range)
    const chart = new Chart(canvas.current, {
      type: 'line',
      data: {
        labels: selected.map((point) => point.date),
        datasets: [
          {
            label: 'Observed close',
            data: selected.map((point) => point.close),
            borderColor: '#188265',
            backgroundColor: 'rgba(24,130,101,.07)',
            borderWidth: 2,
            pointRadius: 0,
            pointHitRadius: 12,
            fill: true,
            tension: 0.22,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: { display: false },
          tooltip: { displayColors: false, backgroundColor: '#202c28' },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              maxTicksLimit: 5,
              maxRotation: 0,
              color: '#718077',
              callback(value) {
                return this.getLabelForValue(Number(value)).slice(5)
              },
            },
            border: { display: false },
          },
          y: {
            position: 'right',
            grid: { color: '#edf1ee' },
            ticks: { maxTicksLimit: 5, color: '#718077' },
            border: { display: false },
          },
        },
      },
    })
    return () => chart.destroy()
  }, [history, range])
  return (
    <div className="price-chart">
      {history.length ? (
        <canvas ref={canvas} aria-label="Historical closing price chart" role="img" />
      ) : (
        <div className="empty">Historical prices unavailable</div>
      )}
    </div>
  )
}
