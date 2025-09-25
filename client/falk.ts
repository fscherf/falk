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

  public runCallback = (
    nodeId: string,
    callbackName: string,
    delay: number,
  ) => {
    const node = document.querySelector(`[data-falk-id=${nodeId}]`);
    const token = node.getAttribute("data-falk-token");

    const data = {
      nodeId: nodeId,
      token: token,
      callbackName: callbackName,
    };

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
        const template = document.createElement("template");

        template.innerHTML = responseData.html.trim();

        morphdom(node, template.content.firstElementChild, {
          onBeforeElUpdated: (fromEl, toEl) => {
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

        this.runHook("render", node);
      });
    }, delay);
  };
}

window.addEventListener("load", () => {
  window["falk"] = new Falk();

  window["falk"].init();
});
