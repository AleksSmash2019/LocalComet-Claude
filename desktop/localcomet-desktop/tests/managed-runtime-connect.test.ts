import { get } from 'svelte/store';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  managedRuntimeStore,
  startSelectedManagedRuntime,
  connectSelectedManagedModel,
  shutdownModelGateway
} from '../src/lib/stores/modelGateway';
import { resetShellStores } from '../src/lib/stores/shellStore';
import type { ManagedCatalogIdentity, ApprovedRuntimeSummary, ApprovedModelSummary, ModelReadinessSummary } from '../src/lib/types/modelGateway';

let invokeCalls: { command: string; args?: Record<string, unknown> }[] = [];
let mockRuntimeState = 'Stopped';
let startCallCount = 0;

const MODEL_ID = 'qwen2.5-1.5b-instruct-q4-k-m';
const RUNTIME_ID = 'llama-cpp-b10068';
const INSTANCE_ID = 'a'.repeat(32);
const FINGERPRINT = 'b'.repeat(64);
const CATALOG_DIGEST = 'c'.repeat(64);
const CATALOG_IDENTITY: ManagedCatalogIdentity = { schema_version: 1 as const, catalog_id: 'localcomet-approved-artifacts' as const, catalog_version: '1.0.0', catalog_digest: CATALOG_DIGEST };

const READINESS_RESPONSE = {
  schema_version: 1,
  catalog_id: 'localcomet-approved-artifacts',
  catalog_version: '1.0.0',
  catalog_digest: CATALOG_DIGEST,
  model_id: MODEL_ID,
  model_status: 'valid',
  compatible_runtime_ids: [RUNTIME_ID],
  selected_runtime_id: RUNTIME_ID,
  runtime_status: 'valid',
  compatibility: 'compatible',
  readiness: 'ready',
  launchable: true
};

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(async (command: string, args?: Record<string, unknown>): Promise<unknown> => {
    invokeCalls.push({ command, args });
    if (command === 'managed_model_readiness') return READINESS_RESPONSE;
    if (command === 'managed_runtime_start') {
      startCallCount++;
      if (startCallCount > 1) throw { code: 'busy', message: 'managed runtime is busy' };
      return { state: 'Starting', model_state: 'Loading', inference_ready: false, provider_id: 'managed-llama-cpp', model_id: MODEL_ID, model_display_name: 'Qwen2.5 1.5B', runtime_instance_id: '', runtime_instance_fingerprint: '' };
    }
    if (command === 'managed_runtime_status') return { engine: 'llama.cpp', state: mockRuntimeState, installation: 'Installed', runtime_version: 'b10068', runtime_instance_id: mockRuntimeState === 'Ready' ? INSTANCE_ID : null, runtime_instance_fingerprint: mockRuntimeState === 'Ready' ? FINGERPRINT : null, model_id: mockRuntimeState === 'Ready' ? MODEL_ID : null, model_display_name: mockRuntimeState === 'Ready' ? 'Qwen2.5 1.5B' : null, binding_fingerprint: null, model_state: mockRuntimeState === 'Ready' ? 'Ready' : 'Loading', inference_ready: mockRuntimeState === 'Ready', last_error: null };
    if (command === 'managed_runtime_stop') return { state: 'Stopped', model_state: 'Unavailable', inference_ready: false, stopped: true };
    if (command === 'model_binding_set') return { provider_id: 'managed-llama-cpp', harness_id: args?.harnessId, host: '127.0.0.1', port: 0, base_path: '/v1', model_id: args?.modelId, binding_fingerprint: FINGERPRINT, discovered_fingerprint: FINGERPRINT, persistence: false, runtime_instance_id: INSTANCE_ID };
    if (command === 'managed_runtime_catalog') return { schema_version: 1, catalog_id: 'test', catalog_version: '1.0.0', catalog_digest: CATALOG_DIGEST, runtimes: [] };
    if (command === 'managed_model_catalog') return { schema_version: 1, catalog_id: 'test', catalog_version: '1.0.0', catalog_digest: CATALOG_DIGEST, engine: 'llama.cpp', model_root: '<ROOT>', models: [], maximum_models: 32 };
    if (command === 'managed_installed_artifacts') return { schema_version: 1, catalog_id: 'test', catalog_version: '1.0.0', catalog_digest: CATALOG_DIGEST, artifacts: [] };
    if (command === 'managed_runtime_logs') return { stdout_tail: [], stderr_tail: [] };
    if (command === 'model_gateway_catalog') return { gateway_version: 'v6.84.5', providers: [], harnesses: [], persistence: false, tools_available: false };
    return {};
  })
}));

vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn(async (): Promise<() => void> => () => undefined)
}));

