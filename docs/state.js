
/**
 * Managing the state of the app
 */
class State {

    constructor() {
        this.qs = new QueryParams();

        this.state = {
            entrypointUri: null,
            query: null,
            selectedElement: null,
            selectedAccessRole: null,
            selectedCommands: [],
            allCommands: [],
            allDomains: [],
        };
    }

    init() {
        this.qs.parse();
        let params = this.qs.params;

        return new Promise(resolve => {
            if (params.entrypointUri !== null) {
                this.updateWithEntrypointURI(params.entrypointUri).then(() => {

                    if (params.selectedElement !== null) {
                        this.updateWithSelectedElement(params.selectedElement);
                    }

                    if (params.selectedAccessRole !== null) {
                        this.updateWithSelectedAccessRole(params.selectedAccessRole);

                    }

                    if (params.query !== null) {
                        this.updateWithQuery(params.query);

                    }

                    resolve();
                });

            } else {
                if (params.selectedElement !== null) {
                    this.updateWithSelectedElement(params.selectedElement);

                }

                if (params.selectedAccessRole !== null) {
                    this.updateWithSelectedAccessRole(params.selectedAccessRole);

                }

                if (params.query !== null) {
                    this.updateWithQuery(params.query);

                }

                resolve();
            }

        });
    }

    updateWithEntrypointURI(entrypointUri) {
        this.qs.setEntrypointUri(entrypointUri);
        return new Promise(resolve => {
            fetch(entrypointUri).then(res => {
                return res.json();
            }).then(data => {
                let commands = data.commands;
                let selectedCommands = [];
                let domains = {};

                // -- group by domain
                Object.keys(commands).forEach(name => {
                    let conf = commands[name];
                    let domainName = conf.meta.domain.name;
                    let domainId = conf.meta.domain.id;
                    let command = {
                        name: name,
                        ...conf,
                    };

                    if (conf.hasOwnProperty('examples')) {
                        command.examples = Object.keys(conf.examples).map(key => {
                            return {
                                name: key,
                                ...conf.examples[key],
                            };
                        });

                    } else {
                        command.examples = [];

                    }

                    selectedCommands.push(command);

                    if (!domains.hasOwnProperty(domainName)) {
                        domains[domainName] = domainId;
                    }
                });

                this.state = {
                    ...this.state,
                    entrypointUri: entrypointUri,
                    selectedCommands: selectedCommands,
                    allCommands: selectedCommands,
                    allDomains: domains,
                };

                resolve(self.state);
            });
        });
    }

    updateWithSelectedElement(selectedElement) {
        this.qs.setSelectedElement(selectedElement);
        this.state = {
            ...this.state,
            selectedElement: selectedElement,
        };

        return this.state;
    }

    updateWithSelectedAccessRole(selectedAccessRole) {
        this.qs.setSelectedAccessRole(selectedAccessRole);
        this.state = {
            ...this.state,
            selectedAccessRole: selectedAccessRole,
        };
        this.state.selectedCommands = this.refreshSelectedCommands();

        return this.state;
    }

    updateWithQuery(query) {
        this.qs.setQuery(query);
        this.state = {
            ...this.state,
            query: query,
        };
        this.state.selectedCommands = this.refreshSelectedCommands();

        return this.state;
    }

    refreshSelectedCommands() {
        let commands = this.state.allCommands;

        // -- selected access role
        if (this.state.selectedAccessRole) {
            commands = commands.filter(c => {
                return c.access.access_list.indexOf(
                    this.state.selectedAccessRole) >= 0;
            });

        }

        // -- query
        let getTextRepresentation = (command) => {
            return `
                ${command.name}
                ${command.meta.title}
                ${command.method}
                ${command.path_conf.path}
                ${command.meta.description}
            `.toLowerCase();
        }

        if (this.state.query) {
            commands = commands.filter(c => {
                return getTextRepresentation(c).indexOf(
                    this.state.query.toLowerCase()) >= 0;
            });

        }

        return commands;
    }
}
