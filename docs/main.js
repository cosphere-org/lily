
$(document).ready(() => {

    let state = new State();
    let dom = new DOMRenderer(state);

    state.init().then(() => {
        dom.refresh();
    });
});
