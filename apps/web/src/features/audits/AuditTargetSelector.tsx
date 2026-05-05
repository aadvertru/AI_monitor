import { Plus, Trash2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import type {
  AuditTarget,
  ModelCatalogFamily,
  ModelCatalogModel,
  SCDLLevel,
} from "../../lib/api/types";
import { useModelCatalog } from "./modelCatalog";

type LevelSelection = Partial<Record<SCDLLevel, boolean>>;

type FamilyBlock = {
  id: string;
  familyId: string;
  selectedModelIds: string[];
  levelsByModelId: Record<string, LevelSelection>;
};

type AuditTargetSelectorProps = {
  value?: AuditTarget[];
  onChange: (targets: AuditTarget[]) => void;
};

function newBlock(familyId: string, index: number): FamilyBlock {
  return {
    id: `${familyId}-${index}`,
    familyId,
    selectedModelIds: [],
    levelsByModelId: {},
  };
}

function buildTarget(
  family: ModelCatalogFamily,
  model: ModelCatalogModel,
  level: SCDLLevel,
): AuditTarget {
  return {
    aiFamily: family.id,
    executionProvider: model.executionProvider,
    modelProvider: model.modelProvider,
    modelId: model.modelId,
    displayName: model.displayName,
    level,
    gateway: model.executionProvider === "openrouter",
    gatewayL2Experimental: level === "L2" && model.l2Experimental,
  };
}

function targetsFromBlocks(
  blocks: FamilyBlock[],
  families: ModelCatalogFamily[],
): AuditTarget[] {
  const targets: AuditTarget[] = [];
  const seen = new Set<string>();

  for (const block of blocks) {
    const family = families.find((item) => item.id === block.familyId);
    if (!family) {
      continue;
    }
    for (const modelId of block.selectedModelIds) {
      const model = family.models.find((item) => item.modelId === modelId);
      if (!model) {
        continue;
      }
      const levels = block.levelsByModelId[modelId] ?? { L1: true };
      for (const level of ["L1", "L2"] as const) {
        if (!levels[level]) {
          continue;
        }
        const key = `${model.executionProvider}:${model.modelId}:${level}`;
        if (seen.has(key)) {
          continue;
        }
        seen.add(key);
        targets.push(buildTarget(family, model, level));
      }
    }
  }

  return targets;
}

function defaultBlocksFromValue(
  value: AuditTarget[] | undefined,
  families: ModelCatalogFamily[],
): FamilyBlock[] {
  if (!value || value.length === 0) {
    return families[0] ? [newBlock(families[0].id, 0)] : [];
  }

  const byFamily = new Map<string, FamilyBlock>();
  for (const target of value) {
    const family = families.find((item) => item.id === target.aiFamily);
    if (!family) {
      continue;
    }
    const block =
      byFamily.get(family.id) ?? newBlock(family.id, byFamily.size);
    if (!block.selectedModelIds.includes(target.modelId)) {
      block.selectedModelIds.push(target.modelId);
    }
    block.levelsByModelId[target.modelId] = {
      ...block.levelsByModelId[target.modelId],
      [target.level]: true,
    };
    byFamily.set(family.id, block);
  }

  return byFamily.size > 0
    ? Array.from(byFamily.values())
    : families[0]
      ? [newBlock(families[0].id, 0)]
      : [];
}

function targetSignature(targets: AuditTarget[] | undefined) {
  return (targets ?? [])
    .map((target) => `${target.aiFamily}:${target.modelId}:${target.level}`)
    .sort()
    .join("|");
}

export function AuditTargetSelector({ value, onChange }: AuditTargetSelectorProps) {
  const catalog = useModelCatalog();
  const families = catalog.data?.families ?? [];
  const [blocks, setBlocks] = useState<FamilyBlock[]>([]);
  const [appliedValueSignature, setAppliedValueSignature] = useState<string | null>(null);
  const emittedSignature = useRef<string | null>(null);
  const targets = useMemo(() => targetsFromBlocks(blocks, families), [blocks, families]);
  const valueSignature = useMemo(() => targetSignature(value), [value]);

  useEffect(() => {
    if (families.length > 0 && appliedValueSignature !== valueSignature) {
      setBlocks(defaultBlocksFromValue(value, families));
      setAppliedValueSignature(valueSignature);
    }
  }, [appliedValueSignature, families, value, valueSignature]);

  useEffect(() => {
    const signature = targetSignature(targets);
    if (signature !== emittedSignature.current) {
      emittedSignature.current = signature;
      onChange(targets);
    }
  }, [onChange, targets]);

  if (catalog.isLoading || catalog.isPending) {
    return (
      <div className="rounded-md border border-border bg-muted p-4 text-sm text-subtle" role="status">
        Loading model catalog...
      </div>
    );
  }

  if (catalog.isError) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">
        Unable to load model catalog.
      </div>
    );
  }

  if (families.length === 0) {
    return (
      <div className="rounded-md border border-border bg-muted p-4 text-sm text-subtle" role="status">
        No model catalog entries are available.
      </div>
    );
  }

  const selectedFamilyIds = new Set(blocks.map((block) => block.familyId));
  const canAddFamily = blocks.length < families.length;

  return (
    <div className="grid gap-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-ink">AI model targets</h2>
          <p className="mt-1 text-sm text-subtle">
            Select AI families, models, and SCDL levels for this audit.
          </p>
        </div>
        <button
          className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium text-ink hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!canAddFamily}
          onClick={() => {
            const nextFamily = families.find((family) => !selectedFamilyIds.has(family.id));
            if (nextFamily) {
              setBlocks((current) => [...current, newBlock(nextFamily.id, current.length)]);
            }
          }}
          type="button"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Add family
        </button>
      </div>

      {blocks.map((block, index) => (
        <FamilySelectorBlock
          block={block}
          families={families}
          key={block.id}
          onChange={(nextBlock) => {
            setBlocks((current) =>
              current.map((item) => (item.id === block.id ? nextBlock : item)),
            );
          }}
          onRemove={
            blocks.length > 1
              ? () => setBlocks((current) => current.filter((item) => item.id !== block.id))
              : undefined
          }
          selectedFamilyIds={selectedFamilyIds}
          title={`AI family ${index + 1}`}
        />
      ))}

      {targets.length === 0 ? (
        <p className="text-sm text-red-600" role="alert">
          Select at least one model target.
        </p>
      ) : null}
    </div>
  );
}