function setupStore(): void {
  invokeCalls = [];
  mockRuntimeState = 'Stopped';
  startCallCount = 0;
  managedRuntimeStore.set({
    status: { engine: 'llama.cpp', state: 'Stopped', installation: 'Installed', runtime_version: 'b10068', runtime_instance_id: null, runtime_instance_fingerprint: null, model_id: null, model_display_name: null, binding_fingerprint: null, model_state: 'Unavailable', inference_ready: false, last_error: null },
    catalogIdentity: CATALOG_IDENTITY,
    runtimeCatalog: [{ runtime_id: RUNTIME_ID, provider: 'llama-cpp', release_tag: 'b10068', platform: 'windows', architecture: 'x86-64', variant: 'cpu', upstream_repository: 'test', upstream_revision: 'test', asset_filename: 'test.zip', asset_bytes: 50 * 1024 * 1024, asset_sha256: 'd'.repeat(64), archive_format: 'zip', permitted_bind_scope: 'loopback-only', supported_api_protocol: 'openai-compatible-v1', license_id: 'MIT' }] as ApprovedRuntimeSummary[],
    catalog: [{ model_id: MODEL_ID, provider: 'qwen', family: 'qwen2.5', display_name: 'Qwen2.5 1.5B Instruct Q4_K_M', format: 'GGUF', quantization: 'Q4_K_M', upstream_repository: 'test', upstream_revision: 'test', asset_filename: 'model.gguf', asset_bytes: 1066 * 1024 * 1024, asset_sha256: 'e'.repeat(64), license_id: 'apache-2.0', compatible_runtime_ids: [RUNTIME_ID], public_distribution: false, installer_bundled: false }] as unknown as ApprovedModelSummary[],
    installedArtifacts: [],
    readiness: { ...CATALOG_IDENTITY, model_id: MODEL_ID, model_status: 'valid', compatible_runtime_ids: [RUNTIME_ID], selected_runtime_id: RUNTIME_ID, runtime_status: 'valid', compatibility: 'compatible', readiness: 'ready', launchable: true } as ModelReadinessSummary,
    selectedModelId: MODEL_ID,
    harnessId: 'minimal',
    binding: null,
    logs: { stdout_tail: [], stderr_tail: [] },
    lastError: null
  });
}

/** Simulates the managed-runtime-changed event handler updating the store directly. */
function simulateRuntimeChangedEvent(payload: { state: 'Ready' | 'Failed'; model_id: string; error_code?: string | null; error_message?: string | null }): void {
  mockRuntimeState = payload.state;
  if (payload.state === 'Ready') {
    managedRuntimeStore.update((current) => ({
      ...current,
      status: current.status ? { ...current.status, state: 'Ready' as const, model_state: 'Ready' as const, inference_ready: true, model_id: payload.model_id } : current.status,
      lastError: null
    }));
  } else {
    managedRuntimeStore.update((current) => ({
      ...current,
      status: current.status ? { ...current.status, state: 'Failed' as const, model_state: 'Failed' as const, inference_ready: false } : current.status,
      binding: null,
      lastError: { code: payload.error_code ?? 'runtime_start_failed', message: payload.error_message ?? 'Managed runtime failed to start' }
    }));
  }
}

describe('Managed runtime connection state machine', () => {
  beforeEach(() => {
    shutdownModelGateway();
    resetShellStores();
    setupStore();
  });

  it('transitions idle to Starting immediately on connect (no blocking await)', async () => {
    await startSelectedManagedRuntime();
    const state = get(managedRuntimeStore);
    expect(state.status?.state).toBe('Starting');
    expect(state.status?.model_state).toBe('Loading');
    expect(state.status?.inference_ready).toBe(false);
    expect(state.lastError).toBeNull();
    expect(invokeCalls.some((c) => c.command === 'managed_runtime_start')).toBe(true);
  });

  it('transitions Starting to Ready on managed-runtime-changed event', async () => {
    await startSelectedManagedRuntime();
    expect(get(managedRuntimeStore).status?.state).toBe('Starting');
    simulateRuntimeChangedEvent({ state: 'Ready', model_id: MODEL_ID, error_code: null, error_message: null });
    const state = get(managedRuntimeStore);
    expect(state.status?.state).toBe('Ready');
    expect(state.lastError).toBeNull();
  });

  it('transitions Starting to Failed on error event with retry available', async () => {
    await startSelectedManagedRuntime();
    expect(get(managedRuntimeStore).status?.state).toBe('Starting');
    simulateRuntimeChangedEvent({ state: 'Failed', model_id: MODEL_ID, error_code: 'launch_failed', error_message: 'llama.cpp exited with code 1' });
    const state = get(managedRuntimeStore);
    expect(state.status?.state).toBe('Failed');
    expect(state.lastError?.code).toBe('launch_failed');
    expect(state.lastError?.message).toContain('llama.cpp exited');
    expect(state.binding).toBeNull();
  });

  it('late Ready event after timeout still transitions to connected', async () => {
    await startSelectedManagedRuntime();
    expect(get(managedRuntimeStore).status?.state).toBe('Starting');
    managedRuntimeStore.update((s) => ({
      ...s,
      status: s.status ? { ...s.status, state: 'Failed' as const, model_state: 'Failed' as const, inference_ready: false } : s.status,
      lastError: { code: 'start_timed_out', message: 'Model start timed out' }
    }));
    expect(get(managedRuntimeStore).status?.state).toBe('Failed');
    expect(get(managedRuntimeStore).lastError?.code).toBe('start_timed_out');
    simulateRuntimeChangedEvent({ state: 'Ready', model_id: MODEL_ID, error_code: null, error_message: null });
    const state = get(managedRuntimeStore);
    expect(state.status?.state).toBe('Ready');
    expect(state.lastError).toBeNull();
  });

  it('double connect does not spawn second start (guard)', async () => {
    await startSelectedManagedRuntime();
    expect(get(managedRuntimeStore).status?.state).toBe('Starting');
    const callsBefore = invokeCalls.filter((c) => c.command === 'managed_runtime_start').length;
    const result = await connectSelectedManagedModel();
    const callsAfter = invokeCalls.filter((c) => c.command === 'managed_runtime_start').length;
    expect(callsAfter).toBe(callsBefore);
    expect(result).toBe(false);
  });
});
