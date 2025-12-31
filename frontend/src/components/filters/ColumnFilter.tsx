import { useState, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, Search, Check } from 'lucide-react';
import { viewerApi, type FilterValue } from '../../services/api';

interface ColumnFilterProps {
  tableName: string;
  columnName: string;
  selectedValues: string[];
  onChange: (values: string[]) => void;
  currentFilters?: Record<string, FilterValue>;
}

export default function ColumnFilter({
  tableName,
  columnName,
  selectedValues,
  onChange,
  currentFilters,
}: ColumnFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch distinct values, passing current filters to scope available options
  const { data, isLoading } = useQuery({
    queryKey: ['distinct-values', tableName, columnName, search, currentFilters],
    queryFn: () => viewerApi.getDistinctValues(tableName, columnName, search || undefined, 100, currentFilters),
    enabled: isOpen,
    staleTime: 30000,
  });

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

  const toggleValue = (value: string) => {
    if (selectedValues.includes(value)) {
      onChange(selectedValues.filter((v) => v !== value));
    } else {
      onChange([...selectedValues, value]);
    }
  };

  const selectAll = () => {
    if (data?.values) {
      const stringValues = data.values.map((v) => String(v));
      onChange(stringValues);
    }
  };

  const clearAll = () => {
    onChange([]);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-1 px-2 py-1 text-xs rounded border transition-colors ${
          selectedValues.length > 0
            ? 'bg-accent-purple/20 border-accent-purple/50 text-accent-purpleLight'
            : 'bg-dark-700 border-dark-500 text-gray-400 hover:border-accent-purple/50'
        }`}
      >
        <span className="truncate max-w-[100px]">
          {selectedValues.length > 0
            ? `${columnName} (${selectedValues.length})`
            : columnName}
        </span>
        <ChevronDown className={`h-3 w-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-64 bg-dark-800 border border-dark-500 rounded-lg shadow-xl">
          {/* Search */}
          <div className="p-2 border-b border-dark-500">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-500" />
              <input
                type="text"
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-7 pr-2 py-1.5 text-xs bg-dark-700 border border-dark-500 rounded text-gray-300 placeholder-gray-500 focus:outline-none focus:border-accent-purple"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="px-2 py-1.5 border-b border-dark-500 flex gap-2">
            <button
              onClick={selectAll}
              className="text-xs text-accent-purple hover:text-accent-purpleLight"
            >
              Select All
            </button>
            <span className="text-dark-500">|</span>
            <button
              onClick={clearAll}
              className="text-xs text-gray-400 hover:text-gray-300"
            >
              Clear
            </button>
          </div>

          {/* Values List */}
          <div className="max-h-48 overflow-y-auto">
            {isLoading ? (
              <div className="p-3 text-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-accent-purple mx-auto"></div>
              </div>
            ) : data?.values && data.values.length > 0 ? (
              data.values.map((value) => {
                const strValue = String(value);
                const isSelected = selectedValues.includes(strValue);
                return (
                  <button
                    key={strValue}
                    onClick={() => toggleValue(strValue)}
                    className={`w-full flex items-center gap-2 px-3 py-1.5 text-xs text-left hover:bg-dark-700 ${
                      isSelected ? 'bg-accent-purple/10' : ''
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded border flex items-center justify-center ${
                        isSelected
                          ? 'bg-accent-purple border-accent-purple'
                          : 'border-dark-500'
                      }`}
                    >
                      {isSelected && <Check className="h-3 w-3 text-white" />}
                    </div>
                    <span className="truncate text-gray-300" title={strValue}>
                      {strValue || <span className="italic text-gray-500">(empty)</span>}
                    </span>
                  </button>
                );
              })
            ) : (
              <div className="p-3 text-center text-xs text-gray-500">No values found</div>
            )}
          </div>

          {/* Footer */}
          {data && data.total_count > 100 && (
            <div className="px-2 py-1.5 border-t border-dark-500 text-xs text-gray-500 text-center">
              Showing 100 of {data.total_count} values
            </div>
          )}
        </div>
      )}
    </div>
  );
}
