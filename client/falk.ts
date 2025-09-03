import morphdom from "morphdom";

const runCallback = (nodeId, callbackName, delay) => {
  const node = document.querySelector(`[data-falk-id=${nodeId}]`);
  const token = node.getAttribute("data-falk-token");

  const data = {
    nodeId: nodeId,
    token: token,
    callbackName: callbackName,
  };

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
  });
};

window.addEventListener("load", () => {
  (window as any).falk = {
    runCallback: runCallback,
  };
});
