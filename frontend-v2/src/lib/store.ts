import { create } from 'zustand';
import { Sample, Result, StageKey, ProcessStatus } from './types';
import { getSamples, runRemoval } from './api';

interface State {
  samples: Sample[];
  selectedId: string | null;
  statusMap: Record<string, ProcessStatus>;
  resultsMap: Record<string, Result>;
  processingDurationMap: Record<string, number>;
  activeStage: StageKey;
  isCompareMode: boolean;
  compareLeft: StageKey;
  compareRight: StageKey;
  maskOverlay: boolean;
  maskOpacity: number;
  inspectExpanded: boolean;
  filterCoverage: 'all' | 'light' | 'medium' | 'heavy';
  sortBy: 'coverage_asc' | 'coverage_desc' | 'name';
  isMobileGalleryOpen: boolean;
  errorMessage: string | null;
  isLoadingSamples: boolean;
  hasViewedCachedMap: Record<string, boolean>; // tracks if user clicked "View previous result" for cached item
}

interface Actions {
  loadInitialSamples: (deepLinkId?: string | null) => Promise<void>;
  selectSample: (id: string) => void;
  navigateSample: (direction: 'prev' | 'next') => void;
  runRemovalForCurrent: () => Promise<void>;
  viewCachedResult: (id?: string) => void;
  retryRemoval: () => Promise<void>;
  setActiveStage: (stage: StageKey) => void;
  toggleCompareMode: () => void;
  setCompareMode: (enabled: boolean) => void;
  setCompareStages: (left: StageKey, right: StageKey) => void;
  swapCompareStages: () => void;
  setMaskOverlay: (enabled: boolean) => void;
  setMaskOpacity: (opacity: number) => void;
  setInspectExpanded: (expanded: boolean) => void;
  setFilterCoverage: (filter: 'all' | 'light' | 'medium' | 'heavy') => void;
  setSortBy: (sort: 'coverage_asc' | 'coverage_desc' | 'name') => void;
  setMobileGalleryOpen: (open: boolean) => void;
}

function prefetchPreviews(sample: Sample | undefined) {
  if (!sample || typeof window === 'undefined') return;
  const urls = [sample.previews.cloudy, sample.previews.sar, sample.previews.mask];
  urls.forEach((url) => {
    if (url) {
      const img = new Image();
      img.src = url;
    }
  });
}

function updateUrlDeepLink(id: string) {
  if (typeof window === 'undefined') return;
  const url = new URL(window.location.href);
  url.searchParams.set('id', id);
  window.history.replaceState({}, '', url.toString());
}

