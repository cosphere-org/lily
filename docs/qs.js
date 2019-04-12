class QueryParams {

    constructor () {
        this.params = {
            entrypointUri: null,
            query: null,
            selectedElement: null,
            selectedAccessRole: null,
        };
    }

    parse () {
        let parsed = Qs.parse(window.location.hash.slice(1));

        if (parsed.entrypointUri) {
            this.params.entrypointUri = parsed.entrypointUri;
        }

        if (parsed.query) {
            this.params.query = parsed.query;
        }

        if (parsed.selectedElement) {
            this.params.selectedElement = parsed.selectedElement;
        }

        if (parsed.selectedAccessRole) {
            this.params.selectedAccessRole = parsed.selectedAccessRole;
        }

        return this.params;
    }

    setEntrypointUri(entrypointUri) {
        this.params.entrypointUri = entrypointUri;
        this.set();
    }

    setQuery(query) {
        this.params.query = query;
        this.set();
    }

    setSelectedElement(selectedElement) {
        this.params.selectedElement = selectedElement;
        this.set();
    }

    setSelectedAccessRole(selectedAccessRole) {
        this.params.selectedAccessRole = selectedAccessRole;
        this.set();
    }

    set() {
        let params = Qs.stringify(this.removeNull(this.params));
        window.location.hash = `${params}`;
    }

    removeNull (obj) {
        let clean = {};
        Object.keys(obj).forEach(key => {
            if (obj[key] !== null) {
                clean[key] = obj[key];
            }
        });

        return clean;
    }
}
