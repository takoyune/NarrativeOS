export const state = {
  novels: [],
  selectedNovel: null,
  selectedVolume: null,
  currentMdPath: null,
  mdDirty: false,
  currentPanel: 'overview',
  images: [],
  epubPreviewMode: false,
};

export let pendingAction = null;
export let pendingSelectTarget = null;

export function setPendingAction(action) {
  pendingAction = action;
}

export function setPendingSelectTarget(target) {
  pendingSelectTarget = target;
}