export const useAppStore = create<State & Actions>((set, get) => ({
  samples: [],
  selectedId: null,
  statusMap: {},
  resultsMap: {},
  processingDurationMap: {},
  activeStage: 'final',
  isCompareMode: false,
  compareLeft: 'cloudy',
  compareRight: 'final',
  maskOverlay: false,
  maskOpacity: 0.6,
  inspectExpanded: true,
  filterCoverage: 'all',
  sortBy: 'coverage_asc',
  isMobileGalleryOpen: false,
  errorMessage: null,
  isLoadingSamples: true,
  hasViewedCachedMap: {},

  loadInitialSamples: async (deepLinkId?: string | null) => {
    try {
      set({ isLoadingSamples: true, errorMessage: null });
      const samples = await getSamples();
      
      let targetId = samples[0]?.id ?? null;
      if (deepLinkId && samples.some((s) => s.id === deepLinkId)) {
        targetId = deepLinkId;
      }

      set({
        samples,
        selectedId: targetId,
        isLoadingSamples: false,
        inspectExpanded: true,
      });

      if (targetId) {
        updateUrlDeepLink(targetId);
        // Prefetch target and neighbours
        const targetIndex = samples.findIndex((s) => s.id === targetId);
        prefetchPreviews(samples[targetIndex]);
        if (targetIndex > 0) prefetchPreviews(samples[targetIndex - 1]);
        if (targetIndex < samples.length - 1) prefetchPreviews(samples[targetIndex + 1]);
      }
    } catch (err: unknown) {
      set({
        isLoadingSamples: false,
        errorMessage:
          (err instanceof Error && err.message) ||
          "Can't reach the model server. Start it with hf_deploy/local/run_backend (see hf_deploy/local/LOCAL_SETUP.md) and check BACKEND_URL.",
      });
    }
  },

  selectSample: (id: string) => {
    const { samples, selectedId } = get();
    if (id === selectedId) return;

    // STATE RULE:
    // Selecting any image resets the workspace: Inspect OPEN, Processing and Results in the waiting state.
    // If that image already has a cached result, show its check mark and a "View previous result" button
    // inside the Results section instead of auto-opening it.
    set((state) => ({
      selectedId: id,
      inspectExpanded: true,
      activeStage: 'final',
      isCompareMode: false,
      errorMessage: null,
      statusMap: {
        ...state.statusMap,
        [id]: 'idle', // resets to idle waiting state
      },
      hasViewedCachedMap: {
        ...state.hasViewedCachedMap,
        [id]: false,
      },
    }));

    updateUrlDeepLink(id);

    // Prefetch neighbours
    const currentIndex = samples.findIndex((s) => s.id === id);
    if (currentIndex !== -1) {
      prefetchPreviews(samples[currentIndex]);
      if (currentIndex > 0) prefetchPreviews(samples[currentIndex - 1]);
      if (currentIndex < samples.length - 1) prefetchPreviews(samples[currentIndex + 1]);
    }
  },

  navigateSample: (direction: 'prev' | 'next') => {
    const { samples, selectedId } = get();
    if (!samples.length || !selectedId) return;

    const currentIndex = samples.findIndex((s) => s.id === selectedId);
    if (currentIndex === -1) return;

    let nextIndex = direction === 'next' ? currentIndex + 1 : currentIndex - 1;
    if (nextIndex < 0) nextIndex = samples.length - 1;
    if (nextIndex >= samples.length) nextIndex = 0;

    const nextSample = samples[nextIndex];
    if (nextSample) {
      get().selectSample(nextSample.id);
    }
  },

  runRemovalForCurrent: async () => {
    const { selectedId, statusMap } = get();
    if (!selectedId) return;
    if (statusMap[selectedId] === 'running') return;

    const startTime = performance.now();

    set((state) => ({
      statusMap: { ...state.statusMap, [selectedId]: 'running' },
      inspectExpanded: false,
      errorMessage: null,
    }));

    try {
      const minWait = new Promise((resolve) => setTimeout(resolve, 800));
      const [result] = await Promise.all([runRemoval(selectedId), minWait]);

      const endTime = performance.now();
      const durationSec = Math.round(((endTime - startTime) / 1000) * 10) / 10;

      set((state) => ({
        resultsMap: {
          ...state.resultsMap,
          [selectedId]: result,
        },
        processingDurationMap: {
          ...state.processingDurationMap,
          [selectedId]: durationSec,
        },
        statusMap: {
          ...state.statusMap,
          [selectedId]: 'done',
        },
        hasViewedCachedMap: {
          ...state.hasViewedCachedMap,
          [selectedId]: true,
        },
        activeStage: 'final',
      }));
    } catch (err: unknown) {
      set((state) => ({
        statusMap: {
          ...state.statusMap,
          [selectedId]: 'error',
        },
        inspectExpanded: true,
        errorMessage:
          (err instanceof Error && err.message) ||
          "Can't reach the model server. Start it with hf_deploy/local/run_backend (see hf_deploy/local/LOCAL_SETUP.md) and check BACKEND_URL.",
      }));
    }
  },

  viewCachedResult: (id?: string) => {
    const targetId = id ?? get().selectedId;
    if (!targetId) return;
    if (get().resultsMap[targetId]) {
      set((state) => ({
        statusMap: {
          ...state.statusMap,
          [targetId]: 'done',
        },
        hasViewedCachedMap: {
          ...state.hasViewedCachedMap,
          [targetId]: true,
        },
        inspectExpanded: false,
        activeStage: 'final',
      }));
    }
  },

  retryRemoval: async () => {
    await get().runRemovalForCurrent();
  },

  setActiveStage: (stage: StageKey) => {
    set({ activeStage: stage });
  },

  toggleCompareMode: () => {
    set((state) => ({ isCompareMode: !state.isCompareMode }));
  },

  setCompareMode: (enabled: boolean) => {
    set({ isCompareMode: enabled });
  },

  setCompareStages: (left: StageKey, right: StageKey) => {
    set({ compareLeft: left, compareRight: right });
  },

  swapCompareStages: () => {
    set((state) => ({
      compareLeft: state.compareRight,
      compareRight: state.compareLeft,
    }));
  },

  setMaskOverlay: (enabled: boolean) => {
    set({ maskOverlay: enabled });
  },

  setMaskOpacity: (opacity: number) => {
    set({ maskOpacity: opacity });
  },

  setInspectExpanded: (expanded: boolean) => {
    set({ inspectExpanded: expanded });
  },

  setFilterCoverage: (filter: 'all' | 'light' | 'medium' | 'heavy') => {
    set({ filterCoverage: filter });
  },

  setSortBy: (sort: 'coverage_asc' | 'coverage_desc' | 'name') => {
    set({ sortBy: sort });
  },

  setMobileGalleryOpen: (open: boolean) => {
    set({ isMobileGalleryOpen: open });
  },
}));
