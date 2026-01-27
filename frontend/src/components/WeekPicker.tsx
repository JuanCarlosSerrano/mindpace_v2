type Props = {
  planId: number;
  isoWeek: string;
  onPlanIdChange: (value: number) => void;
  onWeekChange: (value: string) => void;
};

export default function WeekPicker({
  planId,
  isoWeek,
  onPlanIdChange,
  onWeekChange,
}: Props) {
  return (
    <div className="controls-grid">
      <div>
        <label>Plan ID</label>
        <input
          type="number"
          value={planId}
          onChange={(e) => onPlanIdChange(Number(e.target.value))}
        />
      </div>
      <div>
        <label>ISO Week</label>
        <input
          type="text"
          value={isoWeek}
          onChange={(e) => onWeekChange(e.target.value)}
        />
      </div>
    </div>
  );
}
