
class DOMRenderer {

    constructor(state) {
        this.state = state;

        this.$inputEntrypointURI = $('#lily-entrypoint-uri');

        this.$inputEntrypointURIButton = $('#lily-entrypoint-uri-button');

        this.$inputQuery = $('#lily-query');

        this.$inputQueryButton = $('#lily-query-button');

        this.$domains = $('.domains');

        this.attachEvent();

        this.domainTemplate = $.templates(`
            <h2>{{:domainName}}</h2>
            <ul
                id="commands-per-domain-{{:id}}"
                class="collapsible">

            </ul>
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
                    <h3>{{:title}}</h3>
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
                            class="col s6">
                            INPUT
                            <pre>
                                <code class="JSON">{{:output}}</code>
                            </pre>
                        </div>

                        <div
                            class="col s6">
                            OUTPUT
                            <pre>
                                <code class="JSON">{{:output}}</code>
                            </pre>
                        </div>

                    </div>
<!--
  <ul class="examples collapsible">
    <li>
      <div class="collapsible-header"><i class="material-icons">filter_drama</i>First</div>
      <div class="collapsible-body"><span>Lorem ipsum dolor sit amet.</span></div>
    </li>
    <li>
      <div class="collapsible-header"><i class="material-icons">place</i>Second</div>
      <div class="collapsible-body"><span>Lorem ipsum dolor sit amet.</span></div>
    </li>
    <li>
      <div class="collapsible-header"><i class="material-icons">whatshot</i>Third</div>
      <div class="collapsible-body"><span>Lorem ipsum dolor sit amet.</span></div>
    </li>
  </ul>
-->
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

    /**
     * EVENTS
     */
    attachEvent () {

        this.$inputQueryButton.on('click', () => {
            this.state.updateWithQuery(
                this.$inputQuery.val());
            this.refresh();
        });

        this.$inputEntrypointURIButton.on('click', () => {
            this.state.updateWithEntrypointURI(
                this.$inputEntrypointURI.val()).then(() => {
                    this.refresh();

                });
        });

    }
    /**
     * Multiple Domains Rendering
     */
    renderDomains(commandsByDomain) {

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
            domainName: domainName,
        }))

        let $parent = $(`#${id}`);
        this.renderCommands($parent, commands);

    }

    /**
     * Multiple Commands Rendering
     */
    renderCommands($parent, commands) {
        commands.forEach(command => {
            this.renderCommand($parent, command);
        });

        $parent.collapsible();
        // !!!!!!!!!!!11
        // $parent.find('.examples').collapsible();
    }

    /**
     * Single Command Rendering
     */
    renderCommand($parent, command) {
        $parent.append(this.commandTemplate.render({
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
    }
}
