/**
 * Project API module for ChipCompiler
 */

import { alovaInstance } from './client'

// Types for API requests and responses
export interface ProjectInfo {
  name: string
  path: string
  flow?: Record<string, unknown>
}

export interface ProjectResponse {
  status: 'success' | 'error'
  message?: string
  project?: ProjectInfo
}

export interface OpenProjectRequest {
  path: string
}

export interface CreateProjectRequest {
  path: string
  name?: string
  description?: string
  design_files?: string[]
  top_module?: string
  pdk?: string
  technology_node?: string
  target_frequency?: number
}

/**
 * Open an existing project
 * @param path - Full path to the project directory
 */
export function openProjectApi(path: string) {
  return alovaInstance.Post<ProjectResponse>('/api/project/open', {
    path
  } as OpenProjectRequest)
}

/**
 * Create a new project
 * @param path - Parent directory where the project will be created
 * @param name - Name of the new project (optional, defaults to "New_Chip_Design")
 * @param options - Additional project configuration options from wizard
 */
export function createProjectApi(
  path: string,
  name?: string,
  options?: {
    description?: string
    designFiles?: string[]
    topModule?: string
    pdk?: string
    technologyNode?: string
    targetFrequency?: number
  }
) {
  return alovaInstance.Post<ProjectResponse>('/api/project/create', {
    path,
    name: name || 'New_Chip_Design',
    description: options?.description,
    design_files: options?.designFiles,
    top_module: options?.topModule,
    pdk: options?.pdk,
    technology_node: options?.technologyNode,
    target_frequency: options?.targetFrequency
  } as CreateProjectRequest)
}

/**
 * Check project API health
 */
export function checkProjectApiHealth() {
  return alovaInstance.Get<{ status: string }>('/api/project/health')
}
