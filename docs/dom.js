
class DOMRenderer {

    constructor(state) {
        this.state = state;

        this.$inputEntrypointURI = $('#lily-entrypoint-uri');

        this.$inputEntrypointURIButton = $('#lily-entrypoint-uri-button');

        this.$inputQuery = $('#lily-query');

        this.$inputQueryButton = $('#lily-query-button');

        this.$domains = $('.domains');

        this.$domainHeaders = $('.domain-header');

        this.attachEvent();

        this.domainTemplate = $.templates(`
            <div>
                <h2
                    class="lily-domain jumpable"
                    id="{{:domainId}}">{{:domainName}}</h2>
                <ul
                    id="commands-per-domain-{{:id}}"
                    class="commands collapsible">

                </ul>
            </div>
        `);

        this.commandTemplate = $.templates(`
            <li>
                <div
                    class="collapsible-header grey lighten-4">
                    <span
                        class="lily-command-name">
                        {{:name}}
                    </span>

                    <span
                        class="lily-command-method">
                        {{:method}}
                    </span>

                    <span
                        class="lily-command-path">
                        {{:path}}
                    </span>
                </div>

                <div
                    class="collapsible-body">
                    <h3
                        id="{{:elementIdPrefix}}-title"
                        class="jumpable">{{:title}}</h3>
                    <span
                        class="lily-command-access">
                        {{for accessList}}
                            <div class="chip">
                                {{:}}
                            </div>
                        {{/for}}
                    </span>
                    <p class="flow-text">
                        {{:description}}
                    </p>
                    <div
                        class="row">

                        <div
                            class=" col s6">
                            <span
                                id="{{:elementIdPrefix}}-input-query"
                                class="jumpable">
                                INPUT QUERY</span>
                            {{if input_query}}

                            <pre>
                                <code class="JSON">{{:input_query}}</code>
                            </pre>

                            {{else}}

                            <pre>
                                <code class="JSON">NO INPUT QUERY</code>
                            </pre>
                            {{/if}}

                            <span
                                id="{{:elementIdPrefix}}-input-body"
                                class="jumpable">
                                INPUT BODY</span>
                            {{if input_body}}

                            <pre>
                                <code class="JSON">{{:input_body}}</code>
                            </pre>

                            {{else}}

                            <pre>
                                <code class="JSON">NO INPUT BODY</code>
                            </pre>
                            {{/if}}
                        </div>

                        <div
                            class="jumpable col s6">

                            <span
                                id="{{:elementIdPrefix}}-output-body"
                                class="jumpable">
                                OUTPUT BODY</span>

                            <pre>
                                <code class="JSON">{{:output}}</code>
                            </pre>
                        </div>

                    </div>

                    <ul class="examples collapsible">
                        {{for examples}}
                        <li>
                            <div
                                class="collapsible-header">
                                {{:name}}
                            </div>
                            <div
                                class="collapsible-body">

                                <h4>
                                    <span
                                        class="lily-command-method">
                                        {{:method}}
                                    </span>

                                    <span
                                        class="lily-command-path">
                                        {{:request.path}}
                                    </span>
                                </h4>

                                <div
                                    class="row">


                                    <div
                                        class="col s6">

                                        {{if request.headers}}
                                        <span
                                            id="{{:elementIdPrefix}}-request-headers"
                                            class="jumpable">
                                            REQUEST HEADERS</span>

                                        <pre>
                                            <code class="JSON">{{:request.headers}}</code>
                                        </pre>
                                        {{/if}}

                                        {{if request.content}}
                                        <span
                                            id="{{{:elementIdPrefix}}-request-body"
                                            class="jumpable">
                                            REQUEST BODY</span>

                                        <pre>
                                            <code class="JSON">{{:request.content}}</code>
                                        </pre>
                                        {{/if}}
                                    </div>

                                    <div
                                        class="col s6">

                                        {{if response.content}}
                                        <span
                                            id="{{:elementIdPrefix}}-response-body"
                                            class="jumpable">
                                            RESPONSE BODY</span>

                                        <pre>
                                            <code class="JSON">{{:response.content}}</code>
                                        </pre>
                                        {{/if}}
                                    </div>
                                </div>
                            </div>
                        </li>
                        {{/for}}
                    </ul>
                </div>
            </li>
        `);
    }

    groupByDomains(commands) {

        let commandsByDomain = {};
        commands.forEach(command => {
            let domainName = command.meta.domain.name;
            if (!commandsByDomain.hasOwnProperty(domainName)) {
                commandsByDomain[domainName] = [];
            }

            commandsByDomain[domainName].push(command);
        });

        return commandsByDomain;
    }

    getDomainId(domainName) {
        let suffix = domainName.replace(/\s+/mg, '-');

        return `domain-${suffix}`;
    }

