import { useState, useRef, useEffect } from 'react';
import { Calendar, ChevronDown, X } from 'lucide-react';

interface DateRangeFilterProps {
  columnName: string;
  value: { from?: string; to?: string } | undefined;
  onChange: (value: { from?: string; to?: string } | undefined) => void;
}

export default function DateRangeFilter({
  columnName,
  value,
  onChange,
}: DateRangeFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [fromDate, setFromDate] = useState(value?.from?.split('T')[0] || '');
  const [fromTime, setFromTime] = useState(value?.from?.split('T')[1]?.slice(0, 5) || '00:00');
  const [toDate, setToDate] = useState(value?.to?.split('T')[0] || '');
  const [toTime, setToTime] = useState(value?.to?.split('T')[1]?.slice(0, 5) || '23:59');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const applyFilter = () => {
    const newValue: { from?: string; to?: string } = {};

    if (fromDate) {
      newValue.from = `${fromDate}T${fromTime}:00`;
    }
    if (toDate) {
      newValue.to = `${toDate}T${toTime}:59`;
    }

    if (newValue.from || newValue.to) {
      onChange(newValue);
    } else {
      onChange(undefined);
    }
    setIsOpen(false);
  };

  const clearFilter = () => {
    setFromDate('');
    setFromTime('00:00');
    setToDate('');
    setToTime('23:59');
    onChange(undefined);
    setIsOpen(false);
  };

  const hasValue = value?.from || value?.to;

  const formatDisplayDate = (dateStr?: string) => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      });
    } catch {
      return dateStr;
    }
  };

  // Quick presets
  const setPreset = (days: number) => {
    const now = new Date();
    const from = new Date();
    from.setDate(now.getDate() - days);

    setFromDate(from.toISOString().split('T')[0]);
    setFromTime('00:00');
    setToDate(now.toISOString().split('T')[0]);
    setToTime('23:59');
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-1 px-2 py-1 text-xs rounded border transition-colors ${
          hasValue
            ? 'bg-accent-purple/20 border-accent-purple/50 text-accent-purpleLight'
            : 'bg-dark-700 border-dark-500 text-gray-400 hover:border-accent-purple/50'
        }`}
      >
        <Calendar className="h-3 w-3" />
        <span className="truncate max-w-[120px]">
          {hasValue
            ? `${formatDisplayDate(value?.from)} - ${formatDisplayDate(value?.to)}`
            : columnName}
        </span>
        <ChevronDown className={`h-3 w-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-72 bg-dark-800 border border-dark-500 rounded-lg shadow-xl">
          {/* Presets */}
          <div className="p-2 border-b border-dark-500">
            <div className="text-xs text-gray-400 mb-2">Quick Select</div>
            <div className="flex flex-wrap gap-1">
              {[
                { label: 'Today', days: 0 },
                { label: 'Last 7 days', days: 7 },
                { label: 'Last 30 days', days: 30 },
                { label: 'Last 90 days', days: 90 },
              ].map((preset) => (
                <button
                  key={preset.label}
                  onClick={() => setPreset(preset.days)}
                  className="px-2 py-1 text-xs bg-dark-700 hover:bg-dark-600 text-gray-300 rounded border border-dark-500"
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* From Date/Time */}
          <div className="p-2 border-b border-dark-500">
            <div className="text-xs text-gray-400 mb-2">From</div>
            <div className="flex gap-2">
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="flex-1 px-2 py-1.5 text-xs bg-dark-700 border border-dark-500 rounded text-gray-300 focus:outline-none focus:border-accent-purple"
              />
              <input
                type="time"
                value={fromTime}
                onChange={(e) => setFromTime(e.target.value)}
                className="w-24 px-2 py-1.5 text-xs bg-dark-700 border border-dark-500 rounded text-gray-300 focus:outline-none focus:border-accent-purple"
              />
            </div>
          </div>

          {/* To Date/Time */}
          <div className="p-2 border-b border-dark-500">
            <div className="text-xs text-gray-400 mb-2">To</div>
            <div className="flex gap-2">
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="flex-1 px-2 py-1.5 text-xs bg-dark-700 border border-dark-500 rounded text-gray-300 focus:outline-none focus:border-accent-purple"
              />
              <input
                type="time"
                value={toTime}
                onChange={(e) => setToTime(e.target.value)}
                className="w-24 px-2 py-1.5 text-xs bg-dark-700 border border-dark-500 rounded text-gray-300 focus:outline-none focus:border-accent-purple"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="p-2 flex justify-between">
            <button
              onClick={clearFilter}
              className="px-3 py-1.5 text-xs text-gray-400 hover:text-gray-300"
            >
              Clear
            </button>
            <button
              onClick={applyFilter}
              className="px-3 py-1.5 text-xs bg-accent-purple hover:bg-accent-purpleDark text-white rounded"
            >
              Apply
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
