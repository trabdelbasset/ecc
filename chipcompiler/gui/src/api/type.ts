export enum CMDEnum {
  create_workspace = "create_workspace",
  load_workspace = "load_workspace",
  delete_workspace = "delete_workspace",
  rtl2gds = "rtl2gds",
  run_step = "run_step",
  get_info = "get_info"
}

// get_info command 的 id 枚举
export enum InfoEnum {
  views = "views",
  layout = "layout",
  metrics = "metrics",
  subflow = "subflow",
  analysis = "analysis",
  maps = "maps",
  checklist = "checklist"
}

export enum StepEnum {
  SYNTHESIS = "Synthesis",
  FLOORPLAN = "Floorplan",
  PLACEMENT = "place",
  CTS = "CTS",
  ROUTING = "route",
  SIGNOFF = "Signoff",
  DRC = "drc",
  FILLER = "filler",
}

export enum ResponseEnum {
  success = "success",
  failed = "failed",
  error = "error",
  warning = "warning"
}

export interface RequestData<T> {
  cmd: CMDEnum;
  data: T;
}

export interface ResponseData<T> {
  cmd: CMDEnum;
  response: ResponseEnum;
  data: T;
  message: string[];
}