    /**
     * EVENTS
     */
    attachEvent () {

        this.$inputQueryButton.on('click', () => {
            this.state.updateWithQuery(
                this.$inputQuery.val());
            this.refresh();
        });

        this.$inputQuery.on('keyup', e => {

            // -- ENTER press
            if (e.keyCode == 13) {
                this.state.updateWithQuery(
                    this.$inputQuery.val());
                this.refresh();
            }
        });

        this.$inputEntrypointURIButton.on('click', () => {
            this.state.updateWithEntrypointURI(
                this.$inputEntrypointURI.val()).then(() => {
                    this.refresh();

                });
        });

        this.$inputEntrypointURI.on('keyup', e => {

            // -- ENTER press
            if (e.keyCode == 13) {
                this.state.updateWithEntrypointURI(
                    this.$inputEntrypointURI.val());
                this.refresh();
            }
        });

        $('body').on('click', '.jumpable', e => {
            let $el = $(e.target);

            this.state.updateWithSelectedElement($el.attr('id'));

            $el[0].scrollIntoView({
                behavior: "smooth",
                block: "start",
                inline: "nearest",
            });
        });
    }
    /**
     * Multiple Domains Rendering
     */
    renderDomains(commandsByDomain) {

        // -- reset
        this.$domains.empty();

        Object.keys(commandsByDomain).sort().forEach((domainName, idx) => {

            let commands = commandsByDomain[domainName];
            this.renderDomain(idx, domainName, commands);
        });

        document.querySelectorAll('pre code').forEach(block => {
            hljs.highlightBlock(block);
        });
    }

    /**
     * Single Domain Rendering
     */
    renderDomain(idx, domainName, commands) {
        let id = `commands-per-domain-${idx}`;

        this.$domains.append(this.domainTemplate.render({
            id: idx,
            domainId: this.getDomainId(domainName),
            domainName: domainName,
        }))

        let $parent = $(`#${id}`);
        this.renderCommands($parent, domainName, commands);

    }

    /**
     * Multiple Commands Rendering
     */
    renderCommands($parent, domainName, commands) {
        commands.forEach((command, idx) => {
            this.renderCommand($parent, domainName, idx, command);
        });

        $parent.collapsible();
        $parent.find('.examples').collapsible();
    }

    /**
     * Single Command Rendering
     */
    renderCommand($parent, domainName, idx, command) {

        $parent.append(this.commandTemplate.render({
            elementIdPrefix: `${this.getDomainId(domainName)}__${idx}__`,
            name: command.name,
            method: command.method,
            path: command.path_conf.path,
            title: command.meta.title,
            description: (
                command.meta.description ?
                command.meta.description :
                ''),
            accessList: (
                command.access.access_list ?
                command.access.access_list :
                ['ANY']),
            output: JSON.stringify(command.schemas.output.schema, null, 2),
            input_query: (
                command.schemas.input_query ?
                JSON.stringify(command.schemas.input_query.schema, null, 2) :
                null),
            input_body: (
                command.schemas.input_body ?
                JSON.stringify(command.schemas.input_body.schema, null, 2) :
                null),
            examples: command.examples.map((e, i) => {
                e.elementIdPrefix = (
                    `${this.getDomainId(domainName)}__${idx}__${i}__`);

                if (e.request.headers) {
                    e.request.headers = Object.keys(e.request.headers).map(h => {
                        let v = e.request.headers[h];

                        return `${h}: ${v}`;
                    }).join('\n');

                } else {
                    e.request.headers = undefined;

                }

                if (e.request.content) {
                    e.request.content = JSON.stringify(
                        e.request.content, null, 2);

                } else {
                    e.request.content = undefined;
                }

                if (e.response.content) {
                    e.response.content = JSON.stringify(
                        e.response.content, null, 2);

                } else {
                    e.response.content = undefined;
                }

                return e;
            }),
        }));
    }

    refresh() {
        let state = this.state.state;

        if (state.query) {
            this.$inputQuery.val(state.query);
        }

        if (state.entrypointUri) {
            this.$inputEntrypointURI.val(state.entrypointUri);
        }

        if (state.selectedCommands) {
            let commandsByDomain = this.groupByDomains(state.selectedCommands);

            this.renderDomains(commandsByDomain);

        }

        if (state.selectedElement) {
            let parts = state.selectedElement.split('__');
            let $el = $(`#${parts[0]}`);

            // -- open all collapsible
            if ($el.length && parts.length >= 2) {
                let $commands = $el.parent().find('.commands');

                if ($commands.length > 0) {
                    let instance = M.Collapsible.getInstance($commands[0]);
                    instance.open(+parts[1]);
                }

                if (parts.length >= 3) {
                    let $examples = $commands.find('.examples');

                    if ($examples.length > 0) {
                        let instance = M.Collapsible.getInstance($examples[0]);
                        instance.open(+parts[2]);

                    }

                }
            }

            let $target = $(`#${state.selectedElement}`);
            if ($target.length > 0) {
                setTimeout(() => {
                    $target[0].scrollIntoView({
                        behavior: "smooth",
                        block: "start",
                        inline: "nearest",
                    });

                }, 100);

            }
        }
    }
}
