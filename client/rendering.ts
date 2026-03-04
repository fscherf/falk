import morphdom from "morphdom";

const FALK_NODE_ID_ATTRIBUTE_NAME = "fx-id";
const FALK_RENDER_ATTRIMUTE_NAME = "fx-render";

// basic checks
export function nodeIsElement(node: Node) {
  return node.nodeType == Node.ELEMENT_NODE;
}

export function nodeIsUiNode(node: HTMLElement) {
  return !["SCRIPT", "LINK", "STYLE"].includes(node.tagName);
}

// node ids
export function nodeHasFalkNodeId(node: HTMLElement) {
  return node.hasAttribute(FALK_NODE_ID_ATTRIBUTE_NAME);
}

export function getFalkNodeId(node: HTMLElement) {
  return node.getAttribute(FALK_NODE_ID_ATTRIBUTE_NAME);
}

// render modes
export function getChildrenRenderMode(node: HTMLElement) {
  const modeString = node.getAttribute(FALK_RENDER_ATTRIMUTE_NAME) || "";

  if (modeString.includes("children-skip")) {
    return "skip";
  } else if (modeString.includes("children-prepend")) {
    return "prepend";
  } else if (modeString.includes("children-append")) {
    return "append";
  }

  return "update";
}

// helper
export function iterFalkComponents(options: {
  rootNode: HTMLElement;
  callback: (node: HTMLElement) => any;
  skipNodes?: Array<HTMLElement>;
}) {
  if (!options.skipNodes) {
    options.skipNodes = new Array();
  }

  Array.from(options.rootNode.children).forEach((child: HTMLElement) => {
    if (options.skipNodes.includes(child)) {
      return;
    }

    if (!nodeIsUiNode(child)) {
      return;
    }

    iterFalkComponents({
      rootNode: child,
      callback: options.callback,
      skipNodes: options.skipNodes,
    });
  });

  if (!nodeHasFalkNodeId(options.rootNode)) {
    return;
  }

  options.callback(options.rootNode);
}

// node patching
export function patchNode(options: {
  fromNode: HTMLElement;
  toNode: HTMLElement;
  eventType: string;
  onInitialRender: (node: HTMLElement) => any;
  onRender: (node: HTMLElement) => any;
  onBeforeUnmount: (node: HTMLElement) => any;
}) {
  // TODO: add tests for render modes
  // TODO: add tests for preserving form input

  // patch nodes
  const skipNodes: Array<HTMLElement> = new Array();

  morphdom(options.fromNode, options.toNode, {
    getNodeKey: (node: HTMLElement) => {
      if (!nodeIsElement(node)) {
        return;
      }

      // If the given node has set a render mode
      // (`fx-render="children-append"`), we need a user set id (`Node.id`) to
      // correctly identify the new and the old node because the falk node id
      // (`fx-id`) is short lived and not reproducible.
      if (node.hasAttribute(FALK_RENDER_ATTRIMUTE_NAME)) {
        return node.id;
      }

      if (nodeHasFalkNodeId(node)) {
        return getFalkNodeId(node);
      }

      return node.id;
    },

    onBeforeElUpdated: (fromEl: HTMLElement, toEl: HTMLElement) => {
      // Preserve values of input elements if the original event is no
      // `submit` event.
      // Normally, we don't want to override user input from the backend
      // because this almost always results in bad user experience, but when
      // submitting a form, the expected behavior is that the form
      // clears afterwards.
      // To make the backend code able to render an empty form after a
      // successful submit, or containing the submitted values in case of an
      // error, we take the new form as is and discard local values.
      if (
        options.eventType != "submit" &&
        ((fromEl instanceof HTMLInputElement &&
          toEl instanceof HTMLInputElement) ||
          (fromEl instanceof HTMLTextAreaElement &&
            toEl instanceof HTMLTextAreaElement) ||
          (fromEl instanceof HTMLSelectElement &&
            toEl instanceof HTMLSelectElement))
      ) {
        toEl.value = fromEl.value;
      }

      return true;
    },

    onBeforeElChildrenUpdated: (fromEl: HTMLElement, toEl: HTMLElement) => {
      // remove non-UI nodes
      // We never add scripts or styles while rendering. Only while loading.
      toEl
        .querySelectorAll("link,style,script")
        .forEach((node: HTMLElement) => {
          node.remove();
        });

      const childrenRendernMode: string = getChildrenRenderMode(fromEl);

      // render mode: update (default)
      if (childrenRendernMode == "update") {
        // we just let morphdom continue

        return true;
      } else {
        // render mode: skip/prepend/append
        //
        // We mark all preexisting child nodes that we did not touch so we do
        // not dispatch render events on them later.
        Array.from(fromEl.children).forEach((node: Node) => {
          if (!nodeIsElement(node)) {
            return;
          }

          skipNodes.push(node as HTMLElement);
        });
      }

      // render mode: skip
      if (childrenRendernMode == "skip") {
        // We do nothing and signal to morphdom to ignore this node.
        return false;

        // render mode: prepend
      } else if (childrenRendernMode == "prepend") {
        // We prepend the child nodes our self and signal to morphdom to ignore
        // this node.
        Array.from(toEl.childNodes)
          .reverse()
          .forEach((node: Node) => {
            fromEl.insertBefore(node, fromEl.firstChild);
          });

        return false;

        // render mode: append
      } else if (childrenRendernMode == "append") {
        // We append the child nodes our self and signal to morphdom to ignore
        // this node.
        Array.from(toEl.childNodes).forEach((node: Node) => {
          fromEl.appendChild(node);
        });

        return false;
      }
    },

    onBeforeNodeDiscarded: (node: Node) => {
      // We never discard scripts or styles while rendering.
      if (!nodeIsUiNode(node as HTMLElement)) {
        return false;
      }

      // find all components and dispatch `beforeunmount` events
      //
      // We need to do this here instead of at the end like the render events
      // in order to give the application code a chance to do tear down while
      // the node still exists and is mounted to the document.
      if (nodeIsElement(node)) {
        iterFalkComponents({
          rootNode: node as HTMLElement,
          callback: (componentRootNode: HTMLElement) => {
            options.onBeforeUnmount(componentRootNode);
          },
        });
      }

      // discard the node normally
      return true;
    },
  });

  // dispatch render events
  //
  // We need to do this outside the morphdom call to maintain the correct order
  // of life cycle events (unmount the previous node, initial render of the new
  // node, render of the new node).
  iterFalkComponents({
    rootNode: options.fromNode,
    skipNodes: skipNodes,
    callback: (componentRootNode: HTMLElement) => {
      if (componentRootNode != options.fromNode) {
        options.onInitialRender(componentRootNode);
      }

      options.onRender(componentRootNode);
    },
  });
}

export function patchNodeAttributes(options: {
  fromNode: HTMLElement;
  toNode: HTMLElement;
  onRender: (node: HTMLElement) => any;
}) {
  // patch node
  morphdom(options.fromNode, options.toNode, {
    onBeforeElChildrenUpdated: (fromEl: HTMLElement, toEl: HTMLElement) => {
      // ignore all children
      return false;
    },
  });

  // dispatch render event
  options.onRender(options.fromNode);
}
