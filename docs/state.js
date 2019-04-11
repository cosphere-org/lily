
/**
 * Managing the state of the app
 */
class State {

    constructor() {
        this.qs = new QueryParams();

        this.state = {
            entrypointUri: null,
            query: null,
            selectedDomain: null,
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

                    if (params.selectedDomain !== null) {
                        this.updateWithSelectedDomain(params.selectedDomain);

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
                if (params.selectedDomain !== null) {
                    this.updateWithSelectedDomain(params.selectedDomain);

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

                    selectedCommands.push({
                        name: name,
                        ...conf,
                    });

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

    updateWithSelectedDomain(selectedDomain) {
        this.qs.setSelectedDomain(selectedDomain);
        this.state = {
            ...this.state,
            selectedCommands: this.state.selectedCommands.filter(c => {
                return c.meta.domain.name == selectedDomain;
            }),
            selectedDomain: selectedDomain,
        };

        return this.state;
    }

    updateWithSelectedAccessRole(selectedAccessRole) {
        this.qs.setSelectedAccessRole(selectedAccessRole);
        this.state = {
            ...this.state,
            selectedAccessRole: selectedAccessRole,
            selectedCommands: this.state.selectedCommands.filter(c => {
                return c.access.access_list.indexOf(selectedAccessRole) >= 0;
            }),
        };

        return this.state;
    }

    updateWithQuery(query) {
        this.qs.setQuery(query);
        let getTextRepresentation = (command) => {
            return `
                ${command.name}
                ${command.meta.title}
                ${command.method}
                ${command.path_conf.path}
                ${command.meta.description}
            `;
        }

        this.state = {
            ...this.state,
            selectedCommands: this.state.selectedCommands.filter(c => {
                return getTextRepresentation(c).indexOf(query) >= 0;
            }),
            query: query,
        };

        return this.state;
    }

}
