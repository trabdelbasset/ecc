export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'image'
  status?: 'loading' | 'done' | 'error'
  image?: {
    url: string
    label?: string
    dimensions?: string
    thumbnailId?: number
    description?: string
  }
}

export interface Thumbnail {
  id: number
  label: string
  description?: string
  thumbnailUrl?: string
  imageUrl?: string
  size?: string
  dimensions?: string
  format?: string
}

export interface Project {
  id: string
  name: string
  path: string
  lastOpened: Date
}

// New Project Wizard Types
export interface ProjectConfig {
  // Step 1: Basic Info
  name: string
  description: string
  location: string
  
  // Step 2: Design Files
  designFiles: DesignFile[]
  topModule: string
  
  // Step 3: Technology Config
  pdk: string
  technologyNode: string
  targetFrequency: number
  
  // Step 4: Constraints (optional)
  constraintFiles: DesignFile[]
}

export interface DesignFile {
  id: string
  name: string
  path: string
  type: 'verilog' | 'vhdl' | 'systemverilog' | 'constraint' | 'other'
  size?: number
}

export interface WizardStep {
  id: number
  title: string
  description: string
  isCompleted: boolean
  isActive: boolean
}
