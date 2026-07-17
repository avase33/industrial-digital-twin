export interface Incident {
  severity: string;
  kind: string;
  summary: string;
  repair: string[];
}

export interface TwinNode {
  node: string;
  health: number;
  anomaly: boolean;
  pos: [number, number, number];
  incident?: Incident | null;
}

export interface TwinUpdate {
  ts: number;
  nodes: TwinNode[];
}
