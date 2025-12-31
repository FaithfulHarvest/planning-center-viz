import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Table,
  ChevronLeft,
  ChevronRight,
  X,
  Database,
  Filter,
} from 'lucide-react';
import { viewerApi, type ColumnInfo, type FilterValue } from '../services/api';
import ColumnFilter from '../components/filters/ColumnFilter';
import DateRangeFilter from '../components/filters/DateRangeFilter';

// Helper to check if a column is a date/timestamp type
const isDateColumn = (column: ColumnInfo): boolean => {
  const dateTypes = ['datetime', 'datetime2', 'date', 'datetimeoffset', 'timestamp'];
  return dateTypes.includes(column.data_type.toLowerCase());
};

export default function DataViewerPage() {
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [filters, setFilters] = useState<Record<string, FilterValue>>({});
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);

  // Fetch available tables
  const { data: tables, isLoading: tablesLoading } = useQuery({
    queryKey: ['viewer-tables'],
    queryFn: () => viewerApi.getTables(),
  });

  // Fetch columns for selected table
  const { data: columns, isLoading: columnsLoading } = useQuery({
    queryKey: ['viewer-columns', selectedTable],
    queryFn: () => viewerApi.getTableColumns(selectedTable!),
    enabled: !!selectedTable,
  });

  // Fetch table data
  const { data: tableData, isLoading: dataLoading } = useQuery({
    queryKey: ['viewer-data', selectedTable, selectedColumns, filters, page, perPage],
    queryFn: () =>
      viewerApi.getTableData(selectedTable!, {
        columns: selectedColumns.length > 0 ? selectedColumns : undefined,
        filters: Object.keys(filters).length > 0 ? filters : undefined,
        page,
        perPage,
      }),
    enabled: !!selectedTable,
  });

  // Reset state when table changes
  useEffect(() => {
    setSelectedColumns([]);
    setFilters({});
    setPage(1);
  }, [selectedTable]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [filters, perPage]);

  const handleColumnToggle = (columnName: string) => {
    setSelectedColumns((prev) =>
      prev.includes(columnName)
        ? prev.filter((c) => c !== columnName)
        : [...prev, columnName]
    );
  };

  const handleFilterChange = (columnName: string, value: FilterValue | undefined) => {
    setFilters((prev) => {
      if (value === undefined || (Array.isArray(value) && value.length === 0)) {
        const newFilters = { ...prev };
        delete newFilters[columnName];
        return newFilters;
      }
      return { ...prev, [columnName]: value };
    });
  };

  const clearAllFilters = () => {
    setFilters({});
  };

  const displayColumns = selectedColumns.length > 0 ? selectedColumns : (tableData?.columns || []);
  const activeFilterCount = Object.keys(filters).length;

  // Get column info for a column name
  const getColumnInfo = (colName: string): ColumnInfo | undefined => {
    return columns?.find((c) => c.name === colName);
  };

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="bg-dark-800 border-b border-dark-500 shadow-lg">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center">
            <Link
              to="/dashboard"
              className="inline-flex items-center text-gray-400 hover:text-gray-200 mr-4"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <Database className="h-6 w-6 text-accent-purple mr-2" />
            <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-accent-purple to-accent-blue">
              Data Viewer
            </h1>
          </div>
        </div>
      </header>

      <main className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex gap-6">
          {/* Sidebar - Table & Column Selection */}
          <div className="w-72 flex-shrink-0 space-y-4">
            {/* Table Selection */}
            <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-4">
              <h2 className="text-sm font-semibold text-gray-300 mb-3 flex items-center">
                <Table className="h-4 w-4 mr-2" />
                Select Table
              </h2>
              {tablesLoading ? (
                <div className="animate-pulse space-y-2">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-8 bg-dark-600 rounded"></div>
                  ))}
                </div>
              ) : tables && tables.length > 0 ? (
                <div className="space-y-1 max-h-64 overflow-y-auto">
                  {tables.map((table) => (
                    <button
                      key={table.name}
                      onClick={() => setSelectedTable(table.name)}
                      className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                        selectedTable === table.name
                          ? 'bg-accent-purple/30 text-accent-purpleLight border border-accent-purple/50'
                          : 'text-gray-300 hover:bg-dark-600'
                      }`}
                    >
                      <div className="font-medium truncate">{table.name}</div>
                      <div className="text-xs text-gray-500">{table.row_count.toLocaleString()} rows</div>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No tables available. Refresh data first.</p>
              )}
            </div>

            {/* Column Selection */}
            {selectedTable && (
              <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-4">
                <h2 className="text-sm font-semibold text-gray-300 mb-3">
                  Select Columns
                  {selectedColumns.length > 0 && (
                    <span className="ml-2 text-xs text-accent-purple">
                      ({selectedColumns.length} selected)
                    </span>
                  )}
                </h2>
                {columnsLoading ? (
                  <div className="animate-pulse space-y-2">
                    {[...Array(6)].map((_, i) => (
                      <div key={i} className="h-6 bg-dark-600 rounded"></div>
                    ))}
                  </div>
                ) : columns && columns.length > 0 ? (
                  <div className="space-y-1 max-h-96 overflow-y-auto">
                    {columns.map((column) => (
                      <label
                        key={column.name}
                        className="flex items-center px-2 py-1.5 rounded hover:bg-dark-600 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedColumns.includes(column.name)}
                          onChange={() => handleColumnToggle(column.name)}
                          className="rounded border-dark-500 bg-dark-700 text-accent-purple focus:ring-accent-purple"
                        />
                        <span className="ml-2 text-sm text-gray-300 truncate" title={column.name}>
                          {column.name}
                        </span>
                        <span className="ml-auto text-xs text-gray-500">{column.data_type}</span>
                      </label>
                    ))}
                  </div>
                ) : null}
              </div>
            )}
          </div>

          {/* Main Content - Data Table */}
          <div className="flex-1 min-w-0">
            {!selectedTable ? (
              <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500 p-12 text-center">
                <Database className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-300">Select a table to view data</h3>
                <p className="text-sm text-gray-500 mt-2">
                  Choose a table from the sidebar to explore your Planning Center data
                </p>
              </div>
            ) : (
              <div className="bg-dark-800 rounded-lg shadow-lg border border-dark-500">
                {/* Table Header with Filters */}
                <div className="p-4 border-b border-dark-500">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-lg font-semibold text-gray-100">{selectedTable}</h2>
                    <div className="flex items-center gap-3">
                      {/* Per Page Selector */}
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-400">Per page:</span>
                        <select
                          value={perPage}
                          onChange={(e) => setPerPage(Number(e.target.value))}
                          className="bg-dark-700 border border-dark-500 text-gray-300 text-sm rounded px-2 py-1 focus:ring-accent-purple focus:border-accent-purple"
                        >
                          <option value={25}>25</option>
                          <option value={50}>50</option>
                          <option value={100}>100</option>
                          <option value={200}>200</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Filters Row */}
                  {columns && columns.length > 0 && (
                    <div className="flex flex-wrap items-center gap-2">
                      <Filter className="h-4 w-4 text-gray-500" />

                      {/* Show filters for displayed columns */}
                      {displayColumns.slice(0, 8).map((colName) => {
                        const colInfo = getColumnInfo(colName);
                        if (!colInfo) return null;

                        if (isDateColumn(colInfo)) {
                          // Date/timestamp filter
                          return (
                            <DateRangeFilter
                              key={colName}
                              columnName={colName}
                              value={filters[colName] as { from?: string; to?: string } | undefined}
                              onChange={(val) => handleFilterChange(colName, val)}
                            />
                          );
                        } else {
                          // Multi-select filter
                          return (
                            <ColumnFilter
                              key={colName}
                              tableName={selectedTable}
                              columnName={colName}
                              selectedValues={
                                Array.isArray(filters[colName])
                                  ? (filters[colName] as string[])
                                  : []
                              }
                              onChange={(vals) => handleFilterChange(colName, vals)}
                              currentFilters={filters}
                            />
                          );
                        }
                      })}

                      {activeFilterCount > 0 && (
                        <button
                          onClick={clearAllFilters}
                          className="flex items-center gap-1 px-2 py-1 text-xs text-red-400 hover:text-red-300 border border-red-400/30 rounded hover:border-red-400/50"
                        >
                          <X className="h-3 w-3" />
                          Clear all ({activeFilterCount})
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {/* Data Table */}
                <div className="overflow-x-auto">
                  {dataLoading ? (
                    <div className="p-8 text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-purple mx-auto"></div>
                      <p className="text-gray-400 mt-4">Loading data...</p>
                    </div>
                  ) : tableData && tableData.rows.length > 0 ? (
                    <table className="w-full">
                      <thead>
                        <tr className="bg-dark-700">
                          {displayColumns.map((col) => (
                            <th
                              key={col}
                              className="px-4 py-3 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider whitespace-nowrap"
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-dark-600">
                        {tableData.rows.map((row, rowIndex) => (
                          <tr key={rowIndex} className="hover:bg-dark-700/50">
                            {displayColumns.map((col) => (
                              <td
                                key={col}
                                className="px-4 py-3 text-sm text-gray-300 max-w-xs truncate"
                                title={String(row[col] ?? '')}
                              >
                                {row[col] === null ? (
                                  <span className="text-gray-600 italic">null</span>
                                ) : (
                                  String(row[col])
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div className="p-8 text-center text-gray-500">
                      No data found
                    </div>
                  )}
                </div>

                {/* Pagination */}
                {tableData && tableData.total_pages > 0 && (
                  <div className="px-4 py-3 border-t border-dark-500 flex items-center justify-between">
                    <div className="text-sm text-gray-400">
                      Showing {((page - 1) * perPage) + 1} to{' '}
                      {Math.min(page * perPage, tableData.total_count)} of{' '}
                      {tableData.total_count.toLocaleString()} results
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="p-2 rounded bg-dark-700 text-gray-300 hover:bg-dark-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </button>
                      <span className="text-sm text-gray-300">
                        Page {page} of {tableData.total_pages}
                      </span>
                      <button
                        onClick={() => setPage((p) => Math.min(tableData.total_pages, p + 1))}
                        disabled={page === tableData.total_pages}
                        className="p-2 rounded bg-dark-700 text-gray-300 hover:bg-dark-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
