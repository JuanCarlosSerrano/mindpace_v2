type Props = {
  planId: number;
  athleteId: number;
  isoWeek: string;
  onPlanIdChange: (value: number) => void;
  onAthleteIdChange: (value: number) => void;
  onWeekChange: (value: string) => void;
};

export default function WeekPicker({
  planId,
  athleteId,
  isoWeek,
  onPlanIdChange,
  onAthleteIdChange,
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
        <label>Athlete ID</label>
        <input
          type="number"
          value={athleteId}
          onChange={(e) => onAthleteIdChange(Number(e.target.value))}
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
