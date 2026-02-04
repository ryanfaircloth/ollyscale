import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { type Filter, type TimeRange } from '@/api/types/common';

export interface QueryState {
  filters: Filter[];
  timeRange: TimeRange;
  timeField: 'db_time' | 'event_time' | 'observed_time';
  timezone: string; // 'local', 'UTC', or IANA timezone
  freeTextSearch: string;
  selectedNamespaces: string[];
  selectedServices: string[];
  liveMode: boolean; // When true, time range slides forward on refresh
  relativeMinutes: number | null; // Minutes of relative time window (e.g., 30 for "last 30 min")
}

export interface QueryPreset {
  id: string;
  name: string;
  description?: string;
  query: QueryState;
  createdAt: string;
}

interface QueryContextValue {
  queryState: QueryState;
  updateFilters: (filters: Filter[]) => void;
  updateTimeRange: (timeRange: TimeRange, liveMode?: boolean) => void;
  updateTimeField: (field: QueryState['timeField']) => void;
  updateTimezone: (timezone: string) => void;
  updateFreeTextSearch: (search: string) => void;
  updateSelectedNamespaces: (namespaces: string[]) => void;
  updateSelectedServices: (services: string[]) => void;
  updateLiveMode: (enabled: boolean) => void;
  refreshTimeWindow: () => void; // Slide time window forward if in live mode
  resetQuery: () => void;

  // Preset management
  presets: QueryPreset[];
  savePreset: (name: string, description?: string) => void;
  loadPreset: (id: string) => void;
  deletePreset: (id: string) => void;
}

const QueryContext = createContext<QueryContextValue | undefined>(undefined);

const DEFAULT_QUERY_STATE: QueryState = {
  filters: [],
  timeRange: {
    start_time: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    end_time: new Date().toISOString(),
  },
  timeField: 'db_time',
  timezone: 'local',
  freeTextSearch: '',
  selectedNamespaces: [],
  selectedServices: [],
  liveMode: true,
  relativeMinutes: 30,
};

const STORAGE_KEY = 'ollyscale-query-state';
const PRESETS_KEY = 'ollyscale-query-presets';

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryState, setQueryState] = useState<QueryState>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        // If in live mode, recalculate time range on load to avoid stale data
        if (parsed.liveMode && parsed.relativeMinutes) {
          const end = new Date();
          const start = new Date(end.getTime() - parsed.relativeMinutes * 60 * 1000);
          parsed.timeRange = {
            start_time: start.toISOString(),
            end_time: end.toISOString(),
          };
        }
        return parsed;
      } catch {
        return DEFAULT_QUERY_STATE;
      }
    }
    return DEFAULT_QUERY_STATE;
  });

  const [presets, setPresets] = useState<QueryPreset[]>(() => {
    const stored = localStorage.getItem(PRESETS_KEY);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {
        return [];
      }
    }
    return [];
  });

  // Persist query state to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queryState));
  }, [queryState]);

  // Persist presets to localStorage
  useEffect(() => {
    localStorage.setItem(PRESETS_KEY, JSON.stringify(presets));
  }, [presets]);

  const updateFilters = (filters: Filter[]) => {
    setQueryState((prev) => ({ ...prev, filters }));
  };

  const updateTimeRange = (timeRange: TimeRange, liveMode?: boolean) => {
    setQueryState((prev) => ({
      ...prev,
      timeRange,
      liveMode: liveMode !== undefined ? liveMode : false, // Manual time selection disables live mode
      relativeMinutes: liveMode ? prev.relativeMinutes : null,
    }));
  };

  const updateLiveMode = (enabled: boolean) => {
    setQueryState((prev) => {
      if (enabled && prev.relativeMinutes) {
        // Re-enable live mode with current relative window
        const end = new Date();
        const start = new Date(end.getTime() - prev.relativeMinutes * 60 * 1000);
        return {
          ...prev,
          liveMode: true,
          timeRange: {
            start_time: start.toISOString(),
            end_time: end.toISOString(),
          },
        };
      }
      return { ...prev, liveMode: enabled };
    });
  };

  const refreshTimeWindow = () => {
    setQueryState((prev) => {
      if (prev.liveMode && prev.relativeMinutes) {
        const end = new Date();
        const start = new Date(end.getTime() - prev.relativeMinutes * 60 * 1000);
        const newRange = {
          start_time: start.toISOString(),
          end_time: end.toISOString(),
        };
        return {
          ...prev,
          timeRange: newRange,
        };
      }
      return prev;
    });
  };

  const updateTimeField = (timeField: QueryState['timeField']) => {
    setQueryState((prev) => ({ ...prev, timeField }));
  };

  const updateTimezone = (timezone: string) => {
    setQueryState((prev) => ({ ...prev, timezone }));
  };

  const updateFreeTextSearch = (freeTextSearch: string) => {
    setQueryState((prev) => ({ ...prev, freeTextSearch }));
  };

  const updateSelectedNamespaces = (selectedNamespaces: string[]) => {
    setQueryState((prev) => ({ ...prev, selectedNamespaces }));
  };

  const updateSelectedServices = (selectedServices: string[]) => {
    setQueryState((prev) => ({ ...prev, selectedServices }));
  };

  const resetQuery = () => {
    setQueryState(DEFAULT_QUERY_STATE);
  };

  const savePreset = (name: string, description?: string) => {
    const preset: QueryPreset = {
      id: `preset-${Date.now()}`,
      name,
      description,
      query: queryState,
      createdAt: new Date().toISOString(),
    };
    setPresets((prev) => [...prev, preset]);
  };

  const loadPreset = (id: string) => {
    const preset = presets.find((p) => p.id === id);
    if (preset) {
      setQueryState(preset.query);
    }
  };

  const deletePreset = (id: string) => {
    setPresets((prev) => prev.filter((p) => p.id !== id));
  };

  return (
    <QueryContext.Provider
      value={{
        queryState,
        updateFilters,
        updateTimeRange,
        updateTimeField,
        updateTimezone,
        updateFreeTextSearch,
        updateSelectedNamespaces,
        updateSelectedServices,
        updateLiveMode,
        refreshTimeWindow,
        resetQuery,
        presets,
        savePreset,
        loadPreset,
        deletePreset,
      }}
    >
      {children}
    </QueryContext.Provider>
  );
}

export function useQuery() {
  const context = useContext(QueryContext);
  if (!context) {
    throw new Error('useQuery must be used within a QueryProvider');
  }
  return context;
}
