import { Streamlit, RenderData } from "streamlit-component-lib"

const rootDoc = (typeof window !== "undefined" && window.parent && window.parent.document)
? window.parent.document
: document;

declare global{
  interface Window {
    autogui_instances?: Document[];
  }
}

if (rootDoc.defaultView && !('autogui_instances' in rootDoc.defaultView)) {
  rootDoc.defaultView.autogui_instances = [];
}
rootDoc.defaultView?.autogui_instances?.push(document);

const instance_num = rootDoc.defaultView?.autogui_instances?.indexOf(document);

let component_key = "";


function getButton(){
  return rootDoc.querySelector(`div[class*="${component_key}-autogui-btn"]`)?.querySelector("button");
}


function rerenderButton(){
  const btn = getButton();
  if(btn){
    const op = '0.2';
    btn.style.border = "none";
    btn.style.backgroundImage = `url("data:image/svg+xml,%3csvg width='100%25' height='100%25' xmlns='http://www.w3.org/2000/svg'%3e%3crect width='100%25' height='100%25' fill='none' rx='8' ry='8' stroke='%23333' stroke-width='3' stroke-dasharray='6%2c 14' stroke-dashoffset='0' stroke-linecap='square' stroke-opacity='${op}'/%3e%3c/svg%3e")`;

    const test = rootDoc.defaultView?.getComputedStyle(btn).font;

    if (btn.childNodes.length == 1) {
      const lbl = btn.appendChild(document.createElement("span"))
      lbl.appendChild(document.createTextNode(`Shift + ${(instance_num ?? 0) + 1} to edit`));
      lbl.style.textIndent = "10px";
      lbl.style.fontSize = "12px";
      lbl.style.opacity = op;
      (btn.firstChild as HTMLElement).style.opacity = op;
    }
  }
}

var keydown = function (event: KeyboardEvent) {
  //const isCtrlCmd = event.ctrlKey || event.metaKey;
  const isShift = event.shiftKey;
  const number = "!@#$%^&*()".indexOf(event.key);

  if (event.shiftKey && number > -1) {
    if(number == instance_num){
      getButton()?.click();
      getButton()?.blur();
    }
  }
}

window.addEventListener("load", () => {
    rootDoc.addEventListener("keydown", keydown);
    Streamlit.setComponentReady();
    Streamlit.setFrameHeight(0);
});

window.addEventListener("beforeunload", () => {
    rootDoc.removeEventListener("keydown", keydown);
});
    

function onRender(event: Event): void {
  const data = (event as CustomEvent<RenderData>).detail

  // Maintain compatibility with older versions of Streamlit that don't send
  // a theme object.
  if (data.theme) {
    // Use CSS vars to style our button border. Alternatively, the theme style
    // is defined in the data.theme object.
    //const borderStyling = `1px solid var(${
    //  isFocused ? "--primary-color" : "gray"
    //})`
    //button.style.border = borderStyling
    //button.style.outline = borderStyling
  }

  component_key = data.args["key"]

  //textNode.textContent = `instance num ${(instance_num ?? 0) + 1}`;
  setTimeout(rerenderButton, 100);

  Streamlit.setFrameHeight()
}

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)

Streamlit.setComponentReady()

Streamlit.setFrameHeight()
