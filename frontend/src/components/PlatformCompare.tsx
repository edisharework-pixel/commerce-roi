import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { PlatformProfit } from '../types';

interface Props {
  data: PlatformProfit[];
}

export default function PlatformCompare({ data }: Props) {
  const chartData = data.map(p => ({
    name: p.platform_name,
    매출: p.revenue,
    원가: p.cost_of_goods,
    수수료: p.platform_fee,
    광고비: p.ad_cost,
    순이익: p.net_profit,
  }));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis tickFormatter={(v) => `₩${(v / 10000).toFixed(0)}만`} />
        <Tooltip formatter={(v) => `₩${Number(v).toLocaleString()}`} />
        <Legend />
        <Bar dataKey="매출" fill="#1890ff" />
        <Bar dataKey="원가" fill="#ff7875" />
        <Bar dataKey="수수료" fill="#ffc069" />
        <Bar dataKey="광고비" fill="#b37feb" />
        <Bar dataKey="순이익" fill="#52c41a" />
      </BarChart>
    </ResponsiveContainer>
  );
}
