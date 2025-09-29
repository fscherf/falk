import morphdom from "morphdom";

class Falk {
  public init = () => {
    this.runHook("render");
  };

  public iterNodes = (
    selector: string,
    callback: (node: Element) => any,
    rootNode: Element = document.body,
  ) => {
    if (rootNode.nodeType !== Node.ELEMENT_NODE) {
      return;
    }

    Array.from(rootNode.children).forEach((child) => {
      this.iterNodes(selector, callback, child);
    });

    if (rootNode.matches(selector)) {
      callback(rootNode);
    }
  };

  public runHook = (name: string, rootNode: Element = document.body) => {
    const attributeName: string = `on${name}`;

    this.iterNodes(
      `[${attributeName}]`,
      (element) => {
        const attribute = element.getAttribute(attributeName);
        let fn: Function = new Function(attribute);

        fn.call(element);
      },
      rootNode,
    );
  };

  public dumpEvent = (event: Event) => {
    const eventData = {
      type: "",
      data: undefined,
      formData: {},
    };

    // The event is `undefined` when handling non-standard event handler
    // like `onRender`.
    if (!event) {
      return eventData;
    }

    eventData.type = event.type;

    // input, change, submit
    if (
      event.type == "input" ||
      event.type == "change" ||
      event.type == "submit"
    ) {
      // forms
      if (event.currentTarget instanceof HTMLFormElement) {
        const formData: FormData = new FormData(event.currentTarget);

        for (const [key, value] of formData.entries()) {
          eventData.formData[key] = value;
        }

        // inputs
      } else {
        const inputElement: HTMLInputElement =
          event.currentTarget as HTMLInputElement;

        eventData.data = inputElement.value;

        if (inputElement.hasAttribute("name")) {
          const inputName: string = inputElement.getAttribute("name");

          if (inputName) {
            eventData.formData[inputName] = inputElement.value;
          }
        }
      }
    }

    return eventData;
  };

  public patchNode = (node, newNode) => {
    return morphdom(node, newNode, {
      onBeforeElUpdated: (fromEl, toEl) => {
        // preserve values of input elemente
        if (
          (fromEl instanceof HTMLInputElement &&
            toEl instanceof HTMLInputElement) ||
          (fromEl instanceof HTMLTextAreaElement &&
            toEl instanceof HTMLTextAreaElement) ||
          (fromEl instanceof HTMLSelectElement &&
            toEl instanceof HTMLSelectElement)
        ) {
          toEl.value = fromEl.value;
        }

        return true;
      },
    });
  };

  public patchNodeAttributes = (node, newNode) => {
    return morphdom(node, newNode, {
      onBeforeElChildrenUpdated: (fromEl, toEl) => {
        // ignore all children
        return false;
      },
    });
  };

  public runCallback = (
    event: Event,
    nodeId: string,
    callbackName: string,
    callbackArgs: string,
    stopEvent: boolean,
    delay: number,
  ) => {
    const node = document.querySelector(`[data-falk-id=${nodeId}]`);
    const token = node.getAttribute("data-falk-token");

    const data = {
      requestType: "falk/mutation",
      nodeId: nodeId,
      token: token,
      callbackName: callbackName,
      callbackArgs: JSON.parse(decodeURIComponent(callbackArgs)),
      event: this.dumpEvent(event),
    };

    // The event is `undefined` when handling non-standard event handler
    // like `onRender`.
    if (event && stopEvent) {
      event.stopPropagation();
      event.preventDefault();
    }

    setTimeout(() => {
      fetch(window.location + "", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      }).then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const responseData = await response.json();
        const domParser = new DOMParser();

        const newDocument = domParser.parseFromString(
          responseData.html,
          "text/html",
        );

        // patch entire document
        if (node.tagName == "HTML") {
          // patch the attributes of the HTML node
          // (node id, token, event handlers, ...)
          this.patchNodeAttributes(node, newDocument.children[0]);

          // patch title
          document.title = newDocument.title;

          // patch body
          this.patchNode(document.body, newDocument.body);

          // patch only one node in the body
        } else {
          this.patchNode(node, newDocument.body.firstChild);
        }

        this.runHook("render", node);
      });
    }, delay);
  };
}

window.addEventListener("load", () => {
  window["falk"] = new Falk();

  window["falk"].init();
});
