declare module 'react-cytoscapejs' {
  import { Component } from 'react';
  import cytoscape from 'cytoscape';

  export interface CytoscapeComponentProps {
    elements: cytoscape.ElementDefinition[];
    stylesheet?: cytoscape.Stylesheet[];
    layout?: cytoscape.LayoutOptions;
    style?: React.CSSProperties;
    cy?: (cy: cytoscape.Core) => void;
    pan?: cytoscape.Position;
    zoom?: number;
    minZoom?: number;
    maxZoom?: number;
    zoomingEnabled?: boolean;
    userZoomingEnabled?: boolean;
    panningEnabled?: boolean;
    userPanningEnabled?: boolean;
    boxSelectionEnabled?: boolean;
    autoungrabify?: boolean;
    autounselectify?: boolean;
  }

  export default class CytoscapeComponent extends Component<CytoscapeComponentProps> {}
}