function FamilySelectorBlock({
  block,
  families,
  onChange,
  onRemove,
  selectedFamilyIds,
  title,
}: {
  block: FamilyBlock;
  families: ModelCatalogFamily[];
  onChange: (block: FamilyBlock) => void;
  onRemove?: () => void;
  selectedFamilyIds: Set<string>;
  title: string;
}) {
  const family = families.find((item) => item.id === block.familyId) ?? families[0];
  const selectedModels = family.models.filter((model) =>
    block.selectedModelIds.includes(model.modelId),
  );

  return (
    <section className="rounded-md border border-border bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <label className="grid flex-1 gap-1 text-sm font-medium text-ink">
          {title}
          <select
            className="rounded-md border border-border px-3 py-2 text-sm"
            value={block.familyId}
            onChange={(event) => {
              onChange({
                ...block,
                familyId: event.target.value,
                selectedModelIds: [],
                levelsByModelId: {},
              });
            }}
          >
            {families.map((option) => (
              <option
                disabled={option.id !== block.familyId && selectedFamilyIds.has(option.id)}
                key={option.id}
                value={option.id}
              >
                {option.label}
              </option>
            ))}
          </select>
        </label>
        {onRemove ? (
          <button
            aria-label={`Remove ${family.label}`}
            className="mt-6 inline-flex h-10 w-10 items-center justify-center rounded-md border border-border text-subtle hover:bg-muted"
            onClick={onRemove}
            type="button"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
          </button>
        ) : null}
      </div>

      <fieldset className="mt-4">
        <legend className="text-sm font-medium text-ink">Models</legend>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {family.models.map((model) => (
            <label
              className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm"
              key={model.modelId}
            >
              <input
                checked={block.selectedModelIds.includes(model.modelId)}
                className="h-4 w-4 accent-brand-600"
                onChange={(event) => {
                  const selected = event.target.checked;
                  onChange({
                    ...block,
                    selectedModelIds: selected
                      ? [...block.selectedModelIds, model.modelId]
                      : block.selectedModelIds.filter((id) => id !== model.modelId),
                    levelsByModelId: {
                      ...block.levelsByModelId,
                      [model.modelId]: selected ? { L1: true } : {},
                    },
                  });
                }}
                type="checkbox"
              />
              {model.displayName}
            </label>
          ))}
        </div>
      </fieldset>

      {selectedModels.length > 0 ? (
        <div className="mt-4 grid gap-3">
          {selectedModels.map((model) => (
            <ModelLevelToggles
              block={block}
              key={model.modelId}
              model={model}
              onChange={onChange}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

function ModelLevelToggles({
  block,
  model,
  onChange,
}: {
  block: FamilyBlock;
  model: ModelCatalogModel;
  onChange: (block: FamilyBlock) => void;
}) {
  const levels = block.levelsByModelId[model.modelId] ?? { L1: true };

  function setLevel(level: SCDLLevel, checked: boolean) {
    onChange({
      ...block,
      levelsByModelId: {
        ...block.levelsByModelId,
        [model.modelId]: {
          ...levels,
          [level]: checked,
        },
      },
    });
  }

  return (
    <div className="rounded-md border border-border bg-muted px-3 py-3">
      <p className="text-sm font-medium text-ink">{model.displayName}</p>
      <div className="mt-2 flex flex-wrap gap-3">
        <label className="inline-flex items-center gap-2 text-sm">
          <input
            aria-label={`${model.displayName} L1`}
            checked={Boolean(levels.L1)}
            className="h-4 w-4 accent-brand-600"
            disabled={!model.supportsL1}
            onChange={(event) => setLevel("L1", event.target.checked)}
            type="checkbox"
          />
          L1
        </label>
        <label
          className="inline-flex items-center gap-2 text-sm"
          title={model.supportsL2Gateway ? undefined : "L2 is not available for this model."}
        >
          <input
            aria-label={`${model.displayName} L2`}
            checked={Boolean(levels.L2)}
            className="h-4 w-4 accent-brand-600"
            disabled={!model.supportsL2Gateway}
            onChange={(event) => setLevel("L2", event.target.checked)}
            type="checkbox"
          />
          L2
          {model.l2Experimental ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
              Experimental
            </span>
          ) : null}
        </label>
      </div>
    </div>
  );
}
